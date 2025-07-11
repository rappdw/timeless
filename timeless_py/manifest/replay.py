import logging
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Optional

from timeless_py.engine import BaseEngine, Snapshot

logger = logging.getLogger(__name__)


def find_latest_manifest_snapshot(engine: BaseEngine) -> Optional[Snapshot]:
    """Finds the latest snapshot with the 'manifest' tag."""
    logger.info("Searching for the latest manifest snapshot...")
    # The engine's snapshots() method should ideally return snapshots sorted newest
    # first.
    for snapshot in engine.snapshots():
        if "manifest" in snapshot.tags:
            logger.info(
                f"Found latest manifest snapshot: {snapshot.id} from {snapshot.time}"
            )
            return snapshot
    logger.warning("No manifest snapshot found.")
    return None


def restore_manifests(
    engine: BaseEngine, snapshot_id: str, target_dir: Path
) -> Dict[str, Path]:
    """Restores all known manifest files from a snapshot to a target directory."""
    manifest_files = ["Brewfile", "applications.json", "mas.txt"]
    restored_paths: Dict[str, Path] = {}

    logger.info(f"Restoring manifests from snapshot {snapshot_id} to {target_dir}...")

    if engine.restore(snapshot_id=snapshot_id, paths=manifest_files, target=target_dir):
        for file in manifest_files:
            restored_file = target_dir / file
            if restored_file.exists():
                logger.debug(f"Successfully restored {file} to {restored_file}")
                restored_paths[file] = restored_file
            else:
                logger.warning(f"Could not find {file} in restored snapshot.")
    else:
        logger.error(f"Failed to restore files from snapshot {snapshot_id}")

    return restored_paths


def replay_brewfile(brewfile_path: Path) -> bool:
    """Reinstalls software from a Brewfile."""
    if not brewfile_path.exists():
        logger.error(f"Brewfile not found at {brewfile_path}")
        return False

    command = ["brew", "bundle", "install", f"--file={brewfile_path}"]
    cmd_str = " ".join(shlex.quote(str(arg)) for arg in command)
    logger.info(f"Replaying Brewfile with command: {cmd_str}")

    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                print(line, end="")

        returncode = process.wait()
        if returncode == 0:
            logger.info("Brewfile replay completed successfully.")
            return True
        else:
            logger.error(f"Brewfile replay failed with exit code {returncode}.")
            return False

    except FileNotFoundError:
        logger.error("`brew` command not found. Is Homebrew installed?")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during Brewfile replay: {e}")
        return False


def replay_mas_manifest(mas_manifest_path: Path) -> bool:
    """Reinstalls Mac App Store apps from a mas.txt manifest."""
    if not mas_manifest_path.exists():
        logger.error(f"MAS manifest not found at {mas_manifest_path}")
        return False

    logger.info("Replaying MAS manifest...")
    success = True
    try:
        with open(mas_manifest_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if not parts or not parts[0].isdigit():
                    continue

                app_id = parts[0]
                app_name = " ".join(parts[1:])
                logger.info(f"Installing {app_name} ({app_id}) from Mac App Store...")

                command = ["mas", "install", app_id]
                try:
                    subprocess.run(command, check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install {app_name} ({app_id}): {e.stderr}")
                    success = False
    except FileNotFoundError:
        logger.error("`mas` command not found. Is it installed?")
        return False

    if success:
        logger.info("MAS manifest replay completed.")
    else:
        logger.warning("MAS manifest replay completed with some errors.")

    return success
