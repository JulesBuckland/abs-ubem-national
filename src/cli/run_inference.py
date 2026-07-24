"""
CLI entry point for the BS-UBEM production pipeline.
"""
from rich.console import Console
from rich.traceback import install

# Install rich traceback handler for beautiful error messages
install(show_locals=True)
console = Console()

# We use absolute imports based on the project structure
from src.inference.model_unified import run_national_unified_model


def main():
    """Run the national unified model.

    This intentionally does not show a custom progress dashboard: an earlier
    version animated hardcoded placeholder numbers (fake acceptance rate,
    fake iterations/sec, fake log lines) for a few seconds before the real
    run started, with a comment admitting it was "mocking for UX". PyMC's
    own sampler already reports real per-chain progress; wrapping that in
    fabricated telemetry added nothing but a false impression of insight
    into a run that hadn't started yet.
    """
    console.print("[bold cyan]BS-UBEM: Starting national unified Bayesian inference run.[/bold cyan]")
    try:
        run_national_unified_model()
    except Exception as e:
        console.print(f"[bold red]Error during pipeline execution:[/bold red] {e}")
        raise
    console.print("[bold green]Run complete.[/bold green]")


if __name__ == "__main__":
    main()
