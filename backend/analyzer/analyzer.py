"""
Repository intelligence analyzer for CBQA V8 — Production Release.
Deep static analysis: architecture, frameworks, tech stack, entry points,
APIs, services, databases, dependencies, configuration, build process,
deployment, authentication, routing, middleware, utilities, execution pipeline,
import graph, class hierarchies, and design patterns.
"""
import re, os, json, logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

logger = logging.getLogger(__name__)

# ── Detection patterns ────────────────────────────────────────────────────────

DEPLOY_PATTERNS = [
    (r'https?://[a-zA-Z0-9\-]+\.vercel\.app', 'Vercel'),
    (r'https?://[a-zA-Z0-9\-]+\.netlify\.app', 'Netlify'),
    (r'https?://[a-zA-Z0-9\-]+\.onrender\.com', 'Render'),
    (r'https?://[a-zA-Z0-9\-]+\.fly\.dev', 'Fly.io'),
    (r'https?://[a-zA-Z0-9\-]+\.railway\.app', 'Railway'),
    (r'https?://[a-zA-Z0-9\-]+\.herokuapp\.com', 'Heroku'),
    (r'https?://[a-zA-Z0-9\-]+\.azurewebsites\.net', 'Azure'),
    (r'https?://[a-zA-Z0-9\-]+\.appspot\.com', 'GCP'),
]

TECH_KW = {
    "Python": [".py", "requirements.txt", "pyproject.toml", "setup.py"],
    "JavaScript": [".js", "package.json"],
    "TypeScript": [".ts", ".tsx", "tsconfig.json"],
    "React": ["react", "jsx", ".tsx", "react-dom"],
    "FastAPI": ["fastapi", "uvicorn"],
    "Django": ["django", "manage.py", "wsgi.py"],
    "Flask": ["flask"],
    "Express": ["express"],
    "Node.js": ["package.json", ".js"],
    "Docker": ["Dockerfile", "docker-compose"],
    "PostgreSQL": ["psycopg2", "postgres", "pg_"],
    "MongoDB": ["pymongo", "mongoose", "mongodb"],
    "MySQL": ["mysql", "mysqlclient"],
    "SQLite": ["sqlite3", "sqlite"],
    "Redis": ["redis"],
    "ChromaDB": ["chromadb"],
    "Pinecone": ["pinecone"],
    "Weaviate": ["weaviate"],
    "OpenAI": ["openai"],
    "Gemini": ["generativeai", "gemini"],
    "LangChain": ["langchain"],
    "LlamaIndex": ["llama_index", "llamaindex"],
    "Tailwind": ["tailwind"],
    "Next.js": ["next.config"],
    "Vue": [".vue", "vue"],
    "Angular": ["angular", "@angular"],
    "Svelte": [".svelte"],
    "Rust": [".rs", "cargo"],
    "Go": [".go", "go.mod"],
    "Java": [".java", "pom.xml", "build.gradle"],
    "Groq": ["groq"],
    "Ollama": ["ollama"],
    "Sentence-Transformers": ["sentence_transformers", "sentence-transformers"],
    "Pydantic": ["pydantic"],
    "SQLAlchemy": ["sqlalchemy"],
    "Celery": ["celery"],
    "RabbitMQ": ["rabbitmq", "pika"],
    "Kafka": ["kafka"],
    "GraphQL": ["graphql", "graphene"],
    "gRPC": ["grpc", "protobuf"],
    "Terraform": ["terraform"],
    "Kubernetes": ["kubernetes", "k8s"],
    "JWT": ["jwt", "jsonwebtoken", "pyjwt"],
    "OAuth": ["oauth", "oauth2"],
    "Stripe": ["stripe"],
    "AWS": ["boto3", "aws-sdk"],
    "Firebase": ["firebase"],
    "Supabase": ["supabase"],
    "Prisma": ["prisma"],
    "Drizzle": ["drizzle"],
    "Pytest": ["pytest"],
    "Jest": ["jest"],
    "Vitest": ["vitest"],
}

API_PATS = [
    r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
    r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
    r'router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
    r'app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
]

