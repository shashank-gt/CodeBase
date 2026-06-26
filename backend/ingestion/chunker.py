"""
Intelligent code chunker for CBQA V8 — Production Release.
AST-based chunking for Python, regex-based for JS/TS/Go/Rust/Java,
with import context injection, docstring extraction, and semantic
boundary detection. Produces chunks that preserve logical code units
rather than arbitrary text splits.
"""
import ast, re, logging
from typing import List, Dict
from config.settings import settings

logger = logging.getLogger(__name__)


def _mk(text: str, file: str, ctype: str, name: str, start: int, end: int, lang: str, doc: str = "") -> Dict:
    """Create a standardized chunk with rich metadata."""
    return {
        "text": text,
        "metadata": {
            "file": file,
            "type": ctype,
            "name": name,
            "start_line": start,
            "end_line": end,
            "language": lang,
            "docstring": doc[:250] if doc else "",
        },
    }


def _doc(node) -> str:
    """Extract docstring from an AST node."""
    try:
        d = ast.get_docstring(node)
        return d.strip()[:250] if d else ""
    except Exception:
        return ""


def _imports(tree, content: str) -> str:
    """Extract import statements to provide context in chunks."""
    parts = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            seg = ast.get_source_segment(content, node)
            if seg:
                parts.append(seg)
    return "\n".join(parts[:10])


def _extract_decorators(node, lines: list) -> str:
    """Extract decorator lines for a function/class node."""
    decorators = []
    for dec in getattr(node, "decorator_list", []):
        dec_line = lines[dec.lineno - 1].strip() if dec.lineno <= len(lines) else ""
        if dec_line:
            decorators.append(dec_line)
    return "\n".join(decorators)


# ── Python AST Chunker ───────────────────────────────────────────────────────

def chunk_python(fi: Dict) -> List[Dict]:
    """AST-based Python chunking with full context preservation."""
    content = fi["content"]
    rel = fi["relative_path"]
    lines = content.splitlines()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return _tsplit(content, rel, "python")

    imp = _imports(tree, content)
    module_doc = _doc(tree)
    chunks = []
    seen = set()

    # Module-level docstring chunk (provides file context)
    if module_doc and len(module_doc) >= settings.MIN_CHUNK_CHARS:
        chunks.append(_mk(
            f"# Module: {rel}\n# {module_doc}\n\n{imp}" if imp else f"# Module: {rel}\n# {module_doc}",
            rel, "module_doc", Path_basename(rel), 1, 1, "python", module_doc,
        ))

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            s = node.lineno - 1
            e = getattr(node, "end_lineno", node.lineno + 100)
            class_text = "\n".join(lines[s:e])
            class_doc = _doc(node)

            # Full class chunk (if not too large)
            if len(class_text) >= settings.MIN_CHUNK_CHARS and len(class_text) < 4000:
                k = (node.name, node.lineno)
                if k not in seen:
                    seen.add(k)
                    chunks.append(_mk(class_text, rel, "class", node.name, node.lineno, e, "python", class_doc))

            # Individual methods within the class
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    ms = child.lineno - 1
                    me = getattr(child, "end_lineno", child.lineno + 40)
                    method_lines = lines[ms:me]
                    method_doc = _doc(child)

                    # Add class context header
                    decorators = _extract_decorators(child, lines)
                    ctx = f"# Class: {node.name}"
                    if class_doc:
                        ctx += f"\n# {class_doc[:100]}"
                    mt = f"{ctx}\n{decorators}\n{chr(10).join(method_lines)}" if decorators else f"{ctx}\n{chr(10).join(method_lines)}"

                    if len(mt) >= settings.MIN_CHUNK_CHARS:
                        k = (f"{node.name}.{child.name}", child.lineno)
                        if k not in seen:
                            seen.add(k)
                            chunks.append(_mk(mt, rel, "method", f"{node.name}.{child.name}", child.lineno, me, "python", method_doc))

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            s = node.lineno - 1
            e = getattr(node, "end_lineno", node.lineno + 40)
            func_lines = lines[s:e]
            func_doc = _doc(node)
            decorators = _extract_decorators(node, lines)

            # Prepend imports for standalone functions (cross-file context)
            prefix = f"# File: {rel}\n"
            if imp:
                prefix += f"# Imports:\n{imp}\n\n"
            if decorators:
                prefix += f"{decorators}\n"

            text = prefix + "\n".join(func_lines)

            if len(text) >= settings.MIN_CHUNK_CHARS:
                k = (node.name, node.lineno)
                if k not in seen:
                    seen.add(k)
                    chunks.append(_mk(text, rel, "function", node.name, node.lineno, e, "python", func_doc))

        # Module-level assignments (constants, config)
        elif isinstance(node, ast.Assign):
            s = node.lineno - 1
            e = getattr(node, "end_lineno", node.lineno)
            text = "\n".join(lines[s:e])
            if len(text) >= settings.MIN_CHUNK_CHARS:
                # Get the target name
                try:
                    name = ast.dump(node.targets[0])
                    if hasattr(node.targets[0], "id"):
                        name = node.targets[0].id
                except Exception:
                    name = "constant"
                k = (name, node.lineno)
                if k not in seen:
                    seen.add(k)
                    chunks.append(_mk(f"# File: {rel}\n{text}", rel, "constant", str(name), node.lineno, e, "python"))

    return chunks if chunks else _tsplit(content, rel, "python")


# ── Regex-based chunker for JS/TS/Go/Rust/Java etc ──────────────────────────

