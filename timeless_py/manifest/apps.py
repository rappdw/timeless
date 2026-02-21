import json
import logging
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _generate_macos_manifest(manifest_path: Path) -> Optional[Path]:
    """Generate an applications manifest on macOS via ``system_profiler``."""
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


def _generate_linux_manifest(manifest_path: Path) -> Optional[Path]:
    """Generate an applications manifest on Linux by probing package managers."""
    packages: Dict[str, Any] = {}

    if shutil.which("dpkg"):
        packages["dpkg"] = _collect_dpkg()

    if shutil.which("rpm"):
        packages["rpm"] = _collect_rpm()

    if shutil.which("snap"):
        packages["snap"] = _collect_snap()

    if shutil.which("flatpak"):
        packages["flatpak"] = _collect_flatpak()

    if not packages:
        logger.warning("No supported package managers found on this Linux system.")
        return None

    with open(manifest_path, "w") as f:
        json.dump(packages, f, indent=2)

    logger.info(f"Successfully generated applications manifest at {manifest_path}")
    return manifest_path


def _run_pkg_command(cmd: List[str]) -> List[str]:
    """Run a package-manager command and return stdout lines."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip().splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(f"Command {cmd} failed: {e}")
        return []


def _collect_dpkg() -> List[str]:
    return _run_pkg_command(["dpkg-query", "-W", "-f", "${Package} ${Version}\n"])


def _collect_rpm() -> List[str]:
    return _run_pkg_command(["rpm", "-qa", "--qf", "%{NAME} %{VERSION}\n"])


def _collect_snap() -> List[str]:
    return _run_pkg_command(["snap", "list"])


def _collect_flatpak() -> List[str]:
    return _run_pkg_command(["flatpak", "list", "--columns=application,version"])


def generate_apps_manifest(output_path: Path) -> Optional[Path]:
    """
    Generates a JSON manifest of installed applications.

    On macOS this uses ``system_profiler``; on Linux it probes
    ``dpkg``, ``rpm``, ``snap``, and ``flatpak``.

    Args:
        output_path: The directory to save the manifest in.

    Returns:
        The path to the generated manifest, or None if it fails.
    """
    manifest_path = output_path / "applications.json"

    if sys.platform == "darwin":
        return _generate_macos_manifest(manifest_path)
    else:
        return _generate_linux_manifest(manifest_path)