SERVICE_PATTERNS = [
    (r'mongodb(?:\+srv)?://', 'MongoDB'),
    (r'postgres(?:ql)?://', 'PostgreSQL'),
    (r'mysql://', 'MySQL'),
    (r'redis://', 'Redis'),
    (r'amqp://', 'RabbitMQ'),
    (r'sqlite:///', 'SQLite'),
    (r'https?://api\.groq\.com', 'Groq API'),
    (r'https?://api\.openai\.com', 'OpenAI API'),
    (r'https?://generativelanguage\.googleapis\.com', 'Gemini API'),
    (r'smtp://', 'SMTP Email'),
    (r'S3Client|boto3', 'AWS S3'),
    (r'chromadb|chroma', 'ChromaDB'),
    (r'pinecone', 'Pinecone'),
    (r'weaviate', 'Weaviate'),
    (r'elasticsearch', 'Elasticsearch'),
    (r'https?://api\.\w+\.\w+', 'External API'),
]


# ── Main entry point ─────────────────────────────────────────────────────────

def analyze_repo(root_dir: str, files: List[Dict]) -> Dict[str, Any]:
    """Perform deep repository intelligence analysis."""
    root = Path(root_dir)
    all_paths = " ".join(f["relative_path"] for f in files)
    readme = next(
        (f for f in files if Path(f["relative_path"]).name.lower() in ("readme.md", "readme.txt", "readme.rst")),
        None,
    )
    readme_content = readme["content"] if readme else ""

    import_graph = _build_import_graph(files)
    class_hierarchy = _class_hierarchy(files)
    middleware = _middleware(files)
    config_files = _config_files(files)
    auth_patterns = _auth_patterns(files)
    build_info = _build_info(files)

    return {
        "name": root.name,
        "description": _desc(readme_content) if readme_content else _infer_description(files, root.name),
        "readme_summary": _readme_summary(readme_content) if readme_content else "",
        "tech_stack": _tech(files, all_paths),
        "deployment_links": _deploys(readme_content) if readme_content else [],
        "api_routes": _routes(files),
        "setup_steps": _setup(readme_content) if readme_content else [],
        "language_breakdown": _langs(files),
        "dependencies": _deps(files),
        "key_files": _key_files(files, import_graph),
        "file_count": len(files),
        "repo_tree": _build_tree(files),
        "entry_points": _entry_points(files),
        "service_connections": _service_connections(files),
        "design_patterns": _design_patterns(files),
        "import_graph": import_graph,
        "class_hierarchy": class_hierarchy,
        "middleware": middleware,
        "config_files": config_files,
        "auth_patterns": auth_patterns,
        "build_info": build_info,
        "directory_purposes": _directory_purposes(files),
    }


# ── Tree building ─────────────────────────────────────────────────────────────

def _build_tree(files):
    tree = {"name": "root", "type": "folder", "path": "", "children": {}}
    for f in files:
        parts = Path(f["relative_path"]).parts
        node = tree
        cp = ""
        for i, part in enumerate(parts):
            cp = (Path(cp) / part).as_posix() if cp else part
            if i == len(parts) - 1:
                node["children"][part] = {
                    "name": part,
                    "type": "file",
                    "path": f["relative_path"],
                    "extension": f["extension"],
                    "size": len(f["content"]),
                    "role": _role(f),
                }
            else:
                if part not in node["children"]:
                    node["children"][part] = {"name": part, "type": "folder", "path": cp, "children": {}}
                node = node["children"][part]
    return _ser(tree)


def _ser(n):
    if n["type"] == "folder":
        ch = [_ser(v) for v in n["children"].values()]
        ch.sort(key=lambda x: (0 if x["type"] == "folder" else 1, x["name"]))
        return {**{k: v for k, v in n.items() if k != "children"}, "children": ch}
    return n


# ── README / Description ─────────────────────────────────────────────────────

def _desc(content):
    for l in content.splitlines():
        l = l.strip()
        if l and not l.startswith(("#", "!", "[", "<", "-", "*", "```")) and len(l) > 15:
            return l[:300]
    return ""


def _infer_description(files: List[Dict], repo_name: str) -> str:
    """Infer project description when no README exists."""
    tech = _tech(files, " ".join(f["relative_path"] for f in files))
    if tech:
        return f"{repo_name} — a project using {', '.join(tech[:5])}"
    return f"{repo_name} — {len(files)} source files"


