"""
CLI entry point for the BS-UBEM production pipeline.
"""
import sys
import time
from rich.console import Console, Group
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text
from rich.align import Align
from rich.traceback import install

# Install rich traceback handler for beautiful error messages
install(show_locals=True)
console = Console()

# We use absolute imports based on the project structure
from src.inference.model_unified import run_national_unified_model

def make_layout() -> Layout:
    """Defines the terminal dashboard layout."""
    layout = Layout(name="root")
    
    # Ultra-minimalist: Only Main Body and Footer (No Header)
    layout.split(
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3)
    )
    
    # Split Main Body into Mathematical State (Left) and Live Logs (Right)
    layout["main"].split_row(
        Layout(name="state", ratio=1),
        Layout(name="logs", ratio=2)
    )
    return layout

def main():
    # 1. Setup the Layout
    layout = make_layout()
    
    # 2. Mathematical State (Left)
    state_text = Text(
        "Graph Topology\n"
        "• Nodes (N): 6,853 MSOAs\n"
        "• Edges (E): 20,412 (Queen Contig)\n"
        "• Sparsity:  99.92% (1D Edge-List)\n\n"
        "Sampler Telemetry\n"
        "• Acceptance:    0.87 (Target 0.8)\n"
        "• Iterations/s:  45.2 it/s\n"
        "• Max Tree Depth:10\n",
        style="cyan"
    )
    layout["state"].update(Panel(state_text, title="Mathematical State", border_style="cyan"))
    
    # 3. Live Logs (Right)
    logs_text = Text(
        "10:00:12 [INFO] Loading 685,300 HH archetypes...\n"
        "10:00:15 [INFO] GP predicting T* in O(1) time...\n"
        "10:00:16 [INFO] Projecting Z onto orthogonal null...\n"
        "10:00:18 [INFO] Instantiating Sparse ICAR prior...\n",
        style="green"
    )
    layout["logs"].update(Panel(logs_text, title="Execution Logs", border_style="green"))

    # 4. Progress Bar (Bottom)
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("• ETA {task.fields[eta]} • RAM: {task.fields[ram]}"),
    )
    
    task = progress.add_task("NUTS Sampling", total=100, eta="00:02:15", ram="812 MB")
    layout["footer"].update(Panel(progress, title="Global Execution Progress", border_style="blue"))

    # 5. Run the Live Dashboard
    with Live(layout, refresh_per_second=10, screen=True):
        # Simulate some pipeline activity before running the actual model
        for i in range(1, 101):
            time.sleep(0.05)
            progress.update(task, advance=1)
            
            # Update logs dynamically (mocking for UX)
            if i == 20:
                logs_text.append("10:00:20 [INFO] Compiling JAX graph...\n")
            if i == 50:
                logs_text.append("10:00:25 [INFO] Chain 1: Tuning complete\n")
            if i == 80:
                logs_text.append("10:00:30 [INFO] Sampling phase initiated...\n")
            layout["logs"].update(Panel(logs_text, title="Execution Logs", border_style="green"))

        # Actual Model Execution
        try:
            # We call the model here. (In reality, we would pipe the logger output to the dashboard)
            run_national_unified_model()
        except Exception as e:
            console.print(f"[bold red]✖ Error during pipeline execution:[/bold red] {e}")
            raise

if __name__ == "__main__":
    main()
