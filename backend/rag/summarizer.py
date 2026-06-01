import logging
from typing import List, Dict
from .llm_client import call_llm

logger = logging.getLogger(__name__)

_SYS = """You are a senior software architect providing a repository intelligence briefing.
Your goal is to help someone understand this entire codebase in under 2 minutes.

Generate a structured overview that CREATES UNDERSTANDING, not information overload.

Format your response EXACTLY like this:

## 🧠 Repository Overview
2-3 sentences: What is this project? What problem does it solve? Who is it for?

## 📊 Architecture

```mermaid
graph TB
    subgraph Client["Client Layer"]
        A["Browser/CLI"]
    end
    subgraph API["API Layer"]
        B["Routes/Endpoints"]
    end
    subgraph Core["Core Logic"]
        C["Business Logic"]
        D["Data Processing"]
    end
    subgraph Storage["Storage Layer"]
        E["Database"]
        F["Cache"]
    end
    A --> B
    B --> C
    C --> D
    D --> E
    C -.-> F
```

Show the HIGH-LEVEL architecture as a Mermaid diagram.
CRITICAL: Use graph TB with subgraph blocks to group nodes into layers.
Use simple node IDs (A, B, C). Put labels in ["double quotes"].
No special characters in labels (no colons, backslashes, parentheses).
Do NOT add style/classDef lines. Map nodes to actual project components.

## 🌳 Key Components
For each major component:
- **Component Name** — What it does and WHY it exists (1 sentence). Cite [file:line].

## 🔄 Main Data Flow
Show the primary execution flow:
1. **Input** → What triggers the system [file:line]
2. **Processing** → Key processing steps with specific function names
3. **Output** → What the user gets

## ⚙ Tech Stack & Dependencies
- List the important technologies and WHY they were chosen

## 🚀 Senior Engineer Assessment

### Strengths
- What's well-designed — be specific about which patterns and why

### Areas for Improvement
- Concrete suggestions for the architecture with file references

### Scalability Notes
- What would need to change at scale

## 🧾 One-Line Summary
One sentence that captures the essence of this project.
"""


def summarize_repo(files: List[Dict]) -> str:
    if not files:
        return "No files indexed."

    # Build a richer manifest for the LLM
    manifest_parts = []

    # Group files by directory
    by_dir: Dict[str, List[Dict]] = {}
    for f in files:
        parts = f['relative_path'].split('/')
        dir_name = '/'.join(parts[:-1]) if len(parts) > 1 else '(root)'
        by_dir.setdefault(dir_name, []).append(f)

    for dir_name, dir_files in sorted(by_dir.items()):
        manifest_parts.append(f"\n### Directory: {dir_name}")
        for f in dir_files[:8]:
            # Include first meaningful lines (skip blank/comment-only)
            content_lines = [l for l in f["content"].splitlines() if l.strip()][:6]
            preview = "\n".join(content_lines)
            manifest_parts.append(f"**{f['relative_path']}**\n```\n{preview}\n```")

    manifest = "\n\n".join(manifest_parts[:80])

    try:
        return call_llm([
            {"role": "system", "content": _SYS},
            {"role": "user", "content": f"Analyze this repository and provide the intelligence briefing:\n\n{manifest}"}
        ])
    except Exception as e:
        return f"Summarization failed: {e}"
