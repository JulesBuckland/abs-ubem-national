import urllib.request
import json
import urllib.parse
import time

def search(query, limit=5):
    url = "https://api.semanticscholar.org/graph/v1/paper/search?query=" + urllib.parse.quote(query) + "&limit=" + str(limit) + "&fields=title,authors,year,abstract,citationCount,venue,url"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('data', [])
    except Exception as e:
        print(f"Error fetching {query}: {e}")
    return []

queries = [
    "UBEM surrogate model",
    "urban building energy bayesian calibration",
    "building energy spatial bayesian",
    "differentiable surrogate building"
]

results = {}
for q in queries:
    print(f"Querying: {q}")
    papers = search(q)
    for p in papers:
        if p['paperId'] not in results:
            results[p['paperId']] = p
    time.sleep(1.5) # Sleep to avoid 429

print(f"Total unique papers found: {len(results)}")
for p in list(results.values())[:10]:
    abs_text = p.get('abstract') or ""
    print(f"- {p.get('title')} ({p.get('year')}). Citations: {p.get('citationCount')}")
    print(f"  {p.get('url')}")
    print(f"  Abstract: {abs_text[:200]}...")
