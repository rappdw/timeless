import logging
import shlex
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def generate_brewfile(output_path: Path) -> Optional[Path]:
    """
    Generates a Brewfile using `brew bundle dump`.

    Args:
        output_path: The directory to save the Brewfile in.

    Returns:
        The path to the generated Brewfile, or None if it fails.
    """
    brewfile_path = output_path / "Brewfile"
    command = [
        "brew",
        "bundle",
        "dump",
        "--describe",
        "--force",
        f"--file={brewfile_path}",
    ]

    cmd_str = " ".join(shlex.quote(str(arg)) for arg in command)
    logger.info(f"Generating Brewfile with command: {cmd_str}")

    try:
        subprocess.run(["which", "brew"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning(
            "Homebrew (`brew`) is not installed. Skipping Brewfile generation."
        )
        return None

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Successfully generated Brewfile at {brewfile_path}")
        logger.debug(f"brew bundle dump stdout: {result.stdout}")
        return brewfile_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate Brewfile: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error(
            "`brew` command not found. Is Homebrew installed and in your PATH?"
        )
        return None
