"""
Tests for the config module.
"""

import os
from pathlib import Path
from unittest.mock import patch

from timeless_py.config import (
    RetentionConfig,
    TimevaultConfig,
    default_config_path,
)


def test_default_config_path() -> None:
    """default_config_path falls back to ~/.config/timevault/config.yaml."""
    env = {"HOME": str(Path.home())}
    with patch.dict(os.environ, env, clear=True):
        result = default_config_path()
        assert result == Path.home() / ".config" / "timevault" / "config.yaml"


def test_default_config_path_xdg() -> None:
    """default_config_path respects $XDG_CONFIG_HOME."""
    with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}):
        result = default_config_path()
        assert result == Path("/custom/config/timevault/config.yaml")


def test_missing_file_returns_defaults(tmp_path: Path) -> None:
    """Loading a non-existent file returns an empty config."""
    cfg = TimevaultConfig.load(tmp_path / "nonexistent.yaml")
    assert cfg.repo is None
    assert cfg.mount_path is None
    assert cfg.backup_paths == []
    assert cfg.exclude_patterns == []
    assert cfg.retention == RetentionConfig()


def test_empty_file_returns_defaults(tmp_path: Path) -> None:
    """An empty YAML file returns an empty config."""
    p = tmp_path / "config.yaml"
    p.write_text("")
    cfg = TimevaultConfig.from_file(p)
    assert cfg.repo is None
    assert cfg.backup_paths == []


def test_full_config_parsing(tmp_path: Path) -> None:
    """A fully-populated config file is parsed correctly."""
    p = tmp_path / "config.yaml"
    p.write_text("""\
repo: "sftp:user@host:/backups/timevault"
mount_path: "/Volumes/TimeVault"
backup_paths:
  - path: "~/Documents"
    tag: "documents"
  - path: "~/Projects"
    tag: "projects"
    exclude:
      - "*/node_modules"
      - "*/.venv"
exclude_patterns:
  - "*.tmp"
  - ".DS_Store"
retention:
  hourly: 12
  daily: 5
  weekly: 2
  monthly: 6
  yearly: 1
""")
    cfg = TimevaultConfig.from_file(p)
    assert cfg.repo == "sftp:user@host:/backups/timevault"
    assert cfg.mount_path == "/Volumes/TimeVault"
    assert len(cfg.backup_paths) == 2
    assert cfg.backup_paths[0].tag == "documents"
    assert cfg.backup_paths[1].exclude == ["*/node_modules", "*/.venv"]
    assert cfg.exclude_patterns == ["*.tmp", ".DS_Store"]
    assert cfg.retention.hourly == 12
    assert cfg.retention.daily == 5
    assert cfg.retention.weekly == 2
    assert cfg.retention.monthly == 6
    assert cfg.retention.yearly == 1


def test_backup_paths_with_tilde_expansion(tmp_path: Path) -> None:
    """Paths with ~ are expanded."""
    p = tmp_path / "config.yaml"
    p.write_text("""\
backup_paths:
  - path: "~/Documents"
    tag: "docs"
""")
    cfg = TimevaultConfig.from_file(p)
    assert len(cfg.backup_paths) == 1
    assert cfg.backup_paths[0].path == Path.home() / "Documents"


def test_backup_paths_invalid_entry_skipped(tmp_path: Path) -> None:
    """Entries without a 'path' key are skipped."""
    p = tmp_path / "config.yaml"
    p.write_text("""\
backup_paths:
  - tag: "no-path"
  - path: "~/valid"
    tag: "ok"
  - "just a string"
""")
    cfg = TimevaultConfig.from_file(p)
    assert len(cfg.backup_paths) == 1
    assert cfg.backup_paths[0].tag == "ok"


def test_exclude_patterns_parsing(tmp_path: Path) -> None:
    """Global exclude patterns are parsed as a list of strings."""
    p = tmp_path / "config.yaml"
    p.write_text("""\
exclude_patterns:
  - "*.log"
  - "*.bak"
""")
    cfg = TimevaultConfig.from_file(p)
    assert cfg.exclude_patterns == ["*.log", "*.bak"]


def test_retention_partial(tmp_path: Path) -> None:
    """Partial retention config leaves unset fields as None."""
    p = tmp_path / "config.yaml"
    p.write_text("""\
retention:
  daily: 14
  yearly: 5
""")
    cfg = TimevaultConfig.from_file(p)
    assert cfg.retention.hourly is None
    assert cfg.retention.daily == 14
    assert cfg.retention.weekly is None
    assert cfg.retention.monthly is None
    assert cfg.retention.yearly == 5


def test_invalid_yaml_returns_defaults(tmp_path: Path) -> None:
    """Malformed YAML returns an empty config instead of raising."""
    p = tmp_path / "config.yaml"
    p.write_text(": : : [invalid yaml")
    cfg = TimevaultConfig.from_file(p)
    assert cfg.repo is None
    assert cfg.backup_paths == []


def test_from_dict_non_dict() -> None:
    """from_dict with a non-dict value returns defaults."""
    cfg = TimevaultConfig.from_dict("not a dict")  # type: ignore[arg-type]
    assert cfg.repo is None


def test_load_uses_default_path(tmp_path: Path) -> None:
    """load() without arguments uses default_config_path()."""
    with patch(
        "timeless_py.config.default_config_path", return_value=tmp_path / "nope.yaml"
    ):
        cfg = TimevaultConfig.load()
    assert cfg.repo is None
