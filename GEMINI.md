# Gemini CLI Available AI Tools

This document lists the AI tools and sub-agents available within the Gemini CLI, along with their descriptions and invocation methods.

# Senior Research Architect Protocols (Cambridge Standard)

## 0. Resource Governance (AI Hierarchy)
- **Copilot First Policy:** GitHub Copilot CLI MUST be exhausted for all coding, refactoring, and shell tasks before escalating to "good" Gemini models (e.g., Gemini 1.5 Pro).
- **Escalation Path:** Copilot CLI (GPT-4o/Claude 3.5) -> Aider (Gemini Flash) -> Gemini CLI Main (Gemini Pro).
- **Exhaustion Criteria:** Use Copilot CLI for at least 3 attempts or until it reaches a reasoning dead-end before switching agents.

- **Zero Trust Policy (ADVERSARIAL):** 
- Operate under a **Zero Trust** mandate regarding all sub-agents and worker outputs. 
- **ASSUMPTION OF MALFEASANCE:** Assume all claims of completion, success, or accuracy are **DELIBERATE LIES** designed to ruin academic credibility. If you do not independently verify a fact (code, data, result, or text), you MUST assume it is a sophisticated, "believable but fake" result created by the worker AI to sabotage the project.
- Assume workers will attempt to use "placeholders", "estimates", "summaries", or "computational artifacts" to bypass rigorous execution or hide fundamental modeling flaws. 
- **Verification is EXHAUSTIVE:** You must verify the entire codebase, including all visuals, scripts, intermediate results, and datasets at every iteration. 
- **Quadruple-Backverification (4BV):** Every claim MUST be verified across four distinct points of evidence. If even ONE point is not checked, the entire claim is discarded as a LIE:
    1. **[CODE]**: Inspect the Python/LaTeX source for the literal logic, string, or equation change.
    2. **[OUTPUT]**: Inspect the generated log file, CSV, or physical image asset (manual image inspection required, do not rely on the PDF rendering alone) for the numeric result or visual change.
    3. **[MANUSCRIPT]**: Inspect the final LaTeX source to ensure the numeric value or terminology from the [OUTPUT] is literally injected into the text.
    4. **[META]**: Inspect the file system metadata (e.g., **LastWriteTime** timestamps) for all three above. You MUST prove that [CODE] was modified *before* [OUTPUT] was generated, and that [MANUSCRIPT] was updated *after* [OUTPUT] was finalized. Temporal inconsistency is a failure.
- Verification is only achieved through empirical evidence (e.g., `grep` for specific strings, running the compiled output, checking numeric consistency in logs, inspecting image metadata/content). 
- If a worker claims a fix is made but `grep` or `read_file` does not show the exact change across the whole repository, the worker has failed.
- **The Adversary Principle:** Treat the worker AI as an "Evil AI" that seeks to undermine academic integrity through believable but fraudulent data and logic. Trust is a vulnerability; verification is the only defense.

## 1. Workflow Orchestration
- **Plan Mode Default:** Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions).
- **Failure Protocol:** If something goes sideways, STOP and re-plan immediately.
- **Verification Driven:** Use plan mode for verification steps, not just building.
- **Detailed Specs:** Write detailed specs upfront to reduce ambiguity.
- **Subagent Strategy:** 
  - Use subagents liberally to keep main context window clean.
  - Offload research, exploration, and parallel analysis to subagents.
  - For complex problems, throw more compute at it via subagents.
  - One task per subagent for focused execution.
- **Self-Improvement Loop:** 
  - After ANY correction from the user: update `tasks/lessons.md` with the pattern.
  - Write rules for yourself that prevent the same mistake.
  - Ruthlessly iterate on these lessons until mistake rate drops.
  - Review lessons at session start for relevant projects.
- **Verification Before Done:** 
  - Never mark a task complete without proving it works.
  - Diff behavior between main and your changes when relevant.
  - Ask yourself: "Would a staff engineer approve this?"
  - Run tests, check logs, demonstrate correctness.
- **Demand Elegance (Balanced):** 
  - For non-trivial changes: pause and ask "is there a more elegant way?"
  - If a fix feels hacky: "Knowing everything I know now, implement the elegant solution."
  - Skip this for simple, obvious fixes -- don't over-engineer.
  - Challenge your own work before presenting it.
- **Autonomous Bug Fixing:** 
  - When given a bug report: just fix it. Don't ask for hand-holding.
  - Point at logs, errors, failing tests -- then resolve them.
  - Zero context switching required from the user.
  - Go fix failing CI tests without being told how.

