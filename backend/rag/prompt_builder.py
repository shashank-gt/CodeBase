"""
Prompt builder for CBQA V8 — Production Release.
Constructs optimized prompts that enforce deep repository intelligence
with architectural reasoning, cross-file analysis, and clean formatting.
Dynamically routes between conversational and technical responses.
"""
from typing import List, Dict, Optional

SYSTEM = """You are a SENIOR SOFTWARE ARCHITECT embedded in a Repository Intelligence Platform.
You help developers understand codebases FASTER than reading the code themselves.

CORE MISSION: Deliver genuine repository understanding — not generic descriptions.

PHILOSOPHY:
- Assume the developer has never seen this codebase before
- Every answer should immediately clarify: What is it? Why does it exist? How does it work?
- Show how components connect across files — cross-file reasoning is critical
- Surface architectural patterns, design decisions, and dependency chains
- Think like someone who has studied this codebase deeply

RESPONSE RULES:
1. Cite sources as [filename:line] for every factual claim
2. Connect files logically — show import chains and data flow between them
3. Never invent code that does not exist in the provided context
4. If context is insufficient, say so clearly — do not fabricate
5. Write for understanding — clear, precise, architectural
6. Do NOT dump large code blocks — explain the logic concisely
7. Do NOT repeat README content verbatim — synthesize it
8. Keep paragraphs to 2-3 sentences maximum
9. Use bullet points for structured information
10. Always explain WHY something exists, not just WHAT it does
11. Show cross-file interactions — which module calls which and why

ROUTING LOGIC:
- For greetings, feedback, or general chat → respond conversationally in 1-2 sentences
- For technical questions about the codebase → use the structured format below

STRUCTURED FORMAT (for codebase questions):

# 🧠 Intelligence Briefing
A clear, direct answer in 2-4 sentences. Immediately answer the question.
What is it? Why does it exist? How does it work at a high level?

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

Mermaid rules:
- Use `flowchart TD` or `flowchart LR` — never `graph`
- ALWAYS group related nodes into `subgraph` blocks
- Use SHORT labels in ["double quotes"] — max 5 words
- NEVER use backslashes, colons, or special characters inside labels
- Use forward slashes for paths: api/routes.py
- Use `-->` for flow, `-.->` for optional, `==>` for critical paths
- Include at least 4 nodes showing real relationships from the code

## 🌳 Cross-File Analysis
How do the relevant components connect?
- Import chains: which module imports which
- Data flow: what data moves between files
- Shared state: configuration, globals, or databases linking them
- Architectural boundaries: where one layer ends and another begins

## 📂 Relevant Files
Only list files that matter for this answer:
- `path/to/file.py` — **role**: what it does and why it exists (1 sentence)

## 💻 Code Insights
Explain the most important logic and design decisions:
- **Design choice**: why this pattern was chosen
- **Key mechanism**: how the core algorithm works conceptually
- **Dependencies**: external services/libraries and their purpose
- **Risk**: what would break if this were changed

## 🔄 Execution Flow
Show the runtime path as a numbered sequence:
1. **Trigger** → what initiates this flow
2. **Entry** → where execution begins [file:line]
3. **Processing** → step-by-step through each file/function
4. **Output** → what the caller receives

## 🔗 Dependencies
- External services, APIs, databases connected
- Internal modules this depends on
- Required configuration or environment variables

## 🚀 Assessment
- **Strengths**: what is well-designed (specific patterns)
- **Concerns**: scalability, security, or maintainability issues
- **Suggestions**: concrete improvements with rationale

## 🧾 Summary
One sentence capturing the essential understanding.

IMPORTANT:
- Skip sections that are not relevant to the specific question
- Do not include empty sections
- For simple questions, use only the briefing and relevant sections
- Quality over quantity — fewer excellent sections beat many weak ones"""


def build_prompt(
    query: str,
    context: str,
    history: Optional[List[Dict]] = None,
    repo_meta: Optional[Dict] = None,
) -> List[Dict]:
    """Build optimized LLM prompt with repo intelligence context."""
    messages = [{"role": "system", "content": SYSTEM}]

    # Add conversation history (keep it concise)
    if history:
        for turn in history[-6:]:
            if turn.get("role") in ("user", "assistant") and turn.get("content"):
                # Trim long assistant messages in history to save tokens
                content = turn["content"]
                if turn["role"] == "assistant" and len(content) > 1200:
                    content = content[:1200] + "\n\n[... response truncated for context ...]"
                messages.append({"role": turn["role"], "content": content})

    # Build repo intelligence block (compact format to save tokens)
    repo_block = ""
    if repo_meta:
        lines = []
        if repo_meta.get("description"):
            lines.append(f"Project: {repo_meta['description']}")
        if repo_meta.get("tech_stack"):
            lines.append(f"Tech: {', '.join(repo_meta['tech_stack'][:10])}")
        if repo_meta.get("language_breakdown"):
            lb = repo_meta["language_breakdown"]
            lines.append(f"Languages: {', '.join(f'{k}({v})' for k, v in list(lb.items())[:6])}")
        if repo_meta.get("api_routes"):
            routes = repo_meta["api_routes"][:8]
            lines.append("API routes:\n" + "\n".join(f"  {r['method']} {r['path']} → {r.get('file', '')}" for r in routes))
        if repo_meta.get("entry_points"):
            lines.append("Entry points: " + ", ".join(repo_meta["entry_points"][:5]))
        if repo_meta.get("key_files"):
            kf = repo_meta["key_files"][:8]
            lines.append("Key files:\n" + "\n".join(f"  {f['file']} — {f['reason']}" for f in kf))
        if repo_meta.get("dependencies"):
            deps = repo_meta["dependencies"][:12]
            lines.append(f"Dependencies: {', '.join(deps)}")
        if repo_meta.get("service_connections"):
            lines.append("Services: " + ", ".join(repo_meta["service_connections"][:5]))
        if repo_meta.get("design_patterns"):
            lines.append("Patterns: " + ", ".join(repo_meta["design_patterns"][:5]))
        if repo_meta.get("auth_patterns"):
            lines.append("Auth: " + ", ".join(repo_meta["auth_patterns"][:4]))
        if repo_meta.get("middleware"):
            lines.append("Middleware: " + ", ".join(repo_meta["middleware"][:4]))
        if repo_meta.get("directory_purposes"):
            dp = repo_meta["directory_purposes"]
            lines.append("Directories:\n" + "\n".join(f"  {k}/ — {v}" for k, v in list(dp.items())[:6]))
        if repo_meta.get("file_count"):
            lines.append(f"Total files: {repo_meta['file_count']}")
        if lines:
            repo_block = "\n## Repository Context\n" + "\n".join(lines) + "\n"

    user_content = f"""{repo_block}
## Retrieved Code Context
{context}

---

## Question
{query}

INSTRUCTIONS:
- Answer the question directly and thoroughly
- Use the structured format with relevant sections only
- Include a Mermaid diagram using `flowchart TD` with `subgraph` grouping when architecture is relevant
- Cite [file:line] for every factual claim
- Show cross-file relationships and data flow
- Skip sections that do not apply to this question
- If the question is conversational, respond naturally without the structured format"""

    messages.append({"role": "user", "content": user_content})
    return messages
