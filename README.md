# TimeVault

> Snapshot what matters, remember how to rebuild the rest.

Time Machine-style personal backup orchestrated by Python & uv.

## Overview

TimeVault is a modern backup solution for macOS and Linux, providing:

- Hourly, daily, weekly deduplicated snapshots of user data
- Re-install manifest generation for applications and system packages
- Restic-backed with client-side encryption (AES-256) and Keychain/keyring support
- Persistent configuration via `~/.config/timevault/config.yaml`

## Quick Start

```bash
# Run directly (no install needed)
uvx timevault init --repo /path/to/repo --password <pw>
uvx timevault backup

# Or install globally
uv tool install timevault
timevault backup
```

## Usage

```bash
# Initialize repository and store credentials in keyring
timevault init --repo /path/to/repo --password <pw>

# Run a backup (uses config file or platform defaults)
timevault backup

# Back up specific paths
timevault backup ~/Documents ~/Projects

# Back up with a retention policy file
timevault backup --policy policy.yaml

# Mount latest snapshot as a FUSE volume
timevault mount

# Restore a file or directory
timevault restore <snapshot> <path> --target /tmp/restore

# List available snapshots
timevault snapshots

# Verify repository integrity
timevault check

# Reinstall software from manifests (macOS)
timevault brew-replay
```

## Configuration

Create `~/.config/timevault/config.yaml` to persist settings:

```yaml
repo: "sftp:user@host:/backups/timevault"
mount_path: "/Volumes/TimeVault"

backup_paths:
  - path: "~"
    tag: "home"
    exclude:
      - "~/Library"
  - path: "~/Library"
    tag: "library"
    exclude:
      - "~/Library/CloudStorage"
      - "~/Library/Caches"

exclude_patterns:
  - ".DS_Store"
  - "*.tmp"

retention:
  hourly: 24
  daily: 7
  weekly: 4
  monthly: 12
  yearly: 3
```

See `examples/` for macOS and Linux example configs.

**Precedence**: CLI flags > environment variables > config file > keyring/defaults.

## Features

- **Snapshot Management**: Create, browse, and restore backups
- **Retention Policies**: Flexible YAML-based retention (hourly/daily/weekly/monthly/yearly)
- **Manifest Generation**: Auto-generate reinstall manifests (Homebrew/MAS on macOS; dpkg/rpm/snap/flatpak on Linux)
- **Exclude Patterns**: Global excludes in config, per-path excludes, and policy-file excludes are merged
- **FUSE Integration**: Mount snapshots as regular volumes for browsing
- **Keyring Integration**: Repository credentials stored securely in the system keyring

## Development

Requires Python 3.11+.

```bash
git clone https://github.com/rappdw/timeless.git
cd timeless
uv venv && uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format --check .

# Type check
uv run mypy --strict .
```

## License

Apache-2.0. See LICENSE for details.
