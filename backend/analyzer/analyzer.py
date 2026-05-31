import re, os, json, logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

DEPLOY_PATTERNS = [
    (r'https?://[a-zA-Z0-9\-]+\.vercel\.app','Vercel'),
    (r'https?://[a-zA-Z0-9\-]+\.netlify\.app','Netlify'),
    (r'https?://[a-zA-Z0-9\-]+\.onrender\.com','Render'),
    (r'https?://[a-zA-Z0-9\-]+\.fly\.dev','Fly.io'),
    (r'https?://[a-zA-Z0-9\-]+\.railway\.app','Railway'),
    (r'https?://[a-zA-Z0-9\-]+\.herokuapp\.com','Heroku'),
]
TECH_KW = {
    "Python":[".py","requirements.txt"],"JavaScript":[".js","package.json"],
    "TypeScript":[".ts",".tsx","tsconfig.json"],"React":["react","jsx",".tsx"],
    "FastAPI":["fastapi","uvicorn"],"Django":["django","manage.py"],
    "Flask":["flask"],"Node.js":["package.json",".js"],"Docker":["Dockerfile"],
    "PostgreSQL":["psycopg2","postgres"],"MongoDB":["pymongo","mongoose"],
    "Redis":["redis"],"ChromaDB":["chromadb"],"OpenAI":["openai"],"Gemini":["generativeai","gemini"],
    "LangChain":["langchain"],"Tailwind":["tailwind"],"Next.js":["next.config"],
    "Vue":[".vue"],"Rust":[".rs","cargo"],"Go":[".go","go.mod"],
}
API_PATS = [
    r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
    r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
    r'router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
    r'app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
]

def analyze_repo(root_dir: str, files: List[Dict]) -> Dict[str, Any]:
    root = Path(root_dir)
    all_paths = " ".join(f["relative_path"] for f in files)
    readme = next((f for f in files if Path(f["relative_path"]).name.lower() in ("readme.md","readme.txt")), None)
    return {
        "name": root.name,
        "description": _desc(readme["content"]) if readme else "",
        "readme_summary": _readme_summary(readme["content"]) if readme else "",
        "tech_stack": _tech(files, all_paths),
        "deployment_links": _deploys(readme["content"]) if readme else [],
        "api_routes": _routes(files),
        "setup_steps": _setup(readme["content"]) if readme else [],
        "language_breakdown": _langs(files),
        "dependencies": _deps(files),
        "key_files": _key_files(files),
        "file_count": len(files),
        "repo_tree": _build_tree(files),
    }

def _build_tree(files):
    tree = {"name":"root","type":"folder","path":"","children":{}}
    for f in files:
        parts = Path(f["relative_path"]).parts
        node = tree; cp = ""
        for i, part in enumerate(parts):
            cp = str(Path(cp)/part) if cp else part
            if i == len(parts)-1:
                node["children"][part] = {"name":part,"type":"file","path":f["relative_path"],"extension":f["extension"],"size":len(f["content"]),"role":_role(f)}
            else:
                if part not in node["children"]:
                    node["children"][part] = {"name":part,"type":"folder","path":cp,"children":{}}
                node = node["children"][part]
    return _ser(tree)

def _ser(n):
    if n["type"] == "folder":
        ch = [_ser(v) for v in n["children"].values()]
        ch.sort(key=lambda x:(0 if x["type"]=="folder" else 1, x["name"]))
        return {**{k:v for k,v in n.items() if k!="children"},"children":ch}
    return n

def _desc(content):
    for l in content.splitlines():
        l = l.strip()
        if l and not l.startswith(("#","!","[","<","-","*","```")) and len(l)>15:
            return l[:300]
    return ""

def _readme_summary(c):
    lines = [l.strip() for l in c.splitlines() if l.strip()][:40]
    out = []
    for l in lines:
        if l.startswith("#") or (len(l)>20 and not l.startswith(("```","!","<"))):
            out.append(l)
        if len(out)>=10: break
    return "\n".join(out)

