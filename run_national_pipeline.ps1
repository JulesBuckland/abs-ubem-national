$ErrorActionPreference = "Stop"
Write-Host "Starting full national population synthesis..."
.\.venv\Scripts\python -m src.data.population

Write-Host "Training full GP Emulator..."
.\.venv\Scripts\python -m src.inference.gp_emulator

Write-Host "Running National Unified Bayesian Model..."
.\.venv\Scripts\python -m src.inference.model_unified

Write-Host "National run complete."
