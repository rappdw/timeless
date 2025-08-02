"""
Restic engine implementation for Timeless-Py.

This module provides the Restic engine for Timeless-Py.
This module provides a wrapper around the Restic backup tool,
handling subprocess calls and JSON parsing.
"""

import json
import logging
import os
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import orjson  # High-performance JSON parser

from timeless_py.engine import BaseEngine, Snapshot

logger = logging.getLogger("timeless.engine.restic")


class ResticEngine(BaseEngine):
    """Restic backup engine implementation."""

    def __init__(
        self,
        repo_path: Path,
        password: Optional[str] = None,
        password_file: Optional[Path] = None,
        binary_path: str = "restic",
    ):
        """
        Initialize the Restic engine.

        Args:
            repo_path: Path to the Restic repository
            password: Repository password (mutually exclusive with password_file)
            password_file: Path to file containing the repository password
            binary_path: Path to the Restic binary
        """
        self.repo_path = repo_path
        self.password = password
        self.password_file = password_file
        self.binary_path = binary_path

        if not password and not password_file:
            raise ValueError("Either password or password_file must be provided")
        if password and password_file:
            raise ValueError("Only one of password or password_file can be provided")

    def repository_exists(self) -> bool:
        """
        Check if a repository exists by directly checking the filesystem or SFTP.

        Returns:
            bool: True if the repository exists, False otherwise
        """
        repo_path_str = str(self.repo_path)

        # Handle SFTP repositories
        if repo_path_str.startswith("sftp:"):
            try:
                # Use a simple command to check if the repo exists via SFTP
                # The 'cat config' command will succeed only if the repository exists
                returncode, _, _ = self._run_command(["cat", "config"], check=False)
                return returncode == 0
            except Exception as e:
                logger.debug(f"Error checking SFTP repository existence: {e}")
                return False
        else:
            # Handle filesystem repositories
            try:
                # Check if directory exists and contains a config file
                repo_dir = Path(repo_path_str)
                config_file = repo_dir / "config"
                return config_file.exists()
            except Exception as e:
                logger.debug(f"Error checking filesystem repository existence: {e}")
                return False

    def init(self, repo_path: Path, password: str) -> bool:
        """Initializes a new restic repository."""
        self.repo_path = repo_path
        self.password = password
        self.password_file = None
        logger.info(f"Initializing repository at {self.repo_path}")
        try:
            returncode, _, stderr = self._run_command(["init"], check=False)
            if returncode == 0:
                return True
            logger.error(f"Failed to initialize repository: {stderr}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize repository at {self.repo_path}: {e}")
            return False

    def _get_env(self) -> Dict[str, str]:
        """Get the environment variables for Restic commands."""
        env = os.environ.copy()
        env["RESTIC_REPOSITORY"] = str(self.repo_path)

        if self.password:
            env["RESTIC_PASSWORD"] = self.password
        elif self.password_file:
            env["RESTIC_PASSWORD_FILE"] = str(self.password_file)

        return env

    def _run_command(
        self,
        args: List[str],
        capture_output: bool = True,
        check: bool = True,
        stream_output: bool = False,
    ) -> Tuple[int, str, str]:
        """
        Run a Restic command.

        Args:
            args: Command arguments
            capture_output: Whether to capture stdout/stderr
            check: Whether to check the return code

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = [self.binary_path] + args
        cmd_str = " ".join(shlex.quote(str(arg)) for arg in cmd)
        logger.debug(f"Running command: {cmd_str}")

        try:
            # When streaming, we can't also capture the output.
            # The subprocess will inherit stdout/stderr from the parent.
            use_capture = capture_output and not stream_output

            result = subprocess.run(
                cmd,
                env=self._get_env(),
                capture_output=use_capture,
                text=True,
                check=check,
            )
            return result.returncode, result.stdout or "", result.stderr or ""
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {cmd_str}")
            logger.error(f"Return code: {e.returncode}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            if check:
                raise
            return e.returncode, e.stdout, e.stderr

    def backup(
        self,
        paths: List[Path],
        exclude_patterns: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        verbose: bool = False,
    ) -> Optional[str]:
        """
        Create a new backup snapshot.

        Args:
            paths: List of paths to back up
            exclude_patterns: List of patterns to exclude
            tags: List of tags to apply to the snapshot

        Returns:
            Snapshot ID if successful, None otherwise
        """
        args = ["backup"]
        if verbose:
            args.append("--verbose")
        else:
            # JSON output is required to parse the snapshot ID
            args.append("--json")

        # Add paths
        for path in paths:
            args.append(str(path))

        # Add exclude patterns
        if exclude_patterns:
            for pattern in exclude_patterns:
                args.append(f"--exclude={pattern}")

        # Add tags
        if tags:
            for tag in tags:
                args.append(f"--tag={tag}")

        try:
            # When verbose is True, stdout is streamed and not captured.
            # We also don't use --json, so we can't parse the snapshot ID.
            capture_output = not verbose
            returncode, stdout, stderr = self._run_command(
                args, stream_output=verbose, capture_output=capture_output, check=False
            )

            if returncode == 3:
                # Restic returns  if some files could not be read. Treat as a warning.
                logger.warning(f"Backup completed with warnings (code: {returncode}).")
                if stderr:
                    logger.warning(f"Restic stderr:\n{stderr}")
            elif returncode != 0:
                logger.error(f"Backup failed with return code {returncode}: {stderr}")
                return None

            if verbose:
                # In verbose mode, we stream output and don't get a snapshot ID back.
                return None

            # Handle the case where stdout might be bytes (in tests) or string
            # (from _run_command)
            # First, try to handle it directly if it's a single JSON object
            try:
                if isinstance(stdout, bytes):
                    data = json.loads(stdout.decode("utf-8"))
                else:
                    data = json.loads(stdout)
                if data.get("message_type") == "summary":
                    snapshot_id = str(data["snapshot_id"])
                    logger.info(f"Created snapshot: {snapshot_id}")
                    return snapshot_id
            except (json.JSONDecodeError, AttributeError):
                # If it's not a single JSON object, try parsing line by line
                try:
                    if isinstance(stdout, bytes):
                        lines = stdout.decode("utf-8").strip().split("\n")
                    else:
                        lines = stdout.strip().split("\n")

                    for line in reversed(lines):
                        try:
                            data = json.loads(line)
                            if "snapshot_id" in data:
                                snapshot_id = str(data["snapshot_id"])
                                logger.info(f"Created snapshot: {snapshot_id}")
                                return snapshot_id
                        except json.JSONDecodeError:
                            continue
                except Exception as e:
                    logger.error(f"Error parsing backup output: {e}")
                    pass

            logger.warning("Could not find snapshot ID in output")
            return None
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    def snapshots(self) -> List[Snapshot]:
        """
        List all snapshots in the repository.

        Returns:
            List of Snapshot objects
        """
        try:
            _, stdout, _ = self._run_command(["snapshots", "--json"])
            data = orjson.loads(stdout)

            result = []
            for snap in data:
                snapshot = Snapshot(
                    id=snap["id"],
                    time=datetime.fromisoformat(snap["time"].replace("Z", "+00:00")),
                    hostname=snap["hostname"],
                    paths=snap["paths"],
                    tags=snap.get("tags", []),
                    metadata=snap,
                )
                result.append(snapshot)

            return result
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to list snapshots: {e}")
            # Check if the error indicates the repository doesn't exist
            if isinstance(
                e, subprocess.CalledProcessError
            ) and "repository does not exist" in str(e):
                # Re-raise the exception to properly handle repository initialization
                raise
            return []

    def forget(self, snapshot_ids: List[str]) -> bool:
        """
        Remove snapshots from the repository index.

        Args:
            snapshot_ids: List of snapshot IDs to forget

        Returns:
            True if successful, False otherwise
        """
        args = ["forget"]
        args.extend(snapshot_ids)

        try:
            self._run_command(args)
            logger.info(f"Forgot {len(snapshot_ids)} snapshots")
            return True
        except subprocess.CalledProcessError:
            logger.error("Failed to forget snapshots")
            return False

    def prune(self) -> bool:
        """
        Remove unreferenced data from the repository.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._run_command(["prune"])
            logger.info("Pruned repository")
            return True
        except subprocess.CalledProcessError:
            logger.error("Failed to prune repository")
            return False

    def check(self) -> bool:
        """
        Check repository integrity.

        Returns:
            True if repository is healthy, False otherwise
        """
        try:
            self._run_command(["check"])
            logger.info("Repository check passed")
            return True
        except subprocess.CalledProcessError:
            logger.error("Repository check failed")
            return False

    def restore(
        self,
        snapshot_id: str,
        paths: List[str],
        target: Optional[Path] = None,
    ) -> bool:
        """
        Restore files from a snapshot.

        Args:
            snapshot_id: ID of the snapshot to restore from
            paths: List of paths to restore
            target: Target directory for restoration

        Returns:
            True if successful, False otherwise
        """
        args = ["restore", snapshot_id]

        if target:
            args.append(f"--target={target}")
        else:
            args.append("--target=.")

        # Add paths to include
        for path in paths:
            args.extend(["--include", path])

        try:
            returncode, stdout, stderr = self._run_command(args)

            if returncode == 0 and stdout:
                logger.info(f"Restored {len(paths)} paths from snapshot {snapshot_id}")
                return True
            else:
                logger.error(f"Failed to restore from snapshot {snapshot_id}: {stderr}")
                return False
        except Exception as e:
            logger.error(f"Failed to restore from snapshot {snapshot_id}: {e}")
            return False

    def mount(self, target: Path) -> bool:
        """
        Mount the repository.

        Args:
            target: Mount point

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use subprocess.run to match test expectations
            args = ["mount", str(target)]
            result = subprocess.run(
                [self.binary_path] + args,
                env=self._get_env(),
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                logger.info(f"Mounted repository at {target}")
                return True
            else:
                logger.error(f"Failed to mount repository: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Failed to mount repository: {e}")
            return False

    def unmount(self, target: Path) -> bool:
        """
        Unmount the repository.

        Args:
            target: Mount point

        Returns:
            True if successful, False otherwise
        """
        try:
            # On macOS, use umount
            result = subprocess.run(
                ["umount", str(target)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info(f"Unmounted repository from {target}")
                return True
            else:
                logger.error(f"Failed to unmount repository: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Failed to unmount repository: {e}")
            return False
