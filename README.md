# Timeless-Py ⏳

> Snapshot what matters, remember how to rebuild the rest.

Time Machine-style personal backup orchestrated by Python & uv.

## Overview

Timeless-Py is a modern backup solution designed for macOS, providing:

- Hourly, daily, weekly deduplicated snapshots of user data
- Re-install manifest generation for applications and system packages
- Engine-agnostic approach with Restic, Borg, and Kopia support
- Client-side encryption (AES-256) with keys stored in Keychain
- Simple 10-minute setup: `brew install timeless-py` → `timeless init --wizard`

## Features

- **Snapshot Management**: Create, browse, and restore backups with ease
- **Retention Policies**: Define flexible retention policies (hourly/daily/weekly/monthly)
- **Manifest Generation**: Auto-generate reinstall manifests for your Mac software
- **Built-in Security**: Fully encrypted snapshots with secure key management
- **FUSE Integration**: Mount snapshots as regular volumes for easy browsing

## Installation

```bash
# Coming soon - once published
brew install timeless-py

# Initialize with wizard
timeless init --wizard
```

## Usage

```bash
# Create a backup
timeless backup

# Mount latest snapshot
timeless mount

# Restore a file or directory
timeless restore <snapshot> <path>

# List available snapshots
timeless snapshots

# Verify repository integrity
timeless check

# Reinstall software from manifests
timeless brew-replay
```

## Development

This project requires Python 3.11 or higher.

```bash
# Setup development environment
git clone https://github.com/rappdw/timeless.git
cd timeless
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linting and type checks
ruff check .
black --check .
isort --check .
mypy --strict .
```

## License

This project is licensed under Apache-2.0. See LICENSE file for more details.
