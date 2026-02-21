import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from timeless_py.engine import Snapshot
from timeless_py.manifest.apps import generate_apps_manifest
from timeless_py.manifest.brew import generate_brewfile
from timeless_py.manifest.mas import generate_mas_manifest
from timeless_py.manifest.replay import (
    find_latest_manifest_snapshot,
    replay_brewfile,
    replay_mas_manifest,
    restore_manifests,
)


@patch("subprocess.run")
def test_generate_brewfile_success(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="Success")
    result = generate_brewfile(tmp_path)
    assert result == tmp_path / "Brewfile"
    assert mock_run.call_count == 2  # which brew + brew bundle dump


@patch("subprocess.run")
def test_generate_brewfile_brew_not_found(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.side_effect = [FileNotFoundError, None]  # `which brew` fails
    result = generate_brewfile(tmp_path)
    assert result is None


@patch("timeless_py.manifest.apps.sys")
@patch("subprocess.run")
def test_generate_apps_manifest_success(
    mock_run: MagicMock, mock_sys: MagicMock, tmp_path: Path
) -> None:
    mock_sys.platform = "darwin"
    mock_run.return_value = MagicMock(returncode=0)
    with patch("builtins.open", mock_open()) as mock_file:
        result = generate_apps_manifest(tmp_path)
        assert result == tmp_path / "applications.json"
        mock_file.assert_called_once_with(tmp_path / "applications.json", "w")


@patch("subprocess.run")
def test_generate_mas_manifest_success(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.return_value = MagicMock(returncode=0)
    with patch("builtins.open", mock_open()) as mock_file:
        result = generate_mas_manifest(tmp_path)
        assert result == tmp_path / "mas.txt"
        mock_file.assert_called_once_with(tmp_path / "mas.txt", "w")


def test_find_latest_manifest_snapshot() -> None:
    mock_engine = MagicMock()
    snapshots = [
        Snapshot("1", datetime(2023, 1, 2), "h", [], ["manifest"], {}),
        Snapshot("2", datetime(2023, 1, 1), "h", [], [], {}),
    ]
    mock_engine.snapshots.return_value = snapshots
    result = find_latest_manifest_snapshot(mock_engine)
    assert result is not None
    assert result.id == "1"


def test_restore_manifests_success(tmp_path: Path) -> None:
    mock_engine = MagicMock()
    mock_engine.restore.return_value = True
    (tmp_path / "Brewfile").touch()
    (tmp_path / "applications.json").touch()
    result = restore_manifests(mock_engine, "snap1", tmp_path)
    assert "Brewfile" in result
    assert "applications.json" in result


@patch("subprocess.Popen")
def test_replay_brewfile_success(mock_popen: MagicMock, tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.touch()
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_process.stdout.readline.return_value = ""
    mock_popen.return_value = mock_process
    assert replay_brewfile(brewfile) is True


@patch("subprocess.run")
def test_replay_mas_manifest_success(mock_run: MagicMock, tmp_path: Path) -> None:
    mas_file = tmp_path / "mas.txt"
    mas_file.write_text("12345 App Name")
    mock_run.return_value = MagicMock(returncode=0)
    assert replay_mas_manifest(mas_file) is True
    mock_run.assert_called_with(
        ["mas", "install", "12345"], check=True, capture_output=True, text=True
    )


@patch("timeless_py.manifest.apps.sys")
@patch("timeless_py.manifest.apps.shutil.which")
@patch("timeless_py.manifest.apps.subprocess.run")
def test_generate_apps_manifest_linux_dpkg(
    mock_run: MagicMock, mock_which: MagicMock, mock_sys: MagicMock, tmp_path: Path
) -> None:
    """Test Linux manifest generation with dpkg available."""
    mock_sys.platform = "linux"
    mock_which.side_effect = lambda cmd: (
        "/usr/bin/dpkg-query" if cmd == "dpkg" else None
    )

    mock_result = MagicMock()
    mock_result.stdout = "vim 9.0\ncurl 7.88\n"
    mock_run.return_value = mock_result

    result = generate_apps_manifest(tmp_path)
    assert result == tmp_path / "applications.json"

    data = json.loads((tmp_path / "applications.json").read_text())
    assert "dpkg" in data
    assert "vim 9.0" in data["dpkg"]


@patch("timeless_py.manifest.apps.sys")
@patch("timeless_py.manifest.apps.shutil.which")
def test_generate_apps_manifest_linux_no_pkg_managers(
    mock_which: MagicMock, mock_sys: MagicMock, tmp_path: Path
) -> None:
    """Test Linux manifest returns None when no package managers found."""
    mock_sys.platform = "linux"
    mock_which.return_value = None

    result = generate_apps_manifest(tmp_path)
    assert result is None
