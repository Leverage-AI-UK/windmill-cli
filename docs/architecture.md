# Architecture

## Goals

The architecture is shaped around four constraints:

- use Windmill's HTTP API directly rather than shelling out to `wmill`
- stay discoverable for humans and agents through a clean CLI tree
- keep sensitive defaults safe
- support real remote preview execution without persistence hacks

## Layers

### CLI layer

`src/wmx/cli.py` defines the root Typer application and the global runtime options:

- auth/config flags
- output mode selection
- spill-to-file controls
- root commands such as `whoami`, `doctor`, and `config show`

Command groups live in `src/wmx/commands/`.

### Config layer

`src/wmx/config.py` resolves configuration from:

1. explicit flags
2. `WMX_*` environment variables
3. `WINDMILL_*` compatibility aliases

Resolution remains partial until a command actually needs authenticated access. That allows `wmx config show` and help output to work without forcing auth values to exist.

### HTTP layer

`src/wmx/client/http.py` wraps `httpx.Client` and centralizes:

- API base URL normalization
- bearer token headers
- JSON/text helpers
- HTTP error mapping into CLI-oriented exceptions

The CLI uses concrete route wrappers rather than shelling out to another CLI or building opaque generic requests at the command layer.

### Domain API wrappers

Each major Windmill surface has a small wrapper:

- `scripts.py`
- `flows.py`
- `resources.py`
- `variables.py`
- `jobs.py`
- `schedules.py`
- `apps.py`
- `docs.py`
- `auth.py`

These wrappers map closely to the OpenAPI routes, which keeps the command layer readable and the tests straightforward.

### Output layer

`src/wmx/output.py` owns stdout/stderr behavior:

- JSON or human rendering
- stable JSON serialization
- automatic spill-to-file for large payloads
- explicit file output support

This is the main agent-specific layer. It keeps bulky payloads out of context when they exceed the configured threshold.

## Preview strategy

Preview is implemented as a first-class feature, not as a temp deployment workflow.

Script preview:

- submit preview job with `/jobs/run/preview`
- poll `/jobs_u/getupdate/{id}` for incremental logs when `--follow` is enabled
- poll `/jobs_u/completed/get_result_maybe/{id}` until completion

Flow preview:

- submit preview job with `/jobs/run/preview_flow`
- use the same waiting/log polling path as normal jobs

This design preserves Windmill runtime semantics:

- variables and resources are resolved by Windmill
- permissions come from the authenticated user/token
- preview code runs as a real Windmill job

## Error model

Errors are converted into CLI-first exceptions with deterministic exit codes:

- configuration failures
- permission/auth failures
- not-found responses
- destructive-action confirmation failures
- job execution failures

The command layer does not print stack traces for normal expected failures.

## Testing approach

The test suite is split into:

- unit tests for config and output mechanics
- CLI tests for help and secret handling
- mocked wait/poll tests for preview/job behavior
- optional live integration smoke tests gated by env vars

This keeps the default suite fast while still covering the agent-facing contract.

