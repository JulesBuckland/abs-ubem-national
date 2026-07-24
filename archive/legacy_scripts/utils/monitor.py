import time
import subprocess
import os
import logging
from pathlib import Path

def monitor_log(log_path, success_marker="Success!"):
    print(f"Monitoring {log_path} for '{success_marker}'...")
    while True:
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                content = f.read()
                if success_marker in content:
                    print("Success marker found!")
                    return True
                # Also check if process is still running if possible, 
                # but reading the log is the primary task.
        time.sleep(30)

def run_command(command, cwd=None):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        return False
    return True

if __name__ == "__main__":
    log_file = "logs/bayesian_turbo_run.log"
    
    if monitor_log(log_file):
        print("Starting downstream tasks...")
        
        if not run_command("python -m src.analysis.eti"):
            exit(1)
        
        if not run_command("python -m src.visualization.visuals_generator"):
            exit(1)
            
        print("Running LaTeX cycle...")
        latex_commands = [
            "pdflatex -interaction=nonstopmode manuscript.tex",
            "bibtex manuscript",
            "pdflatex -interaction=nonstopmode manuscript.tex",
            "pdflatex -interaction=nonstopmode manuscript.tex"
        ]
        
        manuscript_dir = Path("manuscript")
        for cmd in latex_commands:
            if not run_command(cmd, cwd=manuscript_dir):
                print(f"LaTeX step failed: {cmd}")
                # We might continue anyway if it's just a non-fatal error
        
        print("All downstream tasks completed.")
