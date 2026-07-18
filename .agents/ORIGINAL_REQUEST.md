# Original User Request

## 2026-07-16T09:28:34Z

# Teamwork Project Prompt — Draft

> Status: Launched

A multi-agent academic writing pipeline that parses `bibliography.bib` to download all cited papers using APIs (OpenAlex/arXiv), critically reviews `manuscript/manuscript.tex` for logical rigor, and autonomously writes the final LaTeX draft for a weekend submission.

Working directory: C:/Users/jules/OneDrive - The University of Manchester/Internships/projects/energy/paper 5
Integrity mode: development

## Requirements

### R1. Download Cited Papers
Parse the `manuscript/bibliography.bib` file and write a Python script using the OpenAlex or arXiv APIs to automatically download the full-text PDFs of all open-access cited papers into the `papers/` directory.

### R2. Adversarial Manuscript Review
Critically review `manuscript/manuscript.tex` for logical gaps, mathematical inconsistencies, and alignment with the newly downloaded literature. Write all suggested edits, line-by-line, to a new file called `manuscript/review_notes.md`. Do not modify the original `.tex` file.

## Acceptance Criteria

### Bibliography & PDF Downloads
- [ ] A Python script successfully parses the `.bib` file.
- [ ] New PDF files corresponding to citation keys are present in the `papers/` directory.

### Manuscript Review
- [ ] `manuscript/review_notes.md` is created.
- [ ] The review notes contain explicit references to specific line numbers or sections in `manuscript.tex`.
- [ ] The review notes reference findings from at least one of the newly downloaded PDFs.
