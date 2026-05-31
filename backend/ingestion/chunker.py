import ast, re, logging
from typing import List, Dict
from config.settings import settings

logger = logging.getLogger(__name__)

def _mk(text, file, ctype, name, start, end, lang, doc=""):
    return {"text": text, "metadata": {"file": file, "type": ctype, "name": name,
                                        "start_line": start, "end_line": end,
                                        "language": lang, "docstring": doc}}

def _doc(node):
    try:
        d = ast.get_docstring(node)
        return d.strip()[:200] if d else ""
    except Exception:
        return ""

def _imports(tree, content):
    parts = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            seg = ast.get_source_segment(content, node)
            if seg:
                parts.append(seg)
    return "\n".join(parts[:8])

def chunk_python(fi):
    content, rel = fi["content"], fi["relative_path"]
    lines = content.splitlines()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return _tsplit(content, rel, "python")
    imp = _imports(tree, content)
    chunks, seen = [], set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            s, e = node.lineno-1, getattr(node,"end_lineno",node.lineno+100)
            text = "\n".join(lines[s:e])
            if len(text) >= settings.MIN_CHUNK_CHARS:
                chunks.append(_mk(text, rel, "class", node.name, node.lineno, e, "python", _doc(node)))
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    ms, me = child.lineno-1, getattr(child,"end_lineno",child.lineno+40)
                    mt = f"# Class: {node.name}\n" + "\n".join(lines[ms:me])
                    if len(mt) >= settings.MIN_CHUNK_CHARS:
                        chunks.append(_mk(mt, rel, "method", f"{node.name}.{child.name}", child.lineno, me, "python", _doc(child)))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            s, e = node.lineno-1, getattr(node,"end_lineno",node.lineno+40)
            text = (f"# Imports:\n{imp}\n\n" if imp else "") + "\n".join(lines[s:e])
            if len(text) >= settings.MIN_CHUNK_CHARS:
                chunks.append(_mk(text, rel, "function", node.name, node.lineno, e, "python", _doc(node)))
    deduped = []
    for c in chunks:
        k = (c["metadata"]["name"], c["metadata"]["start_line"])
        if k not in seen:
            seen.add(k); deduped.append(c)
    return deduped if deduped else _tsplit(content, rel, "python")

_PATS = [
    re.compile(r'^(?:export\s+)?(?:async\s+)?function\s+\w+\s*\(', re.MULTILINE),
    re.compile(r'^(?:export\s+)?(?:abstract\s+)?class\s+\w+', re.MULTILINE),
    re.compile(r'^(?:public|private|protected|static|func)\s+\S+\s+\w+\s*\(', re.MULTILINE),
]

def chunk_regex(fi):
    content, rel, ext = fi["content"], fi["relative_path"], fi["extension"].lstrip(".")
    pts = sorted({0, len(content)} | {m.start() for p in _PATS for m in p.finditer(content)})
    seen, chunks = set(), []
    for i in range(len(pts)-1):
        text = content[pts[i]:pts[i+1]].strip()
        if len(text) < settings.MIN_CHUNK_CHARS:
            continue
        h = hash(text[:200])
        if h in seen:
            continue
        seen.add(h)
        if len(text.split()) > settings.CHUNK_SIZE * 2:
            chunks.extend(_tsplit(text, rel, ext)); continue
        sl = content[:pts[i]].count("\n") + 1
        name = (re.search(r'\b(\w+)\s*[({]', text.split("\n")[0]) or type("",(),({"group":lambda s,n:"block"}))()).group(1) if re.search(r'\b(\w+)\s*[({]', text.split("\n")[0]) else "block"
        chunks.append(_mk(text, rel, "block", name, sl, sl, ext))
    return chunks if chunks else _tsplit(content, rel, ext)

def _tsplit(text, rel, lang):
    words = text.split()
    size, overlap, chunks, i, idx = settings.CHUNK_SIZE, settings.CHUNK_OVERLAP, [], 0, 0
    while i < len(words):
        t = " ".join(words[i:i+size])
        if len(t) >= settings.MIN_CHUNK_CHARS:
            sl = text[:len(" ".join(words[:i]))].count("\n") + 1
            chunks.append(_mk(t, rel, "chunk", f"chunk_{idx}", sl, sl, lang))
        i += size - overlap; idx += 1
    return chunks

def chunk_file(fi):
    ext = fi["extension"]
    if ext == ".py": return chunk_python(fi)
    if ext in {".js",".ts",".tsx",".jsx",".java",".go",".rs",".cs",".cpp",".c",".h",".rb",".swift",".kt",".php"}: return chunk_regex(fi)
    return _tsplit(fi["content"], fi["relative_path"], ext.lstrip("."))

def chunk_codebase(files):
    all_chunks = []
    for fi in files:
        all_chunks.extend(chunk_file(fi))
    logger.info(f"Chunked {len(files)} files → {len(all_chunks)} chunks")
    return all_chunks