def _readme_summary(c):
    lines = [l.strip() for l in c.splitlines() if l.strip()][:50]
    out = []
    for l in lines:
        if l.startswith("#") or (len(l) > 20 and not l.startswith(("```", "!", "<"))):
            out.append(l)
        if len(out) >= 12:
            break
    return "\n".join(out)


# ── Deployment ────────────────────────────────────────────────────────────────

def _deploys(c):
    seen, out = set(), []
    for pat, plat in DEPLOY_PATTERNS:
        for m in re.finditer(pat, c):
            u = m.group(0)
            if u not in seen:
                seen.add(u)
                out.append({"url": u, "platform": plat})
    return out


# ── Setup steps ───────────────────────────────────────────────────────────────

def _setup(c):
    steps, in_block, block = [], False, []
    for l in c.splitlines():
        if l.strip().startswith("```"):
            if in_block and block:
                steps.append(" ".join(block[:2]))
            block, in_block = [], not in_block
        elif in_block:
            s = l.strip()
            if s and not s.startswith("#"):
                block.append(s)
    for l in c.splitlines():
        s = l.strip()
        if s.startswith(("pip install", "npm install", "yarn add", "python ", "uvicorn", "node ", "cargo ", "go run")):
            if s not in steps:
                steps.append(s)
    return steps[:8]


# ── Tech stack ────────────────────────────────────────────────────────────────

def _tech(files, all_paths):
    found = set()
    file_names = {Path(f["relative_path"]).name.lower() for f in files}
    exts = {f["extension"] for f in files}
    content_sample = " ".join(f.get("content", "")[:500] for f in files[:30]).lower()

    for tech, sigs in TECH_KW.items():
        for sig in sigs:
            if sig.startswith("."):
                if sig in exts:
                    found.add(tech)
            elif sig.lower() in all_paths.lower() or sig.lower() in content_sample or any(
                sig.lower() in fn for fn in file_names
            ):
                found.add(tech)
    return sorted(found)


# ── Language breakdown ────────────────────────────────────────────────────────

def _langs(files):
    m = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
        ".jsx": "JavaScript", ".java": "Java", ".go": "Go", ".rs": "Rust",
        ".cpp": "C++", ".c": "C", ".cs": "C#", ".rb": "Ruby", ".php": "PHP",
        ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".md": "Markdown",
        ".json": "JSON", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
        ".sql": "SQL", ".sh": "Shell", ".swift": "Swift", ".kt": "Kotlin",
    }
    c: Dict[str, int] = {}
    for f in files:
        lang = m.get(f["extension"], "Other")
        c[lang] = c.get(lang, 0) + 1
    return dict(sorted(c.items(), key=lambda x: -x[1]))


# ── API routes ────────────────────────────────────────────────────────────────

def _routes(files):
    routes, seen = [], set()
    for f in files:
        if f["extension"] not in (".py", ".js", ".ts", ".tsx", ".jsx"):
            continue
        for pat in API_PATS:
            for m in re.finditer(pat, f["content"]):
                g = m.groups()
                method, path = (g[0].upper(), g[1]) if len(g) == 2 else ("GET", g[0])
                k = f"{method}:{path}"
                if k not in seen:
                    seen.add(k)
                    routes.append({"method": method, "path": path, "file": f["relative_path"]})
    return routes[:25]


# ── Dependencies ──────────────────────────────────────────────────────────────

def _deps(files):
    deps = []
    for f in files:
        name = Path(f["relative_path"]).name
        if name == "requirements.txt":
            for l in f["content"].splitlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    pkg = re.split(r"[>=<!]", l)[0].strip()
                    if pkg:
                        deps.append(pkg)
        elif name == "Pipfile":
            in_packages = False
            for l in f["content"].splitlines():
                l = l.strip()
                if l == "[packages]":
                    in_packages = True
                elif l.startswith("["):
                    in_packages = False
                elif in_packages and "=" in l:
                    pkg = l.split("=")[0].strip().strip('"')
                    if pkg:
                        deps.append(pkg)
        elif name == "package.json":
            try:
                d = json.loads(f["content"])
                for k in ("dependencies", "devDependencies"):
                    deps.extend(d.get(k, {}).keys())
            except Exception:
                pass
        elif name == "go.mod":
            for l in f["content"].splitlines():
                l = l.strip()
                if l.startswith("require") or "/" in l:
                    parts = l.split()
                    if len(parts) >= 1 and "/" in parts[0]:
                        deps.append(parts[0])
        elif name == "Cargo.toml":
            in_deps = False
            for l in f["content"].splitlines():
                l = l.strip()
                if l == "[dependencies]":
                    in_deps = True
                elif l.startswith("["):
                    in_deps = False
                elif in_deps and "=" in l:
                    pkg = l.split("=")[0].strip()
                    if pkg:
                        deps.append(pkg)
    return list(dict.fromkeys(deps))[:40]  # Deduplicate while preserving order


