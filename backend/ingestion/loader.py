"""
Repository loader: clone (via ZIP download) or read local directories,
then walk the codebase and extract source files.
"""
import os, shutil, logging, zipfile, io
from pathlib import Path
from typing import List, Dict, Callable, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

CODE_EXT = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".rs",
    ".cpp", ".c", ".h", ".cs", ".php", ".swift", ".kt", ".scala", ".sh",
    ".yaml", ".yml", ".toml", ".json", ".md", ".txt", ".sql", ".html", ".css", ".scss",
}
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", "vendor", ".idea", ".vscode", "site-packages",
}


def _skip(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_DIRS or part.endswith((".egg-info", ".dist-info")):
            return True
    return False


def clone_repo(url: str, target: str) -> str:
    """Download a GitHub repository as a ZIP archive (no Git required)."""
    import requests

    url = url.strip().rstrip("/")
    if not (url.startswith("https://github.com") or url.startswith("http://github.com")):
        raise ValueError(f"Invalid GitHub URL: {url}")

    # Normalise URL → ZIP download link
    # https://github.com/user/repo  →  https://github.com/user/repo/archive/refs/heads/main.zip
    clean = url.replace(".git", "")
    zip_url = f"{clean}/archive/refs/heads/main.zip"

    if os.path.exists(target):
        shutil.rmtree(target)
    os.makedirs(target, exist_ok=True)

    headers = {}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    logger.info(f"Downloading {zip_url}")
    try:
        r = requests.get(zip_url, headers=headers, timeout=60, stream=True)
        if r.status_code == 404:
            # Try 'master' branch instead of 'main'
            zip_url = f"{clean}/archive/refs/heads/master.zip"
            logger.info(f"main branch not found, trying master: {zip_url}")
            r = requests.get(zip_url, headers=headers, timeout=60, stream=True)
        r.raise_for_status()
    except Exception as e:
        raise ValueError(f"Failed to download repository: {e}")

    # Extract ZIP
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        zf.extractall(target)

    # GitHub ZIPs extract into a subfolder like 'repo-main/' — flatten it
    subdirs = [d for d in Path(target).iterdir() if d.is_dir()]
    if len(subdirs) == 1:
        inner = subdirs[0]
        for item in inner.iterdir():
            dest = Path(target) / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(dest))
        inner.rmdir()

    logger.info(f"Repository downloaded and extracted to {target}")
    return target


def read_local(path: str) -> str:
    p = os.path.abspath(path)
    if not os.path.isdir(p):
        raise ValueError(f"Not a directory: {p}")
    return p


def walk_codebase(root: str, on_file: Optional[Callable] = None) -> List[Dict]:
    root_p = Path(root)
    candidates = [
        p for p in root_p.rglob("*")
        if p.is_file() and not _skip(p) and p.suffix.lower() in CODE_EXT
    ]
    files = []
    for idx, fp in enumerate(candidates):
        if fp.stat().st_size / 1024 > settings.MAX_FILE_KB:
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if not content.strip():
            continue
        rel = str(fp.relative_to(root_p))
        files.append({
            "path": str(fp),
            "relative_path": rel,
            "extension": fp.suffix.lower(),
            "content": content,
        })
        if on_file:
            on_file(rel, idx + 1, len(candidates))
    logger.info(f"Loaded {len(files)} files from {root}")
    return files
