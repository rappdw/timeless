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
| `timeless mount`                     | Mount the repository for browsing snapshots at `/Volumes/Timeless`.                             |
| `timeless restore <snapshot> <path>` | Copy a file/dir from snapshot to working dir.                                                   |
| `timeless snapshots --json`          | Machine-readable list of snapshots (ISO timestamps).                                            |
| `timeless check`                     | Invoke engine integrity check, report via macOS notification center.                            |
| `timeless brew-replay`               | Reinstall software from manifests onto clean Mac (calls Brew, MAS, direct dmg download helper). |

### 3.2 Retention Policy DSL

```yaml
hourly: 24            # keep last 24 hourly snapshots
daily: 30
weekly: 12
monthly: 12
yearly: 3
exclude_patterns:
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

Manifests are backed up as snapshots tagged `manifest`, keeping them small and easy to locate.

---

## 4. Non-Functional Requirements

* **Language**: Python 3.11+ (test under 3.11 & 3.12).
* **Project Management**: uv (init, lock, sync, run, build, publish).
* **Packaging**: wheels (via uv/pip); optional zipapp via `shiv` (dev).
* **Mac Support**: Ventura (13) → Sequoia (15).
* **Memory Budget**: ≤ 600 MB during large prune.
* **Security**: Credentials stored in Keychain via `keyring`; Restic commands receive `RESTIC_*` via environment (parent env inherited); manifests generated in `tempfile.TemporaryDirectory`. Additional env-hardening is planned.

---

## 5. High-Level Architecture

```
timeless_py/
├── cli.py              # Typer CLI entrypoint
├── engine/             # BaseEngine + Restic engine
│   ├── __init__.py     # BaseEngine, Snapshot dataclass
│   └── restic.py       # subprocess wrapper + JSON parsing; repo existence checks; exit code 3 handling
├── manifest/           # software manifests + replay
│   ├── brew.py
│   ├── apps.py
│   ├── mas.py
│   └── replay.py
├── retention.py        # policy parser + evaluator (hourly/daily/weekly/monthly/yearly, exclude_patterns)
└── tests/
```

---

## 6. External Dependencies

| Purpose             | Package                              |
| ------------------- | ------------------------------------ |
| CLI                 | `typer`                              |
| Keychain            | `keyring`, `keyrings.alt`            |
| JSON (Restic)       | `orjson`                             |
| YAML                | `pyyaml`                             |
| Console / Logging   | `rich`                               |
| Scheduling Helpers  | `pycron`, `launchd`                  |
| Notifications       | `pync`                               |
| Dev Packaging       | `shiv`                               |
| Lint / Format       | `ruff`, `black`, `isort`, `mypy`     |
| Testing             | `pytest`, `pytest-cov`, `hypothesis` |

---

## 7. Milestones

• **Completed**
1. **M0** – Repository bootstrap (`uv init`, GitHub Actions, CLI stub).
2. **M1** – Restic engine, retention evaluator, exclude patterns, tests.
3. **M2** – Manifest generators (Brew, Apps, MAS) & replay helpers.

• **Upcoming**
4. **M3** – launchd installer & pync notifications.
5. **M4** – Additional engines (Borg/Kopia). Repository mount exists via Restic (`timeless mount`).
6. **M5 (stretch)** – Minimal SwiftUI status-bar wrapper.

---

## 8. Risks & Mitigations

| Risk                             | Mitigation                                                                   |
| -------------------------------- | ---------------------------------------------------------------------------- |
| Restic JSON output changes       | Pin minimum Restic version; parse via strict dataclass schema.               |
| Photos Library churn             | Option to treat `.photoLibrary` as monolithic bundle (exclude fine-grained). |
| Brew path variations (Intel/ARM) | Detect `brew --prefix` at runtime for manifest restore.                      |
| Restic exit code 3 (unreadable files) | Treat as warning in backup flow; log details; continue processing. Implemented in `ResticEngine.backup()`. |

---

## 9. License

Apache-2.0; include upstream licenses under `third_party/`.

