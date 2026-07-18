## 2026-07-16T09:32:39Z

Your identity is teamwork_preview_worker.
Your working directory is: C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\.agents\worker_download_papers

Your objective is to parse C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\manuscript\bibliography.bib and download the open-access PDF files of all cited papers into C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\papers.

Task details:
1. Write a Python script to parse the bibliography.bib file. You can use standard Python regex or a simple bibtex parser.
2. For each bibliography entry:
   - Extract the citation key (e.g., Grey2017, Booth2013).
   - Extract the DOI if present.
   - Extract the title.
3. For entries with a DOI, query the OpenAlex API: `https://api.openalex.org/works/https://doi.org/{doi}` or `https://api.openalex.org/works?filter=doi:https://doi.org/{doi}`.
4. For entries without a DOI, query the OpenAlex API searching by title: `https://api.openalex.org/works?search={title}`.
5. In the response, look for `best_oa_location` or `primary_location` that has a `pdf_url` (meaning it's open access and has a downloadable PDF link). If not found, you can also search the arXiv API.
6. Download the PDF from the `pdf_url` and save it to the `papers/` directory as `<CitationKey>.pdf` (e.g., `Grey2017.pdf`).
7. Make sure the script handles rate limits, network timeouts, and missing fields gracefully.
8. If some PDFs cannot be downloaded because they are not open access or because they are books, log the reason and skip them.
9. Verify that the files are downloaded and check their integrity (e.g. check that the downloaded files are valid PDFs).
10. Write the Python script to C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\src\utils\download_cited_papers.py and run it.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

When done, report the files downloaded, their sizes, and any errors encountered in a handoff.md file in your working directory.
