import os
import requests
import urllib.parse
import json

def download_pdfs():
    output_dir = os.path.join('docs', 'pdfs')
    os.makedirs(output_dir, exist_ok=True)
    
    papers = [
        "Validation of a Bayesian-based method for defining residential archetypes in urban building energy models",
        "Bayesian calibration at the urban scale: a case study on a large residential heating demand application in Amsterdam",
        "Hierarchical calibration of archetypes for urban building energy modeling",
        "Influence of data acquisition on the Bayesian calibration of urban building energy models",
        "Reducing Uncertainty of Building Shape Information in Urban Building Energy Modeling using Bayesian Calibration"
    ]
    
    for title in papers:
        print(f"Searching for: {title}")
        safe_title = "".join(c if c.isalnum() else "_" for c in title)[:50]
        file_path = os.path.join(output_dir, f"{safe_title}.pdf")
        
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(title)}&limit=1&fields=title,openAccessPdf"
            res = requests.get(url)
            data = res.json()
            if data.get('data') and len(data['data']) > 0:
                paper = data['data'][0]
                oa_info = paper.get('openAccessPdf')
                if oa_info and oa_info.get('url'):
                    pdf_url = oa_info['url']
                    print(f"Found OA PDF: {pdf_url}")
                    pdf_response = requests.get(pdf_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
                    if pdf_response.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in pdf_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"Downloaded to {file_path}")
                        continue
                    else:
                        print(f"Failed to download. Status: {pdf_response.status_code}")
                else:
                    print("No Open Access PDF found via Semantic Scholar.")
            else:
                print("Paper not found on Semantic Scholar.")
        except Exception as e:
            print(f"Semantic Scholar error: {e}")
        
        print("-" * 40)

if __name__ == '__main__':
    download_pdfs()
