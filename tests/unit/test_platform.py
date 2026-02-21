"""Tests for the platform helpers module."""

from unittest.mock import patch

from timeless_py.platform import default_mount_path, is_linux, is_macos, unmount_command


class TestIsMacos:
    def test_true_on_darwin(self) -> None:
        with patch("timeless_py.platform.sys") as mock_sys:
            mock_sys.platform = "darwin"
            assert is_macos() is True

    def test_false_on_linux(self) -> None:
        with patch("timeless_py.platform.sys") as mock_sys:
            mock_sys.platform = "linux"
            assert is_macos() is False


class TestIsLinux:
    def test_true_on_linux(self) -> None:
        with patch("timeless_py.platform.sys") as mock_sys:
            mock_sys.platform = "linux"
            assert is_linux() is True

    def test_true_on_linux_variant(self) -> None:
        with patch("timeless_py.platform.sys") as mock_sys:
            mock_sys.platform = "linux2"
            assert is_linux() is True

    def test_false_on_darwin(self) -> None:
        with patch("timeless_py.platform.sys") as mock_sys:
            mock_sys.platform = "darwin"
            assert is_linux() is False


class TestDefaultMountPath:
    def test_macos(self) -> None:
        with patch("timeless_py.platform.sys") as mock_sys:
            mock_sys.platform = "darwin"
            assert default_mount_path() == "/Volumes/TimeVault"

    def test_linux(self) -> None:
        with patch("timeless_py.platform.sys") as mock_sys:
            mock_sys.platform = "linux"
            assert default_mount_path() == "/mnt/timevault"


class TestUnmountCommand:
    def test_macos(self) -> None:
        with patch("timeless_py.platform.sys") as mock_sys:
            mock_sys.platform = "darwin"
            assert unmount_command("/Volumes/TimeVault") == [
                "umount",
                "/Volumes/TimeVault",
            ]

    def test_linux(self) -> None:
        with patch("timeless_py.platform.sys") as mock_sys:
            mock_sys.platform = "linux"
            assert unmount_command("/mnt/timevault") == [
                "fusermount",
                "-u",
                "/mnt/timevault",
            ]
