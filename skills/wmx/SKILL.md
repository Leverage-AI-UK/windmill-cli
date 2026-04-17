---
name: wmx
description: Windmill CLI for managing scripts, flows, resources, variables, jobs, schedules, apps. Use when interacting with Windmill via terminal commands.
triggers:
  - windmill
  - wmx
  - scripts
  - flows
  - resources
  - variables
  - jobs
  - schedules
  - apps
---

# wmx - Agent-Native Windmill CLI

Use the Windmill HTTP API directly via command line. Designed for both humans and AI coding agents.

## Command Groups

```
wmx scripts    # Deploy and run scripts
wmx flows      # Deploy and run flows
wmx resources  # Manage resources (credentials, configs)
wmx variables  # Manage variables (secrets, config values)
wmx jobs       # Inspect job history and wait on jobs
wmx queue      # View queued/running jobs
wmx schedules  # Create and manage cron schedules
wmx apps       # Manage Windmill apps
wmx docs       # Query Windmill documentation
wmx config     # Show resolved configuration
wmx whoami     # Check authentication
wmx doctor     # Debug configuration issues
```

## Global Flags

```
--base-url URL      Windmill instance URL
--workspace ID      Windmill workspace
--token TOKEN       User auth token
--json              Machine-friendly JSON output
--yes               Skip destructive confirmations
--quiet             Reduce stderr diagnostics
--verbose           Extra stderr diagnostics
--output-mode MODE  inline | auto | file (default: auto)
--output-file PATH  Write payload to specific file
--spill-dir DIR     Directory for auto-spilled output (default: .wmx-output/)
```

## Authentication

Set these environment variables (or use flags):

```bash
export WMX_BASE_URL="https://app.windmill.dev"
export WMX_WORKSPACE="your-workspace"
export WMX_TOKEN="your-token"
```

Fallback aliases: `WINDMILL_BASE_URL`, `WINDMILL_WORKSPACE`, `WINDMILL_TOKEN`

Verify with: `wmx whoami`

## Common Workflows

### List and Get

```bash
# List with filtering
wmx scripts list --path-start f/team/
wmx flows list --path-start f/team/
wmx resources list --type postgresql
wmx variables list --path-start u/me/

# Get single item
wmx scripts get f/team/send_report
wmx flows get f/team/daily_sync
wmx resources get u/me/db              # Values redacted by default
wmx variables get u/me/api_key         # Secrets redacted by default
```

### Create and Update

```bash
# Scripts (require --file and language inference)
wmx scripts create f/team/new_script --file ./script.py
wmx scripts update f/team/new_script --file ./script.py

# Flows (from YAML/JSON definition)
wmx flows create --file ./flow.yaml
wmx flows update f/team/daily_sync --file ./flow.yaml

# Resources (from YAML/JSON with value)
wmx resources create u/me/db --file ./db.json --type postgresql

# Variables
wmx variables create u/me/api_key --value "sk-..." --secret
wmx variables update u/me/api_key --value "sk-new..."

# Apps (standard low-code builder)
wmx apps create --file ./app.json
wmx apps update f/apps/my_app --file ./app.json

# Apps (raw React/Svelte full-code apps)
wmx apps create --file ./raw_app.yaml --raw
wmx apps update f/apps/my_raw_app --file ./raw_app.yaml --raw
```

### Delete (Requires --yes)

```bash
wmx scripts delete f/team/old_script --yes
wmx flows delete f/team/old_flow --yes
wmx resources delete u/me/old_resource --yes
wmx variables delete u/me/old_var --yes
```

### Running Scripts and Flows

```bash
# Run deployed script (async by default)
wmx scripts run f/team/send_report

# Run with arguments and wait for completion
wmx scripts run f/team/send_report --data '{"to":"user@example.com"}' --wait

# Run and stream logs
wmx scripts run f/team/send_report --data @args.json --wait --follow

# Same patterns for flows
wmx flows run f/team/daily_sync --data @payload.json --wait --follow
```

### Preview Execution (First-Class Feature)

