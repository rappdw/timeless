# Timeless-Py – Multi-Agent Contribution Guide

<!-- Keep this file at project root so every coding agent sees it immediately -->

## 1. Agent Roles

| Agent           | Primary Duties                                                                         |
| --------------- | -------------------------------------------------------------------------------------- |
| **Architect**   | Interpret `specification.md`, run `uv init`, scaffold project, CI config.              |
| **Implementer** | Code one module at a time (`engine/restic.py`, etc.), write pytest & hypothesis tests. |
| **Reviewer**    | Run `pytest`, `ruff`, `mypy --strict`; request style/logic changes.                    |
| **Doc-Writer**  | Maintain `README.md`, examples, auto-gen man-page via `typer --help`.                  |
| **Release-Bot** | Bump SemVer, `uv build`, attach wheel & zipapp, `uv publish`, Homebrew PR.             |

> Commit messages must start with `<!-- agent: <role>, <date> -->`.

---

## 2. Branch & PR Workflow

1. **One-module-per-PR** rule.
2. Every PR triggers GitHub Actions:

   * `ruff check --fix .` (fail on remaining issues)
   * `black --check .`
   * `isort --check .`
   * `mypy --strict`
   * `pytest --cov=timeless_py` (coverage ≥ 90 %)
3. ≥ 1 **Reviewer** approval; squash-merge to `main`.

---

## 3. Coding Conventions

| Topic          | Rule                                                              |
| -------------- | ----------------------------------------------------------------- |
| **Formatting** | `black` default, `isort` (profile=black)                          |
| **Imports**    | Absolute; no wildcard imports                                     |
| **Typing**     | All public functions fully typed; `mypy --strict` passes          |
| **Subprocess** | Use `subprocess.run([...], check=True, text=True, env=clean_env)` |
| **Logging**    | Standard `logging` with `--json` flag for JSON lines              |
| **Temp Paths** | `tempfile.TemporaryDirectory(dir="/private/var/tmp", mode=0o700)` |

---

## 4. Security Rules

* **Secrets** only via `keyring` helpers.
* No writes outside user’s `$HOME` except `/Library/LaunchDaemons` plist (requires `sudo`).
* All shell commands use fixed arg-lists and sanitized env.

---

## 5. Directory Ownership Matrix

| Path                 | Owner                 |
| -------------------- | --------------------- |
| `cli.py`             | Architect→Implementer |
| `engine/*`           | Implementer           |
| `manifest/*`         | Implementer           |
| `scheduler/*`        | Implementer           |
| `docs/`, `README.md` | Doc-Writer            |

---

## 6. Prompt Engineering Tips

* **Implementer agents**: read relevant `specification.md` section *before* each prompt.
* Use iterative approach: “Generate skeleton with type stubs” → “Fill body” → “Write tests” → “Run ruff/pytest”.
* When engine behavior is ambiguous, inject `# TODO: confirm with Reviewer`.

---

## 7. Release Procedure (Release-Bot)

1. Bump version in `pyproject.toml`.
2. `uv build` → attach wheel & zipapp to GitHub Release.
3. `uv publish` to PyPI.
4. `brew bump-formula-pr`.

---

## 8. Attribution

This project orchestrates third-party tools:

* Restic (BSD-2)
* BorgBackup (BSD-2)
* Kopia (Apache-2.0)

Include original licenses under `third_party/`.

