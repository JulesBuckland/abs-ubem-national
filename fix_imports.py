import os

target_files = [
    "src/inference/calibration.py",
    "src/inference/lhs_sampler.py",
    "src/inference/pilot_global.py",
    "src/utils/pull_weather_data.py",
    "src/utils/rebuild_confounders.py",
    "src/validation/boundary_checks.py",
    "src/validation/external.py",
    "src/validation/external_checks.py",
    "src/validation/prior_sensitivity.py",
    "tests/inference/test_nuts.py"
]

replacements = [
    ("from config import", "from src.config.settings import"),
    ("from scripts.config import", "from src.config.settings import")
]

for file_path in target_files:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        for old, new in replacements:
            content = content.replace(old, new)
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {file_path}")
    else:
        print(f"File not found: {file_path}")
