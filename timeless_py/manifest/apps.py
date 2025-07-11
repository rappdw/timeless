import logging
import shlex
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def generate_apps_manifest(output_path: Path) -> Optional[Path]:
    """
    Generates a JSON manifest of installed applications using `system_profiler`.

    Args:
        output_path: The directory to save the manifest in.

    Returns:
        The path to the generated manifest, or None if it fails.
    """
    manifest_path = output_path / "applications.json"
    command = [
        "system_profiler",
        "SPApplicationsDataType",
        "-json",
    ]

    cmd_str = " ".join(shlex.quote(str(arg)) for arg in command)
    logger.info(f"Generating applications manifest with command: {cmd_str}")

    try:
        with open(manifest_path, "w") as f:
            subprocess.run(
                command,
                check=True,
                text=True,
                stdout=f,
            )
        logger.info(f"Successfully generated applications manifest at {manifest_path}")
        return manifest_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate applications manifest: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error("`system_profiler` command not found.")
        return None
