# uv — Python Package & Project Manager

Source: https://docs.astral.sh/uv/ (guides/projects, guides/integration/fastapi)

`uv` is a single Rust-based tool from Astral that replaces `pip`, `pip-tools`,
`venv`, `virtualenv`, and `poetry` for day-to-day Python project work. It
manages the virtual environment, dependency resolution, lockfile, and Python
version all through one CLI.

## Initializing a project

```bash
# Standard project (creates a src/<pkg> layout, meant to be built/packaged)
uv init hello-world
cd hello-world

# Flat/unpackaged app project (typical for a FastAPI backend that isn't
# published as a library) — recommended for this app
uv init --no-package
```

`uv init` creates:
- `pyproject.toml` — project metadata + dependencies
- `.python-version` — pins the Python version used for the venv
- `README.md`
- `src/<package>/` (only for the packaged layout, omitted with `--no-package`)

## Adding dependencies

```bash
uv add fastapi --extra standard   # adds "fastapi[standard]"
uv add sqlalchemy
uv add "requests==2.31.0"         # pinned version
uv add --dev pytest ruff          # dev-only dependency group
uv remove requests
```

`uv add`/`uv remove` update both `pyproject.toml` and the `uv.lock` lockfile
automatically — no separate `pip freeze` step needed.

## Running things

```bash
uv run fastapi dev            # run inside the project's managed venv
uv run python script.py
uv run pytest
```

Before every `uv run`, uv checks that `uv.lock` is in sync with
`pyproject.toml` and the environment matches the lockfile; it re-resolves and
re-syncs automatically if not. This means you almost never need to manually
activate a virtualenv or run `pip install`.

`uv sync` does the same resolve/install step without running a command
afterward — useful in CI or Docker layers.

## Lockfile behavior

`uv.lock` is a cross-platform lockfile containing exact resolved versions
(and hashes) of every dependency, direct and transitive. Unlike
`pyproject.toml` (which expresses loose version constraints), `uv.lock` is
meant to be committed to version control so every machine/CI run gets
identical dependency versions.

```bash
uv lock                       # re-resolve without installing
uv lock --upgrade-package foo # bump a single package
uv sync --frozen              # install exactly what's locked, no re-resolve
```

## Virtual environment handling

uv creates and manages a `.venv/` directory in the project root
automatically the first time you run `uv add`, `uv sync`, or `uv run`. You
generally don't activate it yourself — `uv run <cmd>` runs `<cmd>` inside it.
If you do want to activate it manually (e.g. for editor integration):

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Unix
source .venv/bin/activate
```

## Replacing pip / venv / poetry with one tool

| Old tool                 | uv equivalent          |
|---------------------------|------------------------|
| `python -m venv .venv`    | automatic (via `uv add`/`uv run`) |
| `pip install X`           | `uv add X`             |
| `pip install -r req.txt`  | `uv add -r requirements.txt` or `uv pip install -r ...` (pip-compat mode) |
| `pip freeze > req.txt`    | `uv.lock` (auto-generated) |
| `poetry add/init/run`     | `uv add` / `uv init` / `uv run` |

uv also has a `uv pip` subcommand family that mimics pip's CLI directly for
gradual migration, but for new projects prefer the project-oriented commands
above (`uv init`, `uv add`, `uv run`).

## Typical FastAPI project workflow

```bash
uv init --no-package ai-interviewer-backend
cd ai-interviewer-backend
uv add fastapi --extra standard   # installs fastapi + uvicorn + other extras
uv add sqlalchemy
uv run fastapi dev                # starts dev server with reload
```

`uv run fastapi dev` resolves deps, syncs `.venv`, and launches the FastAPI
CLI dev server (built on uvicorn) — no manual venv activation required.

Minimal Dockerfile pattern (from the official uv+FastAPI guide):

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY . .
RUN uv sync --frozen --no-cache
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--port", "80"]
```
