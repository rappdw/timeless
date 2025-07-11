import logging
import shlex
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def generate_mas_manifest(output_path: Path) -> Optional[Path]:
    """
    Generates a text manifest of installed Mac App Store apps using `mas`.

    Args:
        output_path: The directory to save the manifest in.

    Returns:
        The path to the generated manifest, or None if it fails.
    """
    manifest_path = output_path / "mas.txt"
    command = ["mas", "list"]

    cmd_str = " ".join(shlex.quote(str(arg)) for arg in command)
    logger.info(f"Generating MAS manifest with command: {cmd_str}")

    try:
        subprocess.run(["which", "mas"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning(
            "Mac App Store CLI (`mas`) is not installed. "
            "Skipping MAS manifest generation."
        )
        return None

    try:
        with open(manifest_path, "w") as f:
            subprocess.run(
                command,
                check=True,
                text=True,
                stdout=f,
            )
        logger.info(f"Successfully generated MAS manifest at {manifest_path}")
        return manifest_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate MAS manifest: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error("`mas` command not found. Is it installed and in your PATH?")
        return None
