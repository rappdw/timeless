"""
Command-line interface for Timeless-Py.

This module provides the command-line entry point for the Timeless-Py backup application.
"""

import logging
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from timeless_py import __version__

# Set up the console and logger
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger("timeless")

# Create the Typer app
app = typer.Typer(
    help="Time Machine-style personal backup orchestrated by Python & uv.",
    add_completion=False,
)


@app.callback()
def callback(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output."
    ),
    json: bool = typer.Option(False, "--json", help="Output logs in JSON format."),
    version: bool = typer.Option(
        False, "--version", help="Show the application version and exit."
    ),
) -> None:
    """
    Timeless-Py: Snapshot what matters, remember how to rebuild the rest.
    """
    if version:
        console.print(f"Timeless-Py version: {__version__}")
        raise typer.Exit()
    
    # Configure logging level based on verbosity
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Configure JSON logging if requested
    if json:
        # Reconfigure logging for JSON output
        for handler in logging.root.handlers:
            logging.root.removeHandler(handler)
        logging.basicConfig(
            level=logging.INFO if not verbose else logging.DEBUG,
            format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S",
            stream=sys.stdout,
        )
        logger.debug("JSON logging enabled")


@app.command()
def init(
    wizard: bool = typer.Option(True, "--wizard/--no-wizard", help="Run interactive configuration wizard.")
) -> None:
    """
    Initialize Timeless with configuration wizard.
    
    This command sets up the repository, stores keys in the Keychain, and creates necessary launch configurations.
    """
    logger.info("Initializing Timeless...")
    # TODO: Implement initialization logic
    if wizard:
        logger.info("Starting configuration wizard...")
    else:
        logger.info("Skipping wizard, using default settings")


@app.command()
def backup() -> None:
    """
    Run backup snapshot, retention pruning, and manifest refresh.
    """
    logger.info("Running backup...")
    # TODO: Implement backup logic


@app.command()
def mount() -> None:
    """
    Mount selected snapshot at /Volumes/Timeless.
    """
    logger.info("Mounting snapshot...")
    # TODO: Implement mount logic


@app.command()
def restore(
    snapshot: str = typer.Argument(..., help="Snapshot ID or timestamp to restore from."),
    path: str = typer.Argument(..., help="Path to restore from snapshot."),
    target: Optional[str] = typer.Option(
        None, "--target", "-t", help="Target path for restoration (default: current directory)."
    )
) -> None:
    """
    Restore a file or directory from a snapshot.
    """
    target_display = target if target else "current directory"
    logger.info(f"Restoring {path} from snapshot {snapshot} to {target_display}...")
    # TODO: Implement restore logic


@app.command(name="snapshots")
def list_snapshots(
    json_output: bool = typer.Option(False, "--json", help="Output snapshots in JSON format.")
) -> None:
    """
    List available snapshots.
    """
    logger.info("Listing snapshots...")
    # TODO: Implement snapshot listing logic


@app.command()
def check() -> None:
    """
    Invoke engine integrity check and report via notification center.
    """
    logger.info("Running repository integrity check...")
    # TODO: Implement repository check logic


@app.command(name="brew-replay")
def brew_replay() -> None:
    """
    Reinstall software from manifests onto a clean Mac.
    """
    logger.info("Replaying software installation from manifests...")
    # TODO: Implement brew replay logic


if __name__ == "__main__":
    app()
