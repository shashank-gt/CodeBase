"""
Repository summarizer for CBQA V7 — generates deep intelligence briefings.
"""
import logging
from typing import List, Dict
from .llm_client import call_llm

logger = logging.getLogger(__name__)

_SYS = """You are a senior software architect providing a DEEP repository intelligence briefing.
Your goal is to help someone understand this entire codebase in under 2 minutes.

Generate a structured overview that CREATES UNDERSTANDING, not information overload.
Think like a senior engineer who has spent a week studying this repository.

Format your response EXACTLY like this:

## 🧠 Repository Overview
2-3 sentences: What is this project? What problem does it solve? Who is it for?
Be specific about the domain and value proposition.

## 📊 Architecture

```mermaid
flowchart TD
    subgraph Group1 ["Logical Module Group"]
        A["Component A"] --> B["Component B"]
    end
    subgraph Group2 ["Another Module Group"]
        B --> C["Component C"]
    end
```

Show a professional system-level architecture as a Mermaid diagram.
- Use `flowchart TD` or `flowchart LR` (NEVER legacy `graph` syntax)
- Use `subgraph` to group related modules into clear architectural layers
- Use simple node IDs (A, B, C) with labels inside ["double quotes"]
- NEVER use colons, backslashes, parentheses, or special chars inside quotes
- Show how major components connect and data flows between layers

## 🌳 Key Components
For each major component:
- **Component Name** — What it does, WHY it exists, and what depends on it (1-2 sentences)

## 🔗 Cross-File Relationships
Show the most important inter-module dependencies:
- Which files import from which?
- What shared state or configuration connects modules?
- Where are the architectural boundaries?

## 🔄 Main Data Flow
Show the primary execution flow:
1. **Input** → What triggers the system
2. **Processing** → Key processing steps with file references
3. **Output** → What the user gets

## 🏗 Design Patterns & Decisions
- What architectural patterns are used (MVC, pipeline, factory, etc.)?
- Why were key technologies chosen?
- What are the most important design decisions?

## ⚙ Tech Stack & Dependencies
- List each important technology and WHY it was chosen (1 sentence each)

## 🚀 Senior Engineer Assessment

### Strengths
- What's well-designed (be specific about patterns and implementations)

### Areas for Improvement
- Concrete, actionable suggestions for the architecture

### Scalability Notes
- What would need to change at 10x scale

## 🧾 One-Line Summary
One sentence that captures the essence and value of this project.
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
        for f in dir_files[:10]:
            # Include more meaningful lines for deeper understanding
            content_lines = [l for l in f["content"].splitlines() if l.strip()][:12]
            preview = "\n".join(content_lines)
            manifest_parts.append(f"**{f['relative_path']}** ({f['extension']}, {len(f['content'])} bytes)\n```\n{preview}\n```")

    manifest = "\n\n".join(manifest_parts[:120])

    try:
        return call_llm([
            {"role": "system", "content": _SYS},
            {"role": "user", "content": f"Analyze this repository ({len(files)} files) and provide the deep intelligence briefing:\n\n{manifest}"}
        ])
    except Exception as e:
        return f"Summarization failed: {e}"
