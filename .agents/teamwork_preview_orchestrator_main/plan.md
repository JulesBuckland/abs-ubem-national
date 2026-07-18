# Project Plan — Multi-Agent Academic Paper Tooling

This plan outlines the steps required to execute the requirements in `ORIGINAL_REQUEST.md`.

## Milestone 1: Environment & File Check [COMPLETE]
- [x] Create and initialize `plan.md`, `progress.md`, and `context.md` in working directory.
- [x] Create/update `tasks/todo.md` with checkable plan items.
- [x] Create/update `PROJECT.md` in project root with global project index and layout.
- [x] Initialize `BRIEFING.md` in working directory.
- [x] Set up liveness check heartbeat cron.

## Milestone 2: R1 - PDF Downloader Script & Execution [PENDING]
- [ ] Research availability of bibtex parsing and API libraries (urllib/requests, OpenAlex/arXiv).
- [ ] Spawn teamwork_preview_worker to write and run Python script to parse bibliography.bib and download open-access PDFs into `papers/`.
- [ ] Run the downloader script.
- [ ] Verify that PDFs are successfully downloaded to `papers/` and match citation keys in bibliography.bib.

## Milestone 3: R2 - Adversarial Manuscript Review [PENDING]
- [ ] Spawn teamwork_preview_reviewer/critic to review manuscript/manuscript.tex.
- [ ] Analyze downloaded PDFs and cross-reference with manuscript text to find logical gaps, inconsistencies, and alignment issues.
- [ ] Write suggested edits and review notes line-by-line to `manuscript/review_notes.md`.
- [ ] Ensure review notes contain explicit line numbers/sections and reference findings from at least one downloaded PDF.

## Milestone 4: Verification & Completion [PENDING]
- [ ] Perform Quadruple-Backverification (4BV) on code, output, manuscript, and metadata.
- [ ] Run Forensic Auditor tool to verify code integrity and check for any compliance violations.
- [ ] Compile LaTeX (if needed, but without modifying manuscript.tex).
- [ ] Report final completion results to user.
