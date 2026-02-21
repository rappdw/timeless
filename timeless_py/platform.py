"""
Platform detection helpers for Timeless-Py.

Centralizes macOS vs Linux differences so the rest of the codebase
can call simple functions instead of scattering ``sys.platform`` checks.
"""

import sys
from typing import List


def is_macos() -> bool:
    """Return True when running on macOS."""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Return True when running on Linux."""
    return sys.platform.startswith("linux")


def default_mount_path() -> str:
    """Return the platform-appropriate default mount point."""
    if is_macos():
        return "/Volumes/TimeVault"
    return "/mnt/timevault"


def unmount_command(target: str) -> List[str]:
    """Return the command list to unmount *target* on the current platform."""
    if is_macos():
        return ["umount", target]
    return ["fusermount", "-u", target]