def _deploys(c):
    seen, out = set(), []
    for pat, plat in DEPLOY_PATTERNS:
        for m in re.finditer(pat, c):
            u = m.group(0)
            if u not in seen: seen.add(u); out.append({"url":u,"platform":plat})
    return out

def _setup(c):
    steps, in_block, block = [], False, []
    for l in c.splitlines():
        if l.strip().startswith("```"):
            if in_block and block: steps.append(" ".join(block[:2]))
            block, in_block = [], not in_block
        elif in_block:
            s = l.strip()
            if s and not s.startswith("#"): block.append(s)
    for l in c.splitlines():
        s = l.strip()
        if s.startswith(("pip install","npm install","yarn add","python ","uvicorn","node ")):
            if s not in steps: steps.append(s)
    return steps[:8]

def _tech(files, all_paths):
    found, file_names = set(), {Path(f["relative_path"]).name.lower() for f in files}
    exts = {f["extension"] for f in files}
    content_sample = " ".join(f.get("content","")[:300] for f in files[:20]).lower()
    for tech, sigs in TECH_KW.items():
        for sig in sigs:
            if sig.startswith("."):
                if sig in exts: found.add(tech)
            elif sig.lower() in all_paths.lower() or sig.lower() in content_sample or any(sig.lower() in fn for fn in file_names):
                found.add(tech)
    return sorted(found)

def _langs(files):
    m = {".py":"Python",".js":"JavaScript",".ts":"TypeScript",".tsx":"TypeScript",".jsx":"JavaScript",
         ".java":"Java",".go":"Go",".rs":"Rust",".cpp":"C++",".c":"C",".cs":"C#",".rb":"Ruby",
         ".php":"PHP",".html":"HTML",".css":"CSS",".md":"Markdown",".json":"JSON",".yaml":"YAML",".yml":"YAML"}
    c: Dict[str,int] = {}
    for f in files: lang = m.get(f["extension"],"Other"); c[lang] = c.get(lang,0)+1
    return dict(sorted(c.items(), key=lambda x:-x[1]))

def _routes(files):
    routes, seen = [], set()
    for f in files:
        if f["extension"] not in (".py",".js",".ts"): continue
        for pat in API_PATS:
            for m in re.finditer(pat, f["content"]):
                g = m.groups()
                method, path = (g[0].upper(), g[1]) if len(g)==2 else ("GET", g[0])
                k = f"{method}:{path}"
                if k not in seen: seen.add(k); routes.append({"method":method,"path":path,"file":f["relative_path"]})
    return routes[:20]

def _deps(files):
    deps = []
    for f in files:
        name = Path(f["relative_path"]).name
        if name == "requirements.txt":
            for l in f["content"].splitlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    pkg = re.split(r"[>=<!]",l)[0].strip()
                    if pkg: deps.append(pkg)
        elif name == "package.json":
            try:
                d = json.loads(f["content"])
                for k in ("dependencies","devDependencies"): deps.extend(d.get(k,{}).keys())
            except Exception: pass
    return deps[:30]

def _key_files(files):
    KEY = {"main.py","app.py","server.py","index.py","index.js","app.js","server.js",
           "index.ts","app.ts","routes.py","models.py","database.py","settings.py",
           "Dockerfile","README.md","requirements.txt","package.json",".env.example"}
    return [{"file":f["relative_path"],"reason":f"Core: {Path(f['relative_path']).name}"}
            for f in files if Path(f["relative_path"]).name in KEY][:10]

def _role(f):
    p = f["relative_path"].lower(); name = Path(p).name; ext = f["extension"]
    if name in ("main.py","app.py","server.py","index.js","index.ts"): return "entry"
    if "route" in p or "endpoint" in p or "api" in p: return "api"
    if "model" in p or "schema" in p: return "model"
    if "test" in p or "spec" in p: return "test"
    if name.startswith("readme"): return "doc"
    if name in ("requirements.txt","package.json","dockerfile",".env.example"): return "config"
    if "util" in p or "helper" in p or "lib" in p: return "util"
    if "rag" in p or "retriev" in p or "embed" in p: return "rag"
    if "chunk" in p or "ingest" in p or "loader" in p: return "ingestion"
    return "source"
