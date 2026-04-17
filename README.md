# `wmx`

`wmx` is an agent-native Windmill CLI built directly on the Windmill HTTP API. It targets the practical surface of the Windmill MCP server without using MCP, and it treats remote preview execution as a first-class workflow.

The CLI is designed for:

- humans working in a terminal
- AI coding agents exploring command surfaces with `--help`
- sandboxed environments using normal Windmill user tokens

## Why this exists

Windmill MCP is useful, but MCP forces tool inventory and descriptions into model context up front. `wmx` keeps the interaction surface in the shell instead:

- command discovery is progressive through `--help`
- large command surfaces stay out of model context
- the CLI works in local terminals and sandboxed shells
- it can be packaged and reused across repositories

## Install

Install from GitHub (works anywhere with Python 3.10+):

```bash
pip install git+https://github.com/Leverage-AI-UK/windmill-cli.git
```

For local development:

```bash
git clone https://github.com/Leverage-AI-UK/windmill-cli.git
cd windmill-cli
python -m pip install -e .[dev]
```

## Quick Start

Once installed, set your Windmill credentials as environment variables:

```bash
export WMX_BASE_URL="https://your-windmill-instance.com"
export WMX_WORKSPACE="your-workspace"
export WMX_TOKEN="your-api-token"
```

Then run from anywhere:

```bash
wmx whoami          # Check connection
wmx scripts list    # List scripts
wmx flows list      # List flows
```

For persistent setup, add the exports to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.).

### Using in E2B or other sandboxes

```python
from e2b import Sandbox

sandbox = Sandbox(
    template="your-template",
    env_vars={
        "WMX_BASE_URL": "https://your-windmill-instance.com",
        "WMX_WORKSPACE": "your-workspace",
        "WMX_TOKEN": os.environ["WMX_TOKEN"],
    }
)

# Install and use
sandbox.commands.run("pip install git+https://github.com/Leverage-AI-UK/windmill-cli.git")
sandbox.commands.run("wmx scripts list")
```

## Configuration

Flags override environment variables.

| Environment Variable | Description |
|---------------------|-------------|
| `WMX_BASE_URL` | Windmill instance URL (e.g., `https://app.windmill.dev`) |
| `WMX_WORKSPACE` | Workspace ID |
| `WMX_TOKEN` | User API token |

Fallback variables are also supported: `WINDMILL_BASE_URL`, `WINDMILL_WORKSPACE`, `WINDMILL_TOKEN`

Verify your config:

```bash
wmx config show   # Show resolved configuration
wmx whoami        # Test connection
wmx doctor        # Full diagnostic
```

## Command shape

The top-level groups are plural for consistency and discoverability:

- `scripts`
- `flows`
- `resources`
- `variables`
- `jobs`
- `queue`
- `schedules`
- `apps`
- `docs`
- `config`

Examples:

```bash
wmx scripts list
wmx scripts get f/team/send_report
wmx scripts create f/team/send_report --file ./send_report.py --language python3
wmx scripts run f/team/send_report --data @args.json --wait
wmx scripts preview ./scratch.py --data '{"customer_id":"123"}'
```

```bash
wmx flows list
wmx flows get f/team/daily_sync
wmx flows create --file ./daily_sync.flow.yaml
wmx flows update f/team/daily_sync --file ./daily_sync.flow.yaml
wmx flows run f/team/daily_sync --data @payload.json --wait
```

```bash
wmx resources list
wmx resources get u/me/postgres
wmx resources get u/me/postgres --reveal --value-only
wmx resources create u/me/postgres --file ./postgres.resource.json
```

```bash
wmx variables list
wmx variables get u/me/my_secret --metadata-only
wmx variables get u/me/my_secret --reveal --value-only
printf 'super-secret' | wmx variables create u/me/my_secret --secret --value-from-stdin
```

```bash
wmx jobs list
wmx queue list
wmx jobs get 7f6b3e4d-...
wmx jobs wait 7f6b3e4d-... --follow
```

```bash
wmx schedules list
wmx schedules get f/team/nightly
wmx schedules create --file ./nightly.schedule.yaml
```

```bash
wmx apps create --file ./app.json
wmx apps update f/apps/my_app --file ./app.json
```

```bash
wmx docs query "How do I create a flow?"
```

## Preview runtime

Preview execution uses Windmill preview APIs directly instead of creating temporary deployed artifacts.

- script preview: `/api/w/{workspace}/jobs/run/preview`
- flow preview: `/api/w/{workspace}/jobs/run/preview_flow`
- job completion polling: `/api/w/{workspace}/jobs_u/completed/get_result_maybe/{id}`
- log polling: `/api/w/{workspace}/jobs_u/getupdate/{id}`

This means preview code executes inside a real Windmill runtime with the same contextual capabilities Windmill normally exposes during runs, including variables, resources, and contextual environment variables according to the authenticated user's permissions.

## Large output handling

This CLI is explicitly built for agents that should not always dump large results into context.

Global output controls:

- `--json`: stable machine-readable stdout
- `--output-mode inline|auto|file`: choose inline output, automatic spill, or forced file output
- `--output-file PATH`: choose the exact destination file
- `--spill-dir PATH`: directory for automatic spills
- `--spill-threshold-bytes N`: auto-spill threshold, default `131072`

Default behavior is `--output-mode auto`, so large payloads are written to the filesystem and stdout only contains a small manifest with the saved path.

Examples:

```bash
wmx --json jobs get 7f6b3e4d-...
```

```bash
wmx --json --output-mode file --output-file ./job.json jobs get 7f6b3e4d-...
```

```bash
wmx --json --spill-dir /tmp/wmx-output resources get u/me/postgres --reveal
```

## Security model

`wmx` follows Windmill's permission model. It does not try to bypass user permissions or emulate elevated access.

Security defaults:

- secrets are never shown by default
- resource values are redacted by default
- variable secrets require explicit `--reveal` or `--encrypted`
- destructive commands require confirmation unless `--yes` is passed
- auth headers are handled in-process and are not emitted in normal output

See [docs/security.md](docs/security.md) for the full model.

## MCP capability mapping

| Windmill MCP capability | `wmx` command surface |
| --- | --- |
| scripts | `wmx scripts ...` |
| flows | `wmx flows ...` |
| resources | `wmx resources ...` |
| variables | `wmx variables ...` |
| jobs | `wmx jobs ...`, `wmx queue ...` |
| schedules | `wmx schedules ...` |
| apps | `wmx apps ...` |
| docs query | `wmx docs query ...` |
| preview runtime | `wmx scripts preview ...`, `wmx flows preview ...` |

## Repo layout

```text
src/wmx/
  cli.py
  config.py
  errors.py
  output.py
  state.py
  utils.py
  client/
  commands/
tests/
docs/
```

## Tests

Default test suite:

```bash
PYTHONPATH=src pytest
```

Live smoke test:

- set `WMX_BASE_URL`
- set `WMX_WORKSPACE`
- set `WMX_TOKEN`
- run `PYTHONPATH=src pytest tests/integration/test_live_smoke.py`

## Release notes

This repo is packaged as `windmill-agent-cli` and exposes the `wmx` console entrypoint.

Minimal release flow:

1. Run `PYTHONPATH=src pytest`
2. Build with `python -m build`
3. Publish with your preferred package workflow

## Docs

- [Architecture](docs/architecture.md)
- [Command design](docs/command-design.md)
- [Security model](docs/security.md)

