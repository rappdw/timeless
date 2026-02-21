"""
Tests for the Restic engine module.
"""

import json
import os
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from timeless_py.engine import Snapshot
from timeless_py.engine.restic import ResticEngine


@pytest.fixture
def mock_subprocess() -> Generator[MagicMock, None, None]:
    """Fixture to mock subprocess calls."""
    with patch("timeless_py.engine.restic.subprocess") as mock_subprocess:
        # Configure the mock to return a successful CompletedProcess
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = b'{"success": true}'
        mock_subprocess.run.return_value = mock_process
        yield mock_subprocess


@pytest.fixture
def restic_engine() -> Generator[ResticEngine, None, None]:
    """Fixture to create a ResticEngine instance."""
    with patch.dict(os.environ, {"RESTIC_PASSWORD": "test-password"}):
        engine = ResticEngine(
            repo_path=Path("/tmp/test-repo"), password="test-password"
        )
        yield engine


def test_restic_engine_init(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test initializing a repository."""
    result = restic_engine.init(Path("/tmp/test-repo"), "test-password")
    assert result is True

    mock_subprocess.run.assert_called_once()

    # Check that the command includes 'init'
    args, kwargs = mock_subprocess.run.call_args
    assert "init" in args[0]


def test_restic_engine_backup(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test backing up files."""
    # Configure mock to return a snapshot ID
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = '{"message_type": "summary", "snapshot_id": "abc123"}'
    mock_subprocess.run.return_value = mock_process

    paths = [Path("/home/user/docs"), Path("/home/user/photos")]
    exclude_patterns = ["*.tmp", "node_modules/"]
    tags = ["test", "backup"]

    snapshot_id = restic_engine.backup(paths, exclude_patterns, tags)

    assert snapshot_id == "abc123"
    mock_subprocess.run.assert_called_once()

    # Check that the command includes 'backup'
    args, kwargs = mock_subprocess.run.call_args
    assert "backup" in args[0]

    # Check that paths are included
    for path in paths:
        assert str(path) in args[0]

    # Check that exclude patterns are included
    for pattern in exclude_patterns:
        assert f"--exclude={pattern}" in args[0]

    # Check that tags are included
    for tag in tags:
        assert f"--tag={tag}" in args[0]


def test_restic_engine_snapshots(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test listing snapshots."""
    # Sample snapshot data
    snapshots_data = [
        {
            "id": "abc123",
            "time": "2023-01-01T12:00:00Z",
            "hostname": "test-host",
            "paths": ["/home/user/docs"],
            "tags": ["test"],
        },
        {
            "id": "def456",
            "time": "2023-01-02T12:00:00Z",
            "hostname": "test-host",
            "paths": ["/home/user/photos"],
            "tags": ["backup"],
        },
    ]

    # Configure mock to return snapshot data
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = json.dumps(snapshots_data).encode()
    mock_subprocess.run.return_value = mock_process

    snapshots = restic_engine.snapshots()

    assert len(snapshots) == 2
    assert isinstance(snapshots[0], Snapshot)
    assert snapshots[0].id == "abc123"
    assert snapshots[1].id == "def456"

    mock_subprocess.run.assert_called_once()

    # Check that the command includes 'snapshots'
    args, kwargs = mock_subprocess.run.call_args
    assert "snapshots" in args[0]
    assert "--json" in args[0]


def test_restic_engine_forget(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test forgetting snapshots."""
    snapshot_ids = ["abc123", "def456"]

    result = restic_engine.forget(snapshot_ids)

    assert result is True
    mock_subprocess.run.assert_called_once()

    # Check that the command includes 'forget'
    args, kwargs = mock_subprocess.run.call_args
    assert "forget" in args[0]

    # Check that snapshot IDs are included
    for snapshot_id in snapshot_ids:
        assert snapshot_id in args[0]


def test_restic_engine_prune(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test pruning the repository."""
    result = restic_engine.prune()

    assert result is True
    mock_subprocess.run.assert_called_once()

    # Check that the command includes 'prune'
    args, kwargs = mock_subprocess.run.call_args
    assert "prune" in args[0]


def test_restic_engine_check(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test checking the repository."""
    result = restic_engine.check()

    assert result is True
    mock_subprocess.run.assert_called_once()

    # Check that the command includes 'check'
    args, kwargs = mock_subprocess.run.call_args
    assert "check" in args[0]


def test_restic_engine_restore(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test restoring files."""
    snapshot_id = "abc123"
    paths = ["/home/user/docs/file.txt"]
    target = Path("/tmp/restore")

    result = restic_engine.restore(snapshot_id, paths, target)

    assert result is True
    mock_subprocess.run.assert_called_once()

    # Check that the command includes 'restore'
    args, kwargs = mock_subprocess.run.call_args
    assert "restore" in args[0]
    assert snapshot_id in args[0]

    # Check that paths are included
    for path in paths:
        assert path in args[0]

    # Check that target is included
    assert f"--target={target}" in args[0]


def test_restic_engine_mount(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test mounting the repository."""
    target = Path("/tmp/mount")

    # Configure mock to simulate a running process for mount
    mock_subprocess.run.return_value.returncode = 0

    result = restic_engine.mount(target)

    assert result is True
    mock_subprocess.run.assert_called_once()

    # Check that the command includes 'mount'
    args, kwargs = mock_subprocess.run.call_args
    assert "mount" in args[0]
    assert str(target) in args[0]


def test_restic_engine_unmount(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test unmounting the repository."""
    target = Path("/tmp/mount")

    # Configure mock for successful unmount
    mock_subprocess.run.return_value.returncode = 0

    result = restic_engine.unmount(target)

    assert result is True
    mock_subprocess.run.assert_called_once()

    # Check that the command is correct for unmounting
    args, kwargs = mock_subprocess.run.call_args
    assert "umount" in args[0] or "fusermount" in args[0]
    assert str(target) in args[0]


def test_restic_engine_unmount_macos(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test unmount uses umount on macOS."""
    mock_subprocess.run.return_value.returncode = 0

    with patch("timeless_py.engine.restic.unmount_command", return_value=["umount", "/Volumes/Timeless"]):
        result = restic_engine.unmount(Path("/Volumes/Timeless"))

    assert result is True
    args, _ = mock_subprocess.run.call_args
    assert args[0] == ["umount", "/Volumes/Timeless"]


def test_restic_engine_unmount_linux(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test unmount uses fusermount -u on Linux."""
    mock_subprocess.run.return_value.returncode = 0

    with patch("timeless_py.engine.restic.unmount_command", return_value=["fusermount", "-u", "/mnt/timeless"]):
        result = restic_engine.unmount(Path("/mnt/timeless"))

    assert result is True
    args, _ = mock_subprocess.run.call_args
    assert args[0] == ["fusermount", "-u", "/mnt/timeless"]


def test_restic_engine_run_command_error(
    restic_engine: ResticEngine, mock_subprocess: MagicMock
) -> None:
    """Test error handling in the engine."""
    # Configure mock to simulate a failed command
    mock_subprocess.run.return_value.returncode = 1
    mock_subprocess.run.return_value.stderr = b"Error: repository not found"

    result = restic_engine.init(Path("/tmp/test-repo"), "test-password")

    assert result is False
    mock_subprocess.run.assert_called_once()
