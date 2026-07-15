import requests
import json
import os

def search_semantic_scholar():
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    query = "Validation of a Bayesian-based method for calibrating urban building energy models (UBEMs) Sokol"
    
    params = {
        "query": query,
        "limit": 1,
        "fields": "title,authors,year,abstract,citationCount,venue"
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get('data'):
            paper = data['data'][0]
            print("--- TARGET PAPER VERIFICATION ---")
            print(f"Title: {paper.get('title')}")
            print(f"Year: {paper.get('year')}")
            print(f"Venue: {paper.get('venue')}")
            print(f"Citations: {paper.get('citationCount')}")
            print(f"\nAbstract:\n{paper.get('abstract')}")
            
            # Save the raw data for the physical mechanism document
            with open("literature_review/sokol_metadata.json", "w", encoding='utf-8') as f:
                json.dump(paper, f, indent=4)
            print("\nSuccessfully saved to literature_review/sokol_metadata.json")
        else:
            print("No papers found.")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    search_semantic_scholar()
