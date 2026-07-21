import requests
import json
import urllib.parse

titles = [
    "Validation of a Bayesian-based method for defining residential archetypes in urban building energy models",
    "Bayesian calibration at the urban scale: a case study on a large residential heating demand application in Amsterdam",
    "Hierarchical calibration of archetypes for urban building energy modeling",
    "Influence of data acquisition on the Bayesian calibration of urban building energy models",
    "Reducing Uncertainty of Building Shape Information in Urban Building Energy Modeling using Bayesian Calibration"
]

for title in titles:
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(title)}"
        res = requests.get(url).json()
        if res.get("results"):
            print(f"Found: {res['results'][0]['title']}")
    except Exception as e:
        print(f"Error searching {title}: {e}")
