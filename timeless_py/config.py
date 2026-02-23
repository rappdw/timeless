"""
Configuration file support for TimeVault.

Loads settings from ``~/.config/timevault/config.yaml`` (or
``$XDG_CONFIG_HOME/timevault/config.yaml``) and exposes them as typed
dataclasses that the CLI can merge with command-line flags.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger("timevault.config")


def default_config_path() -> Path:
    """Return the default configuration file path.

    Uses ``$XDG_CONFIG_HOME/timevault/config.yaml`` when set, otherwise
    falls back to ``~/.config/timevault/config.yaml``.
    """
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "timevault" / "config.yaml"
    return Path.home() / ".config" / "timevault" / "config.yaml"


@dataclass
class BackupPath:
    """A single backup path entry from the configuration file."""

    path: Path
    tag: Optional[str] = None
    exclude: List[str] = field(default_factory=list)


@dataclass
class RetentionConfig:
    """Retention schedule from the configuration file.

    All fields are optional so that we can distinguish "not set" from the
    ``RetentionPolicy`` defaults.
    """

    hourly: Optional[int] = None
    daily: Optional[int] = None
    weekly: Optional[int] = None
    monthly: Optional[int] = None
    yearly: Optional[int] = None


@dataclass
class TimevaultConfig:
    """Top-level configuration loaded from the YAML file."""

    repo: Optional[str] = None
    mount_path: Optional[str] = None
    backup_paths: List[BackupPath] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    retention: RetentionConfig = field(default_factory=RetentionConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimevaultConfig":
        """Construct a ``TimevaultConfig`` from a parsed YAML dictionary."""
        if not isinstance(data, dict):
            return cls()

        backup_paths: List[BackupPath] = []
        for entry in data.get("backup_paths", []):
            if not isinstance(entry, dict) or "path" not in entry:
                logger.warning("Skipping invalid backup_paths entry: %s", entry)
                continue
            backup_paths.append(
                BackupPath(
                    path=Path(entry["path"]).expanduser(),
                    tag=entry.get("tag"),
                    exclude=[
                        str(Path(e).expanduser()) for e in entry.get("exclude", [])
                    ],
                )
            )

        retention_data = data.get("retention") or {}
        retention = RetentionConfig(
            hourly=retention_data.get("hourly"),
            daily=retention_data.get("daily"),
            weekly=retention_data.get("weekly"),
            monthly=retention_data.get("monthly"),
            yearly=retention_data.get("yearly"),
        )

        return cls(
            repo=data.get("repo"),
            mount_path=data.get("mount_path"),
            backup_paths=backup_paths,
            exclude_patterns=[
                str(Path(e).expanduser()) for e in data.get("exclude_patterns", [])
            ],
            retention=retention,
        )

    @classmethod
    def from_file(cls, path: Path) -> "TimevaultConfig":
        """Read a YAML file and return a ``TimevaultConfig``.

        Returns an empty default config on any error.
        """
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f.read())
            if data is None:
                return cls()
            return cls.from_dict(data)
        except (IOError, yaml.YAMLError) as e:
            logger.error("Failed to load config from %s: %s", path, e)
            return cls()

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "TimevaultConfig":
        """Main entry point — load config from *config_path* or the default location.

        Returns an empty config if the file does not exist.
        """
        path = config_path or default_config_path()
        if not path.exists():
            return cls()
        return cls.from_file(path)
