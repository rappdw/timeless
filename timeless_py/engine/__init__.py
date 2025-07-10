"""
Engine package for Timeless-Py.

This module provides the base classes for backup engines in Timeless-Py.
Interface and implementations for different backup engines (Restic, Borg, Kopia).
"""

import abc
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Snapshot:
    """Represents a backup snapshot."""

    id: str
    time: datetime
    hostname: str
    paths: List[str]
    tags: List[str]

    # Engine-specific metadata
    metadata: Dict[str, Any]


class BaseEngine(abc.ABC):
    """Base class for backup engines."""

    @abc.abstractmethod
    def init(self, repo_path: Path, password: str) -> bool:
        """Initialize a new repository."""
        pass

    @abc.abstractmethod
    def backup(
        self,
        paths: List[Path],
        exclude_patterns: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
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
        pass

    @abc.abstractmethod
    def snapshots(self) -> List[Snapshot]:
        """List all snapshots in the repository."""
        pass

    @abc.abstractmethod
    def forget(self, snapshot_ids: List[str]) -> bool:
        """
        Remove snapshots from the repository index.

        Args:
            snapshot_ids: List of snapshot IDs to forget

        Returns:
            True if successful, False otherwise
        """
        pass

    @abc.abstractmethod
    def prune(self) -> bool:
        """
        Remove unreferenced data from the repository.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abc.abstractmethod
    def check(self) -> bool:
        """
        Check repository integrity.

        Returns:
            True if repository is healthy, False otherwise
        """
        pass

    @abc.abstractmethod
    def restore(
        self, snapshot_id: str, paths: List[str], target: Optional[Path] = None
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
        pass

    @abc.abstractmethod
    def mount(self, target: Path) -> bool:
        """
        Mount the repository.

        Args:
            target: Mount point

        Returns:
            True if successful, False otherwise
        """
        pass

    @abc.abstractmethod
    def unmount(self, target: Path) -> bool:
        """
        Unmount the repository.

        Args:
            target: Mount point

        Returns:
            True if successful, False otherwise
        """
        pass