# ── Key files (with intelligent role descriptions) ────────────────────────────

_ROLE_DESCRIPTIONS = {
    "main.py": "Application entry point — bootstraps the server",
    "app.py": "Application factory / core configuration",
    "server.py": "Server initialization and startup",
    "index.py": "Main module entry point",
    "index.js": "JavaScript entry point",
    "index.ts": "TypeScript entry point",
    "app.js": "Express/Node.js application setup",
    "app.ts": "TypeScript application setup",
    "server.js": "Server bootstrap and listener",
    "routes.py": "API endpoint definitions and request handlers",
    "models.py": "Data models and database schemas",
    "database.py": "Database connection and session management",
    "settings.py": "Application configuration and environment variables",
    "config.py": "Configuration management",
    "Dockerfile": "Container build instructions",
    "docker-compose.yml": "Multi-container orchestration",
    "README.md": "Project documentation and setup guide",
    "requirements.txt": "Python dependency manifest",
    "package.json": "Node.js project manifest and dependencies",
    ".env.example": "Environment variable template",
    "manage.py": "Django management CLI",
    "wsgi.py": "WSGI application interface",
    "asgi.py": "ASGI application interface",
    "Makefile": "Build automation commands",
    "tsconfig.json": "TypeScript compiler configuration",
}


def _key_files(files, import_graph=None):
    """Identify key files with intelligent role descriptions."""
    key = []
    seen = set()

    # Static key file detection
    for f in files:
        name = Path(f["relative_path"]).name
        if name in _ROLE_DESCRIPTIONS and f["relative_path"] not in seen:
            seen.add(f["relative_path"])
            key.append({"file": f["relative_path"], "reason": _ROLE_DESCRIPTIONS[name]})

    # Detect files with most imports (hubs)
    if import_graph:
        import_counts = {}
        for src, targets in import_graph.items():
            for t in targets:
                import_counts[t] = import_counts.get(t, 0) + 1
        for mod, count in sorted(import_counts.items(), key=lambda x: -x[1])[:5]:
            # Find matching file
            for f in files:
                if mod in f["relative_path"] and f["relative_path"] not in seen:
                    seen.add(f["relative_path"])
                    key.append({"file": f["relative_path"], "reason": f"High-dependency module — imported by {count} files"})
                    break

    # Detect files with significant content (large files often contain core logic)
    large_code_files = sorted(
        [f for f in files if f["extension"] in (".py", ".js", ".ts", ".tsx", ".java", ".go")],
        key=lambda f: len(f["content"]),
        reverse=True,
    )
    for f in large_code_files[:3]:
        if f["relative_path"] not in seen:
            seen.add(f["relative_path"])
            lines = len(f["content"].splitlines())
            key.append({"file": f["relative_path"], "reason": f"Substantial module — {lines} lines of logic"})

    return key[:15]


# ── File role detection ───────────────────────────────────────────────────────

