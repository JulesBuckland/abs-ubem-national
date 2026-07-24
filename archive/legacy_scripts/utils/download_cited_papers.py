import os
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
import requests

# Set directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BIB_PATH = os.path.join(BASE_DIR, 'manuscript', 'bibliography.bib')
PAPERS_DIR = os.path.join(BASE_DIR, 'papers')

# Create papers directory if not exists
os.makedirs(PAPERS_DIR, exist_ok=True)

# User agents
POLITE_USER_AGENT = "mailto:jules.buckland@postgrad.manchester.ac.uk"
BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def parse_bib_file(file_path):
    """
    Parses a bibliography.bib file.
    Returns a list of dicts: [{'key': citation_key, 'type': entry_type, 'doi': doi, 'title': title, 'journal': journal, 'url': url}]
    """
    if not os.path.exists(file_path):
        print(f"Error: Bibliography file not found at {file_path}")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split entries by '@'
    chunks = content.split('@')
    entries = []

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # Find first brace
        first_brace = chunk.find('{')
        if first_brace == -1:
            continue

        entry_type = chunk[:first_brace].strip().lower()
        rest = chunk[first_brace+1:]

        # Find citation key
        first_comma = rest.find(',')
        if first_comma == -1:
            continue

        citation_key = rest[:first_comma].strip()

        # Helper to extract a field using matching braces/quotes
        def extract_field(field_name):
            pattern = rf'\b{field_name}\s*=\s*'
            match = re.search(pattern, rest, re.IGNORECASE)
            if not match:
                return None
            start_pos = match.end()
            if start_pos >= len(rest):
                return None
            char = rest[start_pos]
            if char == '{':
                brace_count = 1
                val_chars = []
                for i in range(start_pos + 1, len(rest)):
                    c = rest[i]
                    if c == '{':
                        brace_count += 1
                    elif c == '}':
                        brace_count -= 1
                    if brace_count == 0:
                        break
                    val_chars.append(c)
                return "".join(val_chars).strip()
            elif char == '"':
                val_chars = []
                for i in range(start_pos + 1, len(rest)):
                    c = rest[i]
                    if c == '"':
                        if i > 0 and rest[i-1] != '\\':
                            break
                    val_chars.append(c)
                return "".join(val_chars).strip()
            else:
                val_chars = []
                for i in range(start_pos, len(rest)):
                    c = rest[i]
                    if c in (',', '\n', '}'):
                        break
                    val_chars.append(c)
                return "".join(val_chars).strip()

        doi = extract_field('doi')
        title = extract_field('title')
        journal = extract_field('journal')
        url = extract_field('url')
        publisher = extract_field('publisher')

        # Clean title braces
        if title:
            title = re.sub(r'[\{\}]', '', title)
            title = " ".join(title.split())

        entries.append({
            'key': citation_key,
            'type': entry_type,
            'doi': doi,
            'title': title,
            'journal': journal,
            'url': url,
            'publisher': publisher
        })

    return entries

def clean_title(title):
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r'[^a-z0-9\s]', '', title)
    return " ".join(title.split())

def titles_match(title1, title2, threshold=0.85):
    t1 = clean_title(title1)
    t2 = clean_title(title2)
    if not t1 or not t2:
        return False
    words1 = set(t1.split())
    words2 = set(t2.split())
    if not words1 or not words2:
        return False
    intersection = words1.intersection(words2)
    overlap = len(intersection) / max(len(words1), len(words2))
    words_q = set(t1.split())
    overlap_q = len(intersection) / len(words_q)
    return overlap >= threshold or overlap_q >= 0.90