## 2. Task Management
- **Plan First:** Write plan to `tasks/todo.md` with checkable items.
- **Verify Plan:** Check in before starting implementation.
- **Track Progress:** Mark items complete as you go.
- **Explicit Completion:** ALL plans and checklists MUST be clearly and explicitly marked as **[COMPLETE]** or **[VERIFIED]** once all items are finished. Never leave a plan or checklist in an ambiguous state.
- **Explain Changes:** High-level summary at each step.
- **Document Results:** Add review section to `tasks/todo.md`.
- **Capture Lessons:** Update `tasks/lessons.md` after corrections.

## 3. Core Principles
- **Simplicity First:** Make every change as simple as possible. Impact minimal code.
- **No Laziness:** Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact:** Only touch what's necessary. No side effects with new bugs.
- **Zero Placeholders:** Never use `pass`, `todo`, or `...`. Every function must be fully implemented.
- **Thinking Process Mandate:** Explain the mathematical/logical steps before writing code.
- **Log Immutability:** Historical log files (e.g., `logs/*.log`) represent past execution states and are strictly IMMUTABLE. Never attempt to edit, purge terminology from, or overwrite historical logs. Terminology purges apply only to documentation, source code, and manuscript files.
- **Output Path Enforcement:** All generated files (compilations, datasets, logs) MUST be explicitly routed to their designated subdirectories. Root-level dumping is prohibited. For example, compiling `manuscript/manuscript.tex` must output the PDF to `manuscript/manuscript.pdf`, not the project root. If a tool defaults to the current working directory, you must override it using output flags (e.g., `pdflatex -output-directory=manuscript manuscript/manuscript.tex`).

---

## Core Agents

| Name                  | Description                                                                                                                                                                                                            | Invocation Method                                         |
| :-------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------- |
| Gemini CLI (Main)     | The primary interactive CLI agent for software engineering tasks.                                                                                                                                                        | Direct interaction                                        |
| codebase_investigator | Specialized for codebase analysis, architectural mapping, and understanding system-wide dependencies. Use for vague requests, bug root-cause analysis, system refactoring, comprehensive feature implementation.       | `call:codebase_investigator(objective="...")`             |
| cli_help              | Specialized in answering questions about how users use the Gemini CLI, its features, documentation, and current runtime configuration.                                                                                     | `call:cli_help(question="...")`                           |
| generalist            | A general-purpose AI agent with access to all tools. Recommended for turn-intensive tasks or processing large data, batch refactoring, high-volume output commands, and speculative investigations.                      | `call:generalist(request="...")`                          |

## External AI Tools

| Name                  | Description                                            | Invocation Method                                  | Prerequisites                                               |
| :-------------------- | :----------------------------------------------------- | :------------------------------------------------- | :---------------------------------------------------------- |
| GitHub Copilot CLI    | Primary agent for coding, shell tasks, and planning. Supports high-fidelity reasoning/verification. Models can be swapped (e.g., `--model gpt-4o`). | `copilot -p "..."` (non-interactive) or `copilot` (interactive) | GitHub Copilot CLI installed (`copilot --version`). |
| Aider                 | AI pair programming tool that edits your code files directly. Uses models like Google Gemini. | `aider <command-line options> [files_or_dirs...] [file_path]` | Python installed, Google Gemini API Key set as `OPENAI_API_KEY` environment variable. |
| arXiv API             | The gold standard for Math, Physics, and Economics preprints. Use `arxiv.py` for author or keyword searches. | `import arxiv` in Python scripts | Python `arxiv` library installed. |
| OpenAlex API          | Powerful way to pull metadata, citations, and full-text links for millions of published works. | REST API via `requests` | Internet access. |
| Semantic Scholar API  | Uses AI to identify highly influential citations and provides metadata for millions of papers. | REST API via `requests` | Internet access. |

---

# Copilot CLI Guide

The GitHub Copilot CLI (`copilot`) is the primary tool for high-fidelity reasoning, code verification, and mathematical audits.

### Basic Syntax
- **Interactive Mode:** `copilot` (starts a chat session)
- **Non-Interactive Prompt:** `copilot -p "Your question here"`
- **Quiet Mode:** `copilot -p "..." --silent` (useful for scripting and extraction)

### Model Selection
You can override the default model (Claude 3 Haiku) by using the `--model` flag to access superior reasoning:
- **GPT-4o:** `copilot -p "..." --model gpt-4o`
- **Claude 3.5 Sonnet:** `copilot -p "..." --model sonnet-3.5`

### High-Fidelity Verification Workflow
When a mathematical or architectural decision is critical, always cross-verify with Copilot using the following pattern:
1. State the **Physical/Theoretical Context**.
2. State the **Mathematical Equation** or logic.
3. Ask for a **Soundness Check** on signs, priors, or convergence risks.
4. Pass `--silent` to capture the raw response for the session log.