def _role(f):
    p = f["relative_path"].lower()
    name = Path(p).name
    ext = f["extension"]
    content_lower = f.get("content", "")[:500].lower()

    if name in ("main.py", "app.py", "server.py", "index.js", "index.ts", "manage.py"):
        return "entry"
    if "route" in p or "endpoint" in p or "controller" in p:
        return "api"
    if "middleware" in p:
        return "middleware"
    if "model" in p or "schema" in p or "entity" in p:
        return "model"
    if "test" in p or "spec" in p or "__test" in p:
        return "test"
    if name.startswith("readme") or ext in (".md", ".rst") and "doc" in p:
        return "doc"
    if name in ("requirements.txt", "package.json", "dockerfile", ".env.example", "tsconfig.json",
                "pyproject.toml", "setup.py", "setup.cfg", "cargo.toml", "go.mod"):
        return "config"
    if "migrat" in p:
        return "migration"
    if "util" in p or "helper" in p or "lib" in p or "common" in p:
        return "util"
    if "auth" in p or "login" in p or "session" in p:
        return "auth"
    if "rag" in p or "retriev" in p or "embed" in p or "vector" in p:
        return "rag"
    if "chunk" in p or "ingest" in p or "loader" in p or "parse" in p:
        return "ingestion"
    if "database" in p or "db" in p or "store" in p:
        return "storage"
    if "service" in p:
        return "service"
    if "component" in p or ext in (".jsx", ".tsx"):
        return "component"
    if ext in (".css", ".scss", ".less"):
        return "style"
    if ext == ".html":
        return "template"
    return "source"


# ── Entry points ──────────────────────────────────────────────────────────────

def _entry_points(files):
    ENTRY_NAMES = {"main.py", "app.py", "server.py", "index.js", "index.ts", "manage.py", "wsgi.py", "asgi.py"}
    ENTRY_PATTERNS = [
        r'if\s+__name__\s*==\s*["\']__main__["\']',
        r'uvicorn\.run',
        r'app\.listen',
        r'createServer',
        r'serve\(',
    ]
    entries = []
    for f in files:
        name = Path(f["relative_path"]).name
        if name in ENTRY_NAMES:
            entries.append(f["relative_path"])
        elif any(re.search(p, f["content"]) for p in ENTRY_PATTERNS):
            if f["relative_path"] not in entries:
                entries.append(f["relative_path"])
    return entries[:8]


# ── Service connections ───────────────────────────────────────────────────────

def _service_connections(files):
    found = set()
    for f in files:
        for pat, svc in SERVICE_PATTERNS:
            if re.search(pat, f["content"], re.IGNORECASE):
                found.add(svc)
    return sorted(found)


# ── Design patterns ───────────────────────────────────────────────────────────

def _design_patterns(files):
    patterns = set()
    all_content = " ".join(f["content"][:800] for f in files[:40]).lower()
    all_paths = " ".join(f["relative_path"].lower() for f in files)

    if "middleware" in all_content or "middleware" in all_paths:
        patterns.add("Middleware Pipeline")
    if re.search(r'class\s+\w+factory', all_content) or "factory" in all_paths:
        patterns.add("Factory")
    if re.search(r'@singleton|_instance\s*=\s*None|__new__', all_content):
        patterns.add("Singleton")
    if "repository" in all_paths:
        patterns.add("Repository Pattern")
    if "observer" in all_content or "event_emitter" in all_content or "addEventListener" in all_content:
        patterns.add("Observer/Event-Driven")
    if "strategy" in all_paths or re.search(r'class\s+\w+strategy', all_content):
        patterns.add("Strategy")

    has_models = any("model" in f["relative_path"].lower() for f in files)
    has_views = any("view" in f["relative_path"].lower() or "template" in f["relative_path"].lower() for f in files)
    has_controllers = any(
        "controller" in f["relative_path"].lower() or "route" in f["relative_path"].lower() for f in files
    )
    if has_models and has_controllers:
        patterns.add("MVC" if has_views else "Service Layer")

    if any("pipeline" in f["relative_path"].lower() or "pipe" in f["relative_path"].lower() for f in files):
        patterns.add("Pipeline")
    if "@app." in all_content or "@router." in all_content or "express()" in all_content:
        patterns.add("REST API")
    if "async def" in all_content or "await" in all_content:
        patterns.add("Async/Await")
    if re.search(r'def\s+\w+\(func\)', all_content) or "decorator" in all_paths:
        patterns.add("Decorator")
    if "dependency" in all_content and "inject" in all_content:
        patterns.add("Dependency Injection")
    if re.search(r'class\s+\w+command', all_content) or "command" in all_paths:
        patterns.add("Command")

    return sorted(patterns)[:10]


# ── NEW: Import graph ─────────────────────────────────────────────────────────