_PATS = [
    re.compile(r'^(?:export\s+)?(?:async\s+)?function\s+\w+\s*\(', re.MULTILINE),
    re.compile(r'^(?:export\s+)?(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\(', re.MULTILINE),
    re.compile(r'^(?:export\s+)?(?:abstract\s+)?class\s+\w+', re.MULTILINE),
    re.compile(r'^(?:export\s+)?(?:interface|type|enum)\s+\w+', re.MULTILINE),
    re.compile(r'^(?:public|private|protected|static|func)\s+\S+\s+\w+\s*\(', re.MULTILINE),
    re.compile(r'^(?:pub\s+)?(?:fn|struct|enum|impl|trait)\s+\w+', re.MULTILINE),  # Rust
    re.compile(r'^func\s+(?:\([^)]+\)\s+)?\w+\s*\(', re.MULTILINE),  # Go
]


def chunk_regex(fi: Dict) -> List[Dict]:
    """Regex-based chunking for non-Python code files."""
    content = fi["content"]
    rel = fi["relative_path"]
    ext = fi["extension"].lstrip(".")

    # Find all boundary points
    boundaries = sorted({0, len(content)} | {m.start() for p in _PATS for m in p.finditer(content)})
    seen = set()
    chunks = []

    for i in range(len(boundaries) - 1):
        text = content[boundaries[i]:boundaries[i + 1]].strip()
        if len(text) < settings.MIN_CHUNK_CHARS:
            continue

        h = hash(text[:300])
        if h in seen:
            continue
        seen.add(h)

        # If chunk is too large, split it
        if len(text.split()) > settings.CHUNK_SIZE * 2:
            chunks.extend(_tsplit(text, rel, ext))
            continue

        sl = content[: boundaries[i]].count("\n") + 1
        el = sl + text.count("\n")

        # Extract name from first line
        first_line = text.split("\n")[0]
        name_match = re.search(r'\b(\w+)\s*[({]', first_line)
        name = name_match.group(1) if name_match else "block"

        # Detect type
        ctype = "block"
        if re.match(r'(?:export\s+)?(?:async\s+)?function\s+', first_line):
            ctype = "function"
        elif re.match(r'(?:export\s+)?class\s+', first_line):
            ctype = "class"
        elif re.match(r'(?:export\s+)?interface\s+', first_line):
            ctype = "interface"
        elif re.match(r'(?:pub\s+)?fn\s+', first_line):
            ctype = "function"
        elif re.match(r'func\s+', first_line):
            ctype = "function"

        # Extract leading comment as docstring
        doc = ""
        doc_match = re.match(r'^\s*(?:///?\s*(.+)|/\*\*?\s*\n?\s*\*?\s*(.+?))\n', text)
        if doc_match:
            doc = (doc_match.group(1) or doc_match.group(2) or "").strip()[:200]

        chunks.append(_mk(f"// File: {rel}\n{text}", rel, ctype, name, sl, el, ext, doc))

    return chunks if chunks else _tsplit(content, rel, ext)


# ── Text splitting fallback ──────────────────────────────────────────────────

def _tsplit(text: str, rel: str, lang: str) -> List[Dict]:
    """Line-aware text splitting with overlap — used as fallback."""
    lines_list = text.splitlines()
    target_lines = max(20, settings.CHUNK_SIZE // 5)
    overlap_lines = max(3, settings.CHUNK_OVERLAP // 5)

    chunks = []
    i = 0
    idx = 0

    while i < len(lines_list):
        chunk_lines = lines_list[i: i + target_lines]
        t = "\n".join(chunk_lines)

        if len(t) >= settings.MIN_CHUNK_CHARS:
            chunks.append(_mk(
                f"# File: {rel}\n{t}",
                rel, "chunk", f"chunk_{idx}", i + 1, i + len(chunk_lines), lang,
            ))

        i += target_lines - overlap_lines
        idx += 1

    return chunks


# ── Configuration / markup file chunking ─────────────────────────────────────

def chunk_config(fi: Dict) -> List[Dict]:
    """Chunk config/markup files as single units when small, otherwise split."""
    content = fi["content"]
    rel = fi["relative_path"]
    ext = fi["extension"].lstrip(".")

    if len(content) < 3000:
        return [_mk(f"# Config file: {rel}\n{content}", rel, "config", Path_basename(rel), 1, content.count("\n") + 1, ext)]
    return _tsplit(content, rel, ext)


# ── File routing ─────────────────────────────────────────────────────────────

def chunk_file(fi: Dict) -> List[Dict]:
    """Route each file to the appropriate chunking strategy."""
    ext = fi["extension"]
    if ext == ".py":
        return chunk_python(fi)
    if ext in {".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".cs", ".cpp", ".c", ".h", ".rb", ".swift", ".kt", ".php", ".scala"}:
        return chunk_regex(fi)
    if ext in {".json", ".yaml", ".yml", ".toml", ".xml", ".html", ".css", ".scss"}:
        return chunk_config(fi)
    return _tsplit(fi["content"], fi["relative_path"], ext.lstrip("."))


def chunk_codebase(files: List[Dict]) -> List[Dict]:
    """Chunk all files and return a flat list of chunks."""
    all_chunks = []
    for fi in files:
        try:
            file_chunks = chunk_file(fi)
            all_chunks.extend(file_chunks)
        except Exception as e:
            logger.warning(f"Chunking failed for {fi['relative_path']}: {e}")
            # Fallback to text split
            all_chunks.extend(_tsplit(fi["content"], fi["relative_path"], fi["extension"].lstrip(".")))

    logger.info(f"Chunked {len(files)} files → {len(all_chunks)} chunks")
    return all_chunks


# ── Helpers ───────────────────────────────────────────────────────────────────

def Path_basename(path: str) -> str:
    """Get the basename of a path string."""
    parts = path.replace("\\", "/").split("/")
    return parts[-1] if parts else path