def make_request(url, params=None, headers=None, max_retries=3):
    current_headers = {"User-Agent": POLITE_USER_AGENT}
    if headers:
        current_headers.update(headers)

    backoff = 1.0
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=current_headers, timeout=15)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                print(f"Rate limit (429) hit. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2
            else:
                print(f"HTTP error {response.status_code} for URL: {url}")
                return response
        except requests.exceptions.RequestException as e:
            print(f"Request error (attempt {attempt+1}/{max_retries}): {e}")
            time.sleep(backoff)
            backoff *= 2
    return None

def extract_pdf_url_from_work(work):
    if not work or not isinstance(work, dict):
        return None
    # Check best_oa_location
    best_oa = work.get('best_oa_location')
    if best_oa and isinstance(best_oa, dict):
        url = best_oa.get('pdf_url')
        if url:
            return url
    # Check primary_location
    prim = work.get('primary_location')
    if prim and isinstance(prim, dict):
        url = prim.get('pdf_url')
        if url:
            return url
    # Check other locations
    locations = work.get('locations', [])
    if locations:
        for loc in locations:
            if isinstance(loc, dict):
                url = loc.get('pdf_url')
                if url:
                    return url
    return None

def search_openalex_by_doi(doi):
    print(f"Querying OpenAlex by DOI: {doi}")
    # Try direct work API
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    res = make_request(url)
    if res and res.status_code == 200:
        try:
            work = res.json()
            pdf_url = extract_pdf_url_from_work(work)
            if pdf_url:
                return pdf_url
        except Exception as e:
            print(f"Error parsing JSON from DOI direct query: {e}")

    # Try filtering works API
    url_filter = "https://api.openalex.org/works"
    params = {"filter": f"doi:https://doi.org/{doi}"}
    res = make_request(url_filter, params=params)
    if res and res.status_code == 200:
        try:
            data = res.json()
            results = data.get('results', [])
            if results:
                pdf_url = extract_pdf_url_from_work(results[0])
                if pdf_url:
                    return pdf_url
        except Exception as e:
            print(f"Error parsing JSON from DOI filter query: {e}")

    return None

def search_openalex_by_title(title):
    print(f"Querying OpenAlex by title: {title}")
    url = "https://api.openalex.org/works"
    params = {"search": title}
    res = make_request(url, params=params)
    if res and res.status_code == 200:
        try:
            data = res.json()
            results = data.get('results', [])
            for work in results:
                work_title = work.get('title')
                if titles_match(title, work_title):
                    pdf_url = extract_pdf_url_from_work(work)
                    if pdf_url:
                        print(f"Matched title on OpenAlex: {work_title}")
                        return pdf_url
        except Exception as e:
            print(f"Error parsing JSON from title search: {e}")
    return None

def search_arxiv_by_title(title):
    print(f"Querying arXiv by title: {title}")
    query_title = urllib.parse.quote(f'ti:"{title}"')
    url = f"http://export.arxiv.org/api/query?search_query={query_title}&max_results=3"
    res = make_request(url)
    if res and res.status_code == 200:
        try:
            root = ET.fromstring(res.content)
            # Find entries
            namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', namespaces)
            for entry in entries:
                entry_title = entry.find('atom:title', namespaces)
                entry_title_text = entry_title.text if entry_title is not None else ""
                if titles_match(title, entry_title_text):
                    # Find link with type="application/pdf"
                    links = entry.findall('atom:link', namespaces)
                    for link in links:
                        rel = link.attrib.get('rel')
                        title_attr = link.attrib.get('title')
                        link_type = link.attrib.get('type')
                        href = link.attrib.get('href')
                        if href and (link_type == 'application/pdf' or title_attr == 'pdf' or 'pdf' in href):
                            # Arxiv links might be http, make them https
                            if href.startswith('http://'):
                                href = 'https://' + href[7:]
                            # Arxiv PDF URL could be check-based
                            if '/abs/' in href:
                                href = href.replace('/abs/', '/pdf/')
                            if not href.endswith('.pdf') and '/pdf/' in href:
                                href = href + '.pdf'
                            print(f"Matched title on arXiv: {entry_title_text}")
                            return href
        except Exception as e:
            print(f"Error parsing arXiv XML: {e}")
    return None

def verify_pdf(file_path):
    if not os.path.exists(file_path):
        return False
    size = os.path.getsize(file_path)
    if size < 1024:
        return False
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header == b'%PDF':
                return True
    except Exception as e:
        print(f"Error verifying PDF file header: {e}")
    return False

def download_pdf(pdf_url, output_path):
    print(f"Downloading {pdf_url} -> {output_path}")
    headers = {"User-Agent": BROWSER_USER_AGENT}
    try:
        response = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            if verify_pdf(output_path):
                return True
            else:
                print(f"Integrity check failed: {output_path} is not a valid PDF or is too small.")
                if os.path.exists(output_path):
                    os.remove(output_path)
                return False
        else:
            print(f"Failed to download PDF. Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

def process_entry(entry):
    key = entry['key']
    entry_type = entry['type']
    doi = entry['doi']
    title = entry['title']
    journal = entry['journal']
    publisher = entry['publisher']

    print("\n" + "="*50)
    print(f"Processing citation: {key} ({entry_type.upper()})")
    print(f"Title: {title}")

    # Output path
    output_path = os.path.join(PAPERS_DIR, f"{key}.pdf")

    # Skip if already exists and is valid
    if verify_pdf(output_path):
        size = os.path.getsize(output_path)
        print(f"Valid PDF already exists: {output_path} ({size} bytes). Skipping download.")
        return {'key': key, 'status': 'Already Downloaded', 'size': size, 'error': None}

    # 1. Skip if Book
    if entry_type == 'book':
        print("Skipped: Book entry.")
        return {'key': key, 'status': 'Skipped', 'size': 0, 'error': 'Is a book'}

    # 2. Extract from arXiv ID if mentioned in journal
    arxiv_id_match = None
    if journal:
        match = re.search(r'(?:arxiv[:/]|arxiv\.org/abs/|arxiv\.org/pdf/)(\d{4}\.\d{4,5}(?:v\d+)?)', journal, re.IGNORECASE)
        if match:
            arxiv_id_match = match.group(1)

    if arxiv_id_match:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id_match}.pdf"
        print(f"Found arXiv ID in journal: {arxiv_id_match}. PDF URL: {pdf_url}")
        if download_pdf(pdf_url, output_path):
            return {'key': key, 'status': 'Downloaded', 'size': os.path.getsize(output_path), 'error': None}

    # 3. DOI search
    if doi:
        pdf_url = search_openalex_by_doi(doi)
        if pdf_url:
            if download_pdf(pdf_url, output_path):
                return {'key': key, 'status': 'Downloaded', 'size': os.path.getsize(output_path), 'error': None}

    # 4. Title search on OpenAlex
    if title:
        pdf_url = search_openalex_by_title(title)
        if pdf_url:
            if download_pdf(pdf_url, output_path):
                return {'key': key, 'status': 'Downloaded', 'size': os.path.getsize(output_path), 'error': None}

    # 5. Title search on arXiv
    if title:
        pdf_url = search_arxiv_by_title(title)
        if pdf_url:
            if download_pdf(pdf_url, output_path):
                return {'key': key, 'status': 'Downloaded', 'size': os.path.getsize(output_path), 'error': None}

    # 6. Fallback if URL is directly in the entry
    direct_url = entry['url']
    if direct_url:
        print(f"Attempting direct download from URL field: {direct_url}")
        # If it's a PDF link or we try downloading it
        if direct_url.lower().endswith('.pdf'):
            if download_pdf(direct_url, output_path):
                return {'key': key, 'status': 'Downloaded', 'size': os.path.getsize(output_path), 'error': None}
        else:
            print("Direct URL does not end with .pdf, skipped.")

    # All failed
    reason = "No open-access PDF URL found or download failed"
    print(f"Could not download {key}: {reason}")
    return {'key': key, 'status': 'Failed', 'size': 0, 'error': reason}

def main():
    print(f"Parsing bibliography: {BIB_PATH}")
    entries = parse_bib_file(BIB_PATH)
    print(f"Found {len(entries)} bibliography entries.")

    results = []
    for entry in entries:
        res = process_entry(entry)
        results.append(res)
        # Sleep to respect rate limits
        time.sleep(0.5)

    print("\n" + "="*50)
    print("DOWNLOAD SUMMARY")
    print("="*50)
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    for res in results:
        status = res['status']
        key = res['key']
        size = res['size']
        err = res['error']
        
        if status in ('Downloaded', 'Already Downloaded'):
            downloaded_count += 1
            print(f"[{status}] {key}: {size} bytes")
        elif status == 'Skipped':
            skipped_count += 1
            print(f"[Skipped] {key}: {err}")
        else:
            failed_count += 1
            print(f"[Failed] {key}: {err}")

    print(f"\nTotal: {len(results)} | Downloaded/Existing: {downloaded_count} | Skipped: {skipped_count} | Failed: {failed_count}")

    # Write summary to a JSON file in worker directory for easy report parsing
    report_path = os.path.join(BASE_DIR, '.agents', 'worker_download_papers', 'download_report.json')
    import json
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
    print(f"Report written to {report_path}")

if __name__ == "__main__":
    main()