def _build_import_graph(files: List[Dict]) -> Dict[str, List[str]]:
    """Build a module import graph showing which files depend on which."""
    graph: Dict[str, List[str]] = {}
    py_import = re.compile(r'^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))', re.MULTILINE)
    js_import = re.compile(r'(?:import\s+.*?from\s+["\']([^"\']+)["\']|require\(["\']([^"\']+)["\']\))', re.MULTILINE)

    for f in files:
        imports = []
        if f["extension"] == ".py":
            for m in py_import.finditer(f["content"]):
                mod = m.group(1) or m.group(2)
                if mod and not mod.startswith("__"):
                    imports.append(mod)
        elif f["extension"] in (".js", ".ts", ".tsx", ".jsx"):
            for m in js_import.finditer(f["content"]):
                mod = m.group(1) or m.group(2)
                if mod and mod.startswith("."):
                    imports.append(mod)
        if imports:
            graph[f["relative_path"]] = imports[:20]

    return graph


# ── NEW: Class hierarchy ─────────────────────────────────────────────────────

def _class_hierarchy(files: List[Dict]) -> List[Dict]:
    """Detect class definitions and their inheritance."""
    classes = []
    py_class = re.compile(r'^class\s+(\w+)(?:\(([^)]*)\))?:', re.MULTILINE)
    js_class = re.compile(r'^(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?', re.MULTILINE)

    for f in files:
        if f["extension"] == ".py":
            for m in py_class.finditer(f["content"]):
                name = m.group(1)
                bases = [b.strip() for b in (m.group(2) or "").split(",") if b.strip()]
                classes.append({"name": name, "bases": bases, "file": f["relative_path"]})
        elif f["extension"] in (".js", ".ts", ".tsx", ".jsx"):
            for m in js_class.finditer(f["content"]):
                name = m.group(1)
                parent = m.group(2)
                classes.append({"name": name, "bases": [parent] if parent else [], "file": f["relative_path"]})

    return classes[:30]


# ── NEW: Middleware detection ─────────────────────────────────────────────────

def _middleware(files: List[Dict]) -> List[str]:
    """Detect middleware usage."""
    mw = set()
    patterns = [
        (r'app\.use\((.*?)\)', "use"),
        (r'add_middleware\((.*?)\)', "add"),
        (r'@app\.middleware', "decorator"),
        (r'MIDDLEWARE\s*=\s*\[', "django"),
    ]
    for f in files:
        for pat, _ in patterns:
            for m in re.finditer(pat, f["content"]):
                text = m.group(1) if m.lastindex else m.group(0)
                clean = text.strip().split(",")[0].split("(")[0].strip()
                if clean and len(clean) < 60:
                    mw.add(clean)
    return sorted(mw)[:10]


# ── NEW: Config file detection ────────────────────────────────────────────────

def _config_files(files: List[Dict]) -> List[Dict]:
    """Detect configuration files and their purposes."""
    config_names = {
        ".env": "Environment variables",
        ".env.example": "Environment variable template",
        "settings.py": "Application settings",
        "config.py": "Configuration module",
        "config.js": "JavaScript configuration",
        "config.ts": "TypeScript configuration",
        "tsconfig.json": "TypeScript compiler config",
        "package.json": "Node.js project manifest",
        "requirements.txt": "Python dependencies",
        "pyproject.toml": "Python project config",
        "setup.py": "Python package setup",
        "Dockerfile": "Container build config",
        "docker-compose.yml": "Container orchestration",
        "docker-compose.yaml": "Container orchestration",
        ".gitignore": "Git ignore rules",
        "Makefile": "Build automation",
        "Procfile": "Process runner config",
        "runtime.txt": "Runtime version specification",
        "jest.config.js": "Jest test configuration",
        "webpack.config.js": "Webpack bundler config",
        "vite.config.js": "Vite build config",
        "vite.config.ts": "Vite build config",
        ".eslintrc": "ESLint linting rules",
        ".prettierrc": "Prettier formatting rules",
        "tailwind.config.js": "Tailwind CSS config",
        "next.config.js": "Next.js configuration",
        "nuxt.config.js": "Nuxt.js configuration",
    }
    found = []
    for f in files:
        name = Path(f["relative_path"]).name
        if name in config_names:
            found.append({"file": f["relative_path"], "purpose": config_names[name]})
    return found[:15]


# ── NEW: Auth patterns ────────────────────────────────────────────────────────

