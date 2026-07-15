import urllib.request
import os

url = 'https://www.nomisweb.co.uk/output/census/2021/census2021-rm045.zip'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
req = urllib.request.Request(url, headers=headers)

try:
    print(f"Starting download from {url}...")
    with urllib.request.urlopen(req) as response:
        content = response.read()
        with open('data/raw/census/census2021-rm045_full.zip', 'wb') as f:
            f.write(content)
    print(f"Downloaded {len(content)} bytes to data/raw/census/census2021-rm045_full.zip")
except Exception as e:
    print(f"Error: {e}")
