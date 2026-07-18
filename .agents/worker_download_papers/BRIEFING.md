# BRIEFING — 2026-07-16T10:39:00+01:00

## Mission
Parse bibliography.bib, query OpenAlex and arXiv APIs, download open-access PDF files of all cited papers into papers/, and verify their integrity.

## 🔒 My Identity
- Archetype: teamwork_preview_worker
- Roles: implementer, qa, specialist
- Working directory: C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\.agents\worker_download_papers
- Original parent: e50891bf-90a2-47e7-8ca1-b87dd813a845
- Milestone: download_cited_papers

## 🔒 Key Constraints
- CODE_ONLY network mode: Do NOT use curl, wget, lynx or HTTP client targeting external URLs via run_command.
- Zero Trust Policy: Assumed malfeasance. Quadruple-Backverification (4BV) required.
- Do not modify files without re-reading first. Minimal changes.
- All code files to be written in src/utils/download_cited_papers.py.
- Log failures, check PDF integrity.

## Current Parent
- Conversation ID: e50891bf-90a2-47e7-8ca1-b87dd813a845
- Updated: 2026-07-16T10:39:00+01:00

## Task Summary
- **What to build**: A Python utility script in `src/utils/download_cited_papers.py` that parses `manuscript/bibliography.bib`, queries OpenAlex/arXiv APIs for open-access PDF URLs, downloads them to `papers/` named by CitationKey, and verifies PDF integrity.
- **Success criteria**: Cited open-access PDFs downloaded and verified as valid PDFs; logs show status of each paper; `handoff.md` lists downloaded papers with sizes and status.
- **Interface contracts**: Input `manuscript/bibliography.bib`, output PDF files in `papers/`.
- **Code layout**: Source in `src/utils/download_cited_papers.py`.

## Key Decisions Made
- Used standard Python requests and custom robust bibtex regex parser to parse bib entries.
- Downloaded OpenAccess PDFs using title/DOI filters with Polite OpenAlex User-Agent, fallback to arXiv.
- Inspected the PDF files to guarantee they start with `%PDF` header before saving them.

## Artifact Index
- `src/utils/download_cited_papers.py` — The PDF downloader utility script.
- `.agents/worker_download_papers/download_report.json` — Detailed JSON log of all 42 entries.
- `.agents/worker_download_papers/handoff.md` — Final handoff report.

## Change Tracker
- **Files modified**: `src/utils/download_cited_papers.py` (added), `.agents/worker_download_papers/progress.md` (updated), `.agents/worker_download_papers/handoff.md` (added), `.agents/worker_download_papers/download_report.json` (added)
- **Build status**: Pass
- **Pending issues**: None

## Quality Status
- **Build/test result**: Pass
- **Lint status**: Pass
- **Tests added/modified**: Checked files manually and run python checks for `%PDF` headers.

## Loaded Skills
- None
