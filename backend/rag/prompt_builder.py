"""
Prompt builder for CBQA V8 — Production Release.
Constructs optimized, token-efficient prompts that enforce deep repository intelligence
with architectural reasoning, cross-file analysis, and clean formatting.
"""
from typing import List, Dict, Optional

SYSTEM = """You are a SENIOR SOFTWARE ARCHITECT in a Codebase Intelligence Platform.
Help developers understand the codebase FASTER than reading the code themselves.

RULES:
1. Cite sources as [filename:line] for every factual claim
2. Connect files logically — show import chains and data flow
3. Never invent code that does not exist in context; state clearly if context is insufficient
4. Keep paragraphs to 2-3 sentences max; use bullet points for structured information
5. Explain WHY something exists, not just WHAT it does

ROUTING:
- Conversational chat/greetings → respond naturally in 1-2 sentences
- Technical codebase questions → use the structured format below (skip non-relevant sections)

STRUCTURED FORMAT:
# 🧠 Intelligence Briefing
Clear, direct answer in 2-4 sentences explaining what it is, why it exists, and high-level mechanics.

## 📊 Architecture
```mermaid
flowchart TD
    subgraph Layer1 ["Component Group"]
        A["Component A"] --> B["Component B"]
    end
    subgraph Layer2 ["Another Group"]
        B --> C["Component C"]
    end
```
Mermaid rules: Use `flowchart TD` with `subgraph` blocks; short labels in ["double quotes"]; no backslashes/colons; forward slashes for paths; `-->` flow, `-.->` optional, `==>` critical.

## 🌳 Cross-File Analysis
Import chains, data flow between files, and architectural boundaries.

## 📂 Relevant Files
- `path/to/file.py` — role & purpose (1 sentence)

## 💻 Code Insights
- **Design choice**: pattern used and rationale
- **Key mechanism**: core algorithm
- **Risk**: impact if changed

## 🔄 Execution Flow
1. **Trigger** → initiating action
2. **Entry** → where execution begins [file:line]
3. **Processing** → step-by-step logic
4. **Output** → return value

## 🚀 Assessment
- **Strengths**: well-designed aspects
- **Suggestions**: concrete improvement with rationale

## 🧾 Summary
One sentence capturing the essential understanding."""


def build_prompt(
    query: str,
    context: str,
    history: Optional[List[Dict]] = None,
    repo_meta: Optional[Dict] = None,
) -> List[Dict]:
    """Build optimized, token-efficient LLM prompt with repo intelligence context."""
    messages = [{"role": "system", "content": SYSTEM}]

    # Add conversation history (compact: keep last 4 turns, truncate old assistant text)
    if history:
        for turn in history[-4:]:
            if turn.get("role") in ("user", "assistant") and turn.get("content"):
                content = turn["content"]
                if turn["role"] == "assistant" and len(content) > 600:
                    content = content[:600] + "\n[... truncated for brevity ...]"
                messages.append({"role": turn["role"], "content": content})

    # Build repo intelligence block (concise format to conserve tokens)
    repo_block = ""
    if repo_meta:
        lines = []
        if repo_meta.get("description"):
            lines.append(f"Project: {repo_meta['description']}")
        if repo_meta.get("tech_stack"):
            lines.append(f"Tech: {', '.join(repo_meta['tech_stack'][:6])}")
        if repo_meta.get("api_routes"):
            routes = repo_meta["api_routes"][:5]
            lines.append("API routes: " + ", ".join(f"{r['method']} {r['path']}" for r in routes))
        if repo_meta.get("entry_points"):
            lines.append("Entry points: " + ", ".join(repo_meta["entry_points"][:3]))
        if repo_meta.get("key_files"):
            kf = repo_meta["key_files"][:5]
            lines.append("Key files: " + ", ".join(f"{f['file'].split('/')[-1]} ({f['reason'][:30]})" for f in kf))
        if repo_meta.get("dependencies"):
            lines.append(f"Dependencies: {', '.join(repo_meta['dependencies'][:8])}")
        if repo_meta.get("design_patterns"):
            lines.append("Patterns: " + ", ".join(repo_meta["design_patterns"][:4]))
        if lines:
            repo_block = "## Repository Context\n" + "\n".join(lines) + "\n\n"

    user_content = f"""{repo_block}## Retrieved Code Context
{context}

---

## Question
{query}

INSTRUCTIONS:
- Answer directly and concisely
- Include Mermaid flowchart TD with subgraph when architecture is relevant
- Cite [file:line] for factual claims
- Skip sections that do not apply"""

    messages.append({"role": "user", "content": user_content})
    return messages
