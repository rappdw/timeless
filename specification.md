# Timeless-Py ⏳  –  Time Machine-style personal backup orchestrated by Python & uv

> **Tag line:** “Snapshot what matters, remember how to rebuild the rest.”

---

## 1. Vision

1. Hourly → daily → weekly deduplicated snapshots of *user data* (Home folder, selected volumes).
2. Skip OS files and application bundles; instead, generate a **re-install manifest** (`Brewfile`, `applications.json`, `mas.txt`).
3. Engine-agnostic driver; first target **Restic**, optional **Borg** / **Kopia**.
4. Entirely client-side encryption (AES-256) with keys stored in Keychain.
5. 10-min install path: `brew install timeless-py` → `timeless init --wizard`.

---

## 2. Success Criteria

| Metric                              | Goal                  |
| ----------------------------------- | --------------------- |
| Backup 20 GB delta (NVMe SSD→USB-C) | ≤ 120 s               |
| Manifest generation                 | ≤ 15 s                |
| Restore single file via FUSE        | ≤ 3 s                 |
| Unit-test coverage (statements)     | ≥ 90 %                |
| Lint errors                         | 0 (ruff, mypy strict) |

---

## 3. Functional Requirements

### 3.1 CLI Commands

| Command                              | Description                                                                                     |
| ------------------------------------ | ----------------------------------------------------------------------------------------------- |
| `timeless init`                      | Interactive wizard: choose engine/target, store repo key in Keychain, create launchd plist.     |
| `timeless backup`                    | Run snapshot + retention pruning + manifest refresh.                                            |
| `timeless mount`                     | Mount selected snapshot at `/Volumes/Timeless`.                                                 |
| `timeless restore <snapshot> <path>` | Copy a file/dir from snapshot to working dir.                                                   |
| `timeless snapshots --json`          | Machine-readable list of snapshots (ISO timestamps).                                            |
| `timeless check`                     | Invoke engine integrity check, report via macOS notification center.                            |
| `timeless brew-replay`               | Reinstall software from manifests onto clean Mac (calls Brew, MAS, direct dmg download helper). |

### 3.2 Retention Policy DSL

```yaml
policy:
  hourly: 24          # keep last 24
  daily: 30
  weekly: 12
  monthly: forever
exclude:
  - "/System/**"
  - "/Applications/**"
  - "/opt/homebrew/**"
  - "*.tmp"
```

### 3.3 Manifest Generation

* **Homebrew**:

  ```bash
  brew bundle dump --describe --file $CACHE/Brewfile
  ```
* **Applications**:

  ```bash
  system_profiler SPApplicationsDataType -json > applications.json
  ```
* **MAS** (optional):

  ```bash
  mas list > mas.txt
  ```

Manifests are tagged (`type:manifest`) so they live in Restic but remain tiny.

---

## 4. Non-Functional Requirements

* **Language**: Python 3.11+ (test under 3.11 & 3.12).
* **Project Management**: uv (init, lock, sync, run, build, publish).
* **Packaging**: wheel & zipapp via `uv build`.
* **Mac Support**: Ventura (13) → Sequoia (15).
* **Memory Budget**: ≤ 600 MB during large prune.
* **Security**: All subprocess calls with sanitized env (`env -i`); temp files in `SecureTemporaryDirectory`.

---

## 5. High-Level Architecture

```
timeless_py/
├── cli.py          # Typer + uv-driven entry
├── engine/         # __init__.py declares BaseEngine
│   ├── restic.py   # subprocess wrapper + JSON parsing
│   ├── borg.py
│   └── kopia.py
├── scheduler/      # launchd plist template + loader
├── manifest/       # brew.py, apps.py, mas.py
├── keychain.py     # wrapper over python-keyring
├── retention.py    # policy parser + evaluator
├── notifier.py     # pync notifications
└── tests/
```

---

## 6. External Dependencies

| Purpose             | Package                              |
| ------------------- | ------------------------------------ |
| CLI                 | `typer[all]`                         |
| Keychain            | `keyring`, `keyrings.alt`            |
| Restic JSON Parsing | `orjson`                             |
| Scheduling Helpers  | `pycron`, `python-launchd`           |
| Notifications       | `pync`                               |
| Packaging           | `shiv`, `uv`                         |
| Lint / Format       | `ruff`, `black`, `isort`, `mypy`     |
| Testing             | `pytest`, `pytest-cov`, `hypothesis` |

---

## 7. Milestones

1. **M0 (1 day)** – repo bootstrap (`uv init`, GitHub Actions, CLI stub).
2. **M1 (4 days)** – Restic engine + retention + exclude patterns + tests.
3. **M2 (3 days)** – Manifest generators & replay helpers.
4. **M3 (2 days)** – launchd installer & pync notifications.
5. **M4 (2 days)** – Kopia engine & FUSE mount wrapper.
6. **M5 (stretch)** – Minimal SwiftUI status-bar wrapper.

---

## 8. Risks & Mitigations

| Risk                             | Mitigation                                                                   |
| -------------------------------- | ---------------------------------------------------------------------------- |
| Restic JSON output changes       | Pin minimum Restic version; parse via strict dataclass schema.               |
| Photos Library churn             | Option to treat `.photoLibrary` as monolithic bundle (exclude fine-grained). |
| Brew path variations (Intel/ARM) | Detect `brew --prefix` at runtime for manifest restore.                      |

---

## 9. License

Apache-2.0; include upstream licenses under `third_party/`.

