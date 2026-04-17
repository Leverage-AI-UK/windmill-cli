# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`wmx` is an agent-native Windmill CLI that uses the Windmill HTTP API directly. It is designed for both humans in terminals and AI coding agents exploring commands via `--help`. The CLI keeps command surfaces out of model context through progressive discovery instead of MCP's upfront tool inventory.

## Commands

```bash
# Install for development
python -m pip install -e .[dev]

# Run tests (PYTHONPATH required)
PYTHONPATH=src pytest

# Run a single test file
PYTHONPATH=src pytest tests/unit/test_config.py

# Run a single test
PYTHONPATH=src pytest tests/unit/test_config.py::test_function_name -v

# Live integration tests (requires WMX_BASE_URL, WMX_WORKSPACE, WMX_TOKEN)
PYTHONPATH=src pytest tests/integration/test_live_smoke.py

# Build package
python -m build
```

## Architecture

### Layer Structure

1. **CLI layer** (`src/wmx/cli.py`): Root Typer app with global flags (auth, output mode, spill controls). Command groups registered from `src/wmx/commands/`.

2. **Config layer** (`src/wmx/config.py`): Resolves config from flags → `WMX_*` env vars → `WINDMILL_*` fallbacks. Config stays partial until auth is actually needed.

3. **HTTP layer** (`src/wmx/client/http.py`): Wraps `httpx.Client` with URL normalization, bearer auth, and CLI-oriented exception mapping.

4. **Domain API wrappers** (`src/wmx/client/*.py`): Thin wrappers around Windmill OpenAPI routes (scripts, flows, resources, variables, jobs, schedules, apps, docs, auth).

5. **Output layer** (`src/wmx/output.py`): Handles JSON/human rendering and automatic spill-to-file for large payloads (default threshold 128KB).

### Key Design Patterns

- **Preview as first-class**: Script/flow preview uses Windmill's preview APIs directly (`/jobs/run/preview`, `/jobs/run/preview_flow`) rather than creating temporary deployments.

- **Agent-safe output**: `--output-mode auto` spills large payloads to `.wmx-output/` instead of dumping into stdout. This keeps agent context clean.

- **Secrets redacted by default**: Variables and resources require `--reveal` to show sensitive values. `--value-only` requires `--reveal`.

- **Destructive operations**: Require `--yes` flag. Non-interactive environments error instead of hanging on confirmation.

### State Flow

`AppState` (in `src/wmx/state.py`) holds resolved config, output manager, and confirmation flag. It's attached to `typer.Context.obj` in the main callback and retrieved via `get_state(ctx)` in commands.

### Error Handling

`WmxError` exceptions (`src/wmx/errors.py`) carry exit codes and are caught at the CLI boundary. Commands don't print stack traces for expected failures.

## Test Structure

- `tests/unit/`: Config, output mechanics, CLI help, variable/preview/job behavior with mocks
- `tests/integration/`: Live smoke tests gated by environment variables
- Tests use `CliRunner` from Typer with `mix_stderr=False`
