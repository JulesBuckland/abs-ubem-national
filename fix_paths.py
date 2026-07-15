import os

replacements = {
    "tests/test_e2e_pipeline.py": [
        ("scripts.01_population_synthesis", "src.data.population"),
        ("scripts.00c_gp_emulator", "src.inference.gp_emulator"),
        ("scripts.02a_bayesian_model_unified", "src.inference.model_unified")
    ],
    "tests/test_e2e_integration.py": [
        ("Path(\"scripts/run_pipeline.py\")", "Path(\"main.py\")")
    ],
    "tests/integration/test_gp.py": [
        ("scripts/10c_gp_emulator.py", "src/inference/gp_emulator.py"),
        ("scripts/10d_integration_test.py", "tests/integration/test_gp.py")
    ],
    "src/utils/apply_smoothing.py": [
        ("'scripts/04_generate_visuals.py'", "'src/visualization/visuals_generator.py'")
    ],
    "src/utils/revert_visuals.py": [
        ("'scripts/04_generate_visuals.py'", "'src/visualization/visuals_generator.py'")
    ],
    "src/utils/monitor.py": [
        ("\"python scripts/04_eti_generation.py\"", "\"python -m src.analysis.eti\""),
        ("\"python scripts/04_generate_visuals.py\"", "\"python -m src.visualization.visuals_generator\"")
    ],
    "src/validation/boundary_checks.py": [
        ("\"scripts/03_bayesian_icar_model.py\"", "\"src/inference/abs_ubem_model.py\"")
    ],
    "src/inference/gp_emulator.py": [
        ("scripts/10c_gp_emulator.py", "src/inference/gp_emulator.py")
    ]
}

for file_path, reps in replacements.items():
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        for old, new in reps:
            content = content.replace(old, new)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {file_path}")
    else:
        print(f"File not found: {file_path}")
