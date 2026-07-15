"""
CLI entry point for the ABS-UBEM production pipeline.
"""

import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.traceback import install

# Install rich traceback handler for beautiful error messages
install(show_locals=True)

console = Console()

# We use absolute imports based on the project structure
from src.inference.model_unified import run_national_unified_model

def main():
    console.print(Panel.fit("[bold blue]ABS-UBEM Production Runner[/bold blue]\n[green]National Spatial Graph Interface[/green]", border_style="blue"))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Initializing Bayesian Inference Pipeline...", total=None)
        time.sleep(1)  # Brief pause for UX
        
    try:
        # Execute the main unified model
        run_national_unified_model()
        console.print("[bold green]✔[/bold green] Pipeline executed successfully.")
    except Exception as e:
        console.print(f"[bold red]✖ Error during pipeline execution:[/bold red] {e}")
        raise

if __name__ == "__main__":
    main()
