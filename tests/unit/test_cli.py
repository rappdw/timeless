"""
Tests for the CLI module.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from timeless_py.cli import app


@pytest.fixture
def runner():
    """Fixture to create a CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_restic_engine():
    """Fixture to mock ResticEngine."""
    with patch("timeless_py.cli.ResticEngine") as mock_engine_class:
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        yield mock_engine


def test_version(runner):
    """Test the version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Timeless-Py version" in result.stdout


def test_backup_command(runner, mock_restic_engine):
    """Test the backup command."""
    # Configure mock to return a snapshot ID
    mock_restic_engine.backup.return_value = "abc123"
    mock_restic_engine.snapshots.return_value = []

    # Set environment variables for the test
    with patch.dict(
        os.environ,
        {"TIMELESS_REPO": "/tmp/test-repo", "TIMELESS_PASSWORD": "test-password"},
    ):
        result = runner.invoke(app, ["backup", "/home/user/docs"])

    assert result.exit_code == 0
    assert "Backup successful" in result.stdout

    # Check that the engine was initialized correctly
    from timeless_py.cli import ResticEngine

    ResticEngine.assert_called_once_with(
        repo_path=Path("/tmp/test-repo"), password="test-password", password_file=None
    )

    # Check that backup was called with the correct arguments
    mock_restic_engine.backup.assert_called_once()
    args, kwargs = mock_restic_engine.backup.call_args
    assert len(kwargs["paths"]) == 1
    assert str(kwargs["paths"][0]).endswith("/home/user/docs")


def test_backup_command_with_policy(runner, mock_restic_engine, tmp_path):
    """Test the backup command with a retention policy."""
    # Configure mock to return a snapshot ID
    mock_restic_engine.backup.return_value = "abc123"

    # Create a mock snapshot
    mock_snapshot = MagicMock()
    mock_snapshot.id = "def456"
    mock_restic_engine.snapshots.return_value = [mock_snapshot]

    # Create a policy file
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text(
        """
    hourly: 12
    daily: 7
    weekly: 4
    monthly: 6
    yearly: 2
    exclude_patterns:
      - "*.tmp"
      - "node_modules/"
    """
    )

    # Set environment variables for the test
    with patch.dict(
        os.environ,
        {"TIMELESS_REPO": "/tmp/test-repo", "TIMELESS_PASSWORD": "test-password"},
    ):
        result = runner.invoke(
            app,
            [
                "backup",
                "/home/user/docs",
                "--policy",
                str(policy_file),
                "--tag",
                "test",
            ],
        )

    assert result.exit_code == 0
    assert "Backup successful" in result.stdout

    # Check that backup was called with the correct arguments
    mock_restic_engine.backup.assert_called_once()
    args, kwargs = mock_restic_engine.backup.call_args
    assert len(kwargs["paths"]) == 1
    assert kwargs["exclude_patterns"] == ["*.tmp", "node_modules/"]
    assert kwargs["tags"] == ["test"]

    # Check that forget and prune were called
    mock_restic_engine.forget.assert_called_once()
    mock_restic_engine.prune.assert_called_once()


def test_check_command(runner, mock_restic_engine):
    """Test the check command."""
    # Configure mock to return success
    mock_restic_engine.check.return_value = True

    # Set environment variables for the test
    with patch.dict(
        os.environ,
        {"TIMELESS_REPO": "/tmp/test-repo", "TIMELESS_PASSWORD": "test-password"},
    ):
        result = runner.invoke(app, ["check"])

    assert result.exit_code == 0
    assert "Repository integrity check passed" in result.stdout

    # Check that check was called
    mock_restic_engine.check.assert_called_once()


def test_restore_command(runner, mock_restic_engine):
    """Test the restore command."""
    # Configure mock to return success
    mock_restic_engine.restore.return_value = True

    # Set environment variables for the test
    with patch.dict(
        os.environ,
        {"TIMELESS_REPO": "/tmp/test-repo", "TIMELESS_PASSWORD": "test-password"},
    ):
        result = runner.invoke(
            app,
            [
                "restore",
                "abc123",
                "/home/user/docs/file.txt",
                "--target",
                "/tmp/restore",
            ],
        )

    assert result.exit_code == 0
    assert "Successfully restored" in result.stdout

    # Check that restore was called with the correct arguments
    mock_restic_engine.restore.assert_called_once()
    args, kwargs = mock_restic_engine.restore.call_args
    assert args[0] == "abc123"
    assert args[1] == ["/home/user/docs/file.txt"]
    assert str(args[2]).endswith("/tmp/restore")


def test_snapshots_command(runner, mock_restic_engine):
    """Test the snapshots command."""
    # Create mock snapshots
    mock_snapshot1 = MagicMock()
    mock_snapshot1.id = "abc123"
    mock_snapshot1.time.strftime.return_value = "2023-01-01 12:00:00"
    mock_snapshot1.hostname = "test-host"
    mock_snapshot1.paths = ["/home/user/docs"]
    mock_snapshot1.tags = ["test"]

    mock_snapshot2 = MagicMock()
    mock_snapshot2.id = "def456"
    mock_snapshot2.time.strftime.return_value = "2023-01-02 12:00:00"
    mock_snapshot2.hostname = "test-host"
    mock_snapshot2.paths = ["/home/user/photos"]
    mock_snapshot2.tags = ["backup"]

    mock_restic_engine.snapshots.return_value = [mock_snapshot1, mock_snapshot2]

    # Set environment variables for the test
    with patch.dict(
        os.environ,
        {"TIMELESS_REPO": "/tmp/test-repo", "TIMELESS_PASSWORD": "test-password"},
    ):
        result = runner.invoke(app, ["snapshots"])

    assert result.exit_code == 0
    assert "Snapshots" in result.stdout

    # Check that snapshots was called
    mock_restic_engine.snapshots.assert_called_once()


def test_snapshots_command_json(runner, mock_restic_engine):
    """Test the snapshots command with JSON output."""
    # Create mock snapshots
    mock_snapshot1 = MagicMock()
    mock_snapshot1.id = "abc123"
    mock_snapshot1.time.isoformat.return_value = "2023-01-01T12:00:00Z"
    mock_snapshot1.hostname = "test-host"
    mock_snapshot1.paths = ["/home/user/docs"]
    mock_snapshot1.tags = ["test"]

    mock_restic_engine.snapshots.return_value = [mock_snapshot1]

    # Set environment variables for the test
    with patch.dict(
        os.environ,
        {"TIMELESS_REPO": "/tmp/test-repo", "TIMELESS_PASSWORD": "test-password"},
    ):
        result = runner.invoke(app, ["snapshots", "--json"])

    assert result.exit_code == 0
    assert "abc123" in result.stdout
    assert "2023-01-01T12:00:00Z" in result.stdout

    # Check that snapshots was called
    mock_restic_engine.snapshots.assert_called_once()


def test_error_handling_no_repo(runner):
    """Test error handling when no repository is specified."""
    result = runner.invoke(app, ["backup"])

    assert result.exit_code == 1
    assert "Repository path not specified" in result.stdout


def test_error_handling_no_password(runner):
    """Test error handling when no password is specified."""
    with patch.dict(os.environ, {"TIMELESS_REPO": "/tmp/test-repo"}):
        result = runner.invoke(app, ["backup"])

    assert result.exit_code == 1
    assert "Password not specified" in result.stdout
