# Strategy for Anonymised NEED and Restricted Data Access

This document details the sample size representation in the open Anonymised NEED dataset and outlines the access process, timeframes, and costs associated with acquiring the restricted full NEED and SERL datasets.

## 1. Anonymised NEED (Open Data)
- **Representativeness:** The 4 million row Anonymised NEED dataset represents roughly a 14% to 15% random sample of the domestic properties in England. It is designed by DESNZ to be highly representative at the Local Authority District (LAD) level.
- **Samples per LAD:** England has 309 Local Authority Districts. A 4 million property sample distributed across these LADs yields an average of approximately **12,000 households per LAD**. Even the smallest districts (e.g., City of London, Isles of Scilly, or small rural councils) will typically have thousands of samples. This is an extremely robust sample size for generating marginal distributions and training a stratified expansion model at the LAD level.

## 2. Full NEED via ONS Secure Research Service (Restricted)
- **Timeframe:** **Slow (3 to 6 months).** The process involves several sequential steps: obtaining Accredited Researcher (AR) status, submitting a project application to the Research Accreditation Service (RAS), undergoing review by the data owner (DESNZ), and finally, environment setup.
- **Gatekeepers:** 
    - You must become an **ONS Accredited Researcher**, which requires passing a Safe Researcher Training course and exam.
    - Your project must pass the **Research Accreditation Panel (RAP)**, proving it serves the "public good" and is scientifically sound.
    - **Statistical Disclosure Control (SDC):** You cannot download the raw data. You access it via a remote secure terminal (VDI). Any results (graphs, regression tables) must be manually reviewed and approved by ONS staff before they can be released from the secure environment.
- **Moneywise:** Access to the ONS SRS is generally **free** for academic researchers and public sector organizations conducting non-commercial research for the public good.

## 3. Bonus: SERL Data via UK Data Service Secure Lab (Restricted)
- **Timeframe:** **Slow (2 to 4 months).** Similar to the ONS SRS, this requires obtaining Safe Researcher status and submitting a detailed project application.
- **Gatekeepers:**
    - You must be a UK-based academic researcher (or have a specific eligible affiliation).
    - You need **UKDS Safe Researcher Training (SRT)**.
    - Your project is reviewed by the **SERL Data Governance Board (PRB)**. You must explicitly justify why half-hourly smart meter data is strictly necessary for your research.
    - Like the ONS SRS, access is via a secure remote desktop, and all outputs undergo **Statistical Disclosure Control (SDC)** before release.
- **Moneywise:** Access is **free** for UK academics conducting non-commercial research.

## Recommendation for Paper 5
Given the 3-6 month lead times and strict output controls associated with restricted data (Options 2 and 3), relying on the **Anonymised NEED (4 million row) dataset** is highly recommended for maintaining project momentum. The ~12,000 samples per LAD provide more than enough statistical power for the stratified expansion, allowing you to bypass gatekeepers entirely while still producing highly valid, granular spatial estimates.