Preview runs code directly on Windmill workers without deploying. **Defaults to --wait** (unlike run).

```bash
# Preview a local script file
wmx scripts preview ./scratch.py --data '{"x": 42}'

# Preview with arguments from file
wmx scripts preview ./script.py --data @test_args.json

# Preview a flow definition
wmx flows preview ./my_flow.yaml --data @input.json

# Fire-and-forget preview (unusual)
wmx scripts preview ./script.py --no-wait
```

### Job Management

```bash
# List recent jobs
wmx jobs list --per-page 20

# Get job details (includes result, logs, timing)
wmx jobs get <job-id>

# Get just logs
wmx jobs logs <job-id>

# Wait on a job you started earlier
wmx jobs wait <job-id> --follow --timeout 300
```

### Schedules

```bash
# List schedules
wmx schedules list

# Create from YAML (uses 6-field cron with seconds)
wmx schedules create --file ./schedule.yaml

# Get schedule details
wmx schedules get f/team/daily_schedule
```

### Apps

```bash
# List and get apps
wmx apps list
wmx apps get f/apps/dashboard

# Standard apps (low-code builder JSON export)
wmx apps create --file ./app.json
wmx apps update f/apps/dashboard --file ./app.json

# Raw apps (React/Svelte full-code apps)
# Raw apps require esbuild (npm install -g esbuild)
wmx apps create --file ./raw_app.yaml --raw
wmx apps update f/apps/my_react_app --file ./raw_app.yaml --raw

# Delete
wmx apps delete f/apps/old_app --yes
```

#### Raw App File Structure

Raw apps use YAML/JSON with source files that get bundled via esbuild:

```yaml
path: f/apps/my_react_app
summary: My React App
value:
  files:
    /index.tsx: |
      import { render } from './App';
      render(document.getElementById('root'));
    /App.tsx: |
      import React from 'react';
      export function render(el) {
        // React app code
      }
    /index.css: |
      .container { padding: 1rem; }
  data:
    schema: app1
    tables: []
policy:
  triggerables: {}
```

## Input Patterns

The `--data` flag accepts three formats:

```bash
# Inline JSON
--data '{"key": "value"}'

# From file
--data @args.json

# From stdin
echo '{"key": "value"}' | wmx scripts run f/team/script --data @-
```

## Critical Gotchas

### 1. Non-Interactive Mode

Destructive operations require `--yes` in scripts and pipelines:

```bash
# This hangs in CI/agents - missing --yes
wmx scripts delete f/team/script  # ERROR: requires confirmation

# Correct
wmx scripts delete f/team/script --yes
```

### 2. Secret Values Are Redacted by Default

Variables and resources hide sensitive values unless you explicitly reveal:

```bash
# Default: value is "[REDACTED]"
wmx variables get u/me/api_key

# Reveal plaintext
wmx variables get u/me/api_key --reveal

# Get encrypted form
wmx variables get u/me/api_key --encrypted

# Get just the value (requires --reveal or --encrypted for secrets)
wmx variables get u/me/api_key --value-only --reveal
```

See: [secrets-and-resources.md](references/secrets-and-resources.md)

### 3. Preview vs Run Defaults

- `wmx scripts preview` defaults to `--wait` (blocks until done)
- `wmx scripts run` defaults to `--no-wait` (async, returns job ID)
- `wmx flows preview` defaults to `--wait`
- `wmx flows run` defaults to `--no-wait`

### 4. Output Auto-Spilling

Large outputs (>128KB) are automatically written to `.wmx-output/` instead of flooding stdout. Use `--output-mode inline` to force stdout.

See: [output-modes.md](references/output-modes.md)

### 5. Pagination Defaults

List commands return 50 items by default. Use `--page` and `--per-page` for more:

```bash
wmx scripts list --per-page 100 --page 2
```

## Quick Debugging

```bash
# Check configuration resolution
wmx doctor

# Verify authentication
wmx whoami

# See what would be sent without executing
wmx --verbose scripts list 2>&1 | head
```