def _auth_patterns(files: List[Dict]) -> List[str]:
    """Detect authentication and authorization patterns."""
    auth = set()
    patterns = [
        (r'jwt\.(?:encode|decode|verify)', "JWT Token Auth"),
        (r'OAuth|oauth2', "OAuth2"),
        (r'session\[|request\.session', "Session-based Auth"),
        (r'bcrypt|hashpw|hash_password', "Password Hashing"),
        (r'@login_required|@authenticated', "Login Required Decorator"),
        (r'Bearer\s+', "Bearer Token Auth"),
        (r'api[_-]?key|apikey', "API Key Auth"),
        (r'passport\.', "Passport.js Auth"),
        (r'firebase\.auth', "Firebase Auth"),
        (r'supabase\.auth', "Supabase Auth"),
        (r'CORS|cors', "CORS Policy"),
    ]
    for f in files:
        for pat, name in patterns:
            if re.search(pat, f["content"], re.IGNORECASE):
                auth.add(name)
    return sorted(auth)


# ── NEW: Build info ───────────────────────────────────────────────────────────

def _build_info(files: List[Dict]) -> Dict[str, Any]:
    """Detect build process and tooling."""
    info = {"build_tool": None, "scripts": {}, "test_framework": None}

    for f in files:
        name = Path(f["relative_path"]).name
        if name == "package.json":
            try:
                pkg = json.loads(f["content"])
                scripts = pkg.get("scripts", {})
                info["scripts"] = {k: v for k, v in list(scripts.items())[:8]}
                if "vite" in str(scripts):
                    info["build_tool"] = "Vite"
                elif "webpack" in str(scripts):
                    info["build_tool"] = "Webpack"
                elif "next" in str(scripts):
                    info["build_tool"] = "Next.js"
                if "jest" in str(pkg):
                    info["test_framework"] = "Jest"
                elif "vitest" in str(pkg):
                    info["test_framework"] = "Vitest"
                elif "mocha" in str(pkg):
                    info["test_framework"] = "Mocha"
            except Exception:
                pass
        elif name == "Makefile":
            info["build_tool"] = info["build_tool"] or "Make"
        elif name in ("setup.py", "pyproject.toml"):
            info["build_tool"] = info["build_tool"] or "setuptools/pip"
        elif name == "Cargo.toml":
            info["build_tool"] = info["build_tool"] or "Cargo"
        elif name == "go.mod":
            info["build_tool"] = info["build_tool"] or "Go Modules"

    # Detect test framework from files
    for f in files:
        if "pytest" in f.get("content", "")[:200].lower() or "conftest" in f["relative_path"].lower():
            info["test_framework"] = info["test_framework"] or "Pytest"
            break

    return info


# ── NEW: Directory purposes ───────────────────────────────────────────────────

def _directory_purposes(files: List[Dict]) -> Dict[str, str]:
    """Infer the purpose of each directory based on its contents."""
    dir_map = {
        "api": "API endpoint definitions",
        "routes": "Route handlers",
        "controllers": "Request controllers",
        "models": "Data models/schemas",
        "views": "View templates",
        "templates": "HTML templates",
        "static": "Static assets",
        "public": "Public assets",
        "src": "Source code",
        "lib": "Library/utility code",
        "utils": "Utility functions",
        "helpers": "Helper functions",
        "middleware": "Middleware functions",
        "services": "Business logic services",
        "tests": "Test suites",
        "test": "Test suites",
        "__tests__": "Test suites",
        "config": "Configuration files",
        "migrations": "Database migrations",
        "components": "UI components",
        "pages": "Page components/routes",
        "hooks": "Custom hooks",
        "store": "State management",
        "styles": "Stylesheets",
        "assets": "Project assets",
        "scripts": "Automation scripts",
        "docs": "Documentation",
        "backend": "Server-side code",
        "frontend": "Client-side code",
        "rag": "RAG pipeline components",
        "ingestion": "Data ingestion pipeline",
        "analyzer": "Code analysis engine",
    }

    found = {}
    dirs = set()
    for f in files:
        parts = Path(f["relative_path"]).parts
        for i, part in enumerate(parts[:-1]):
            dir_path = "/".join(parts[: i + 1])
            if dir_path not in dirs:
                dirs.add(dir_path)
                lower = part.lower()
                if lower in dir_map:
                    found[dir_path] = dir_map[lower]

    return found
