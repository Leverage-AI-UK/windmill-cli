# Output Modes

wmx provides multiple output modes to handle different use cases, from human-readable tables to machine-friendly JSON, with automatic handling of large payloads.

## JSON Mode

Use `--json` for machine-parseable output:

```bash
# Human-readable table (default)
wmx scripts list

# JSON array
wmx scripts list --json

# JSON single object
wmx scripts get f/team/script --json
```

JSON mode outputs to stdout, suitable for piping to `jq`:

```bash
wmx scripts list --json | jq '.[].path'
wmx jobs get <job-id> --json | jq '.result'
```

## Output Mode

The `--output-mode` flag controls where output goes:

| Mode | Behavior |
|------|----------|
| `inline` | Always print to stdout, regardless of size |
| `auto` | Print to stdout unless payload exceeds threshold, then spill to file |
| `file` | Always write to file, never print to stdout |

Default: `auto`

### Auto Mode (Default)

```bash
# Small output: prints to stdout
wmx scripts list

# Large output (>128KB): writes to .wmx-output/scripts.json
wmx jobs get <job-id-with-huge-logs>
# Output: "Job saved to .wmx-output/job.json (245123 bytes)"
```

Auto-spilling prevents flooding agent context with massive payloads.

### Inline Mode

```bash
# Force stdout even for large outputs
wmx jobs get <job-id> --output-mode inline
```

Use when you need to pipe large results:

```bash
wmx jobs get <job-id> --output-mode inline --json | jq '.logs'
```

### File Mode

```bash
# Always write to file
wmx scripts get f/team/script --output-mode file
# Output: "Script saved to .wmx-output/script.json (1234 bytes)"
```

## Output File Control

### Explicit Output File

```bash
# Write to specific path
wmx resources get u/me/db --reveal --output-mode file --output-file ./backup/db.json

# Directory is created if needed
wmx jobs get <job-id> --output-file ./logs/job-result.json
```

### Spill Directory

```bash
# Change auto-spill directory (default: .wmx-output/)
wmx jobs list --spill-dir ./tmp/wmx
```

### Spill Threshold

```bash
# Change threshold (default: 131072 = 128KB)
wmx scripts list --spill-threshold-bytes 65536  # 64KB
wmx scripts list --spill-threshold-bytes 0      # Always spill in auto mode
```

## Output Examples

### Human Mode (Default)

List commands show tables:
```
path                    summary        language
----------------------  -------------  --------
f/team/send_report      Send report    python3
f/team/process_data     Process data   python3
```

Single-item commands show key-value:
```
path: f/team/send_report
summary: Send report
language: python3
content:
def main(recipient: str):
    ...
```

### JSON Mode

List commands return arrays:
```json
[
  {"path": "f/team/send_report", "summary": "Send report", "language": "python3"},
  {"path": "f/team/process_data", "summary": "Process data", "language": "python3"}
]
```

Single-item commands return objects:
```json
{
  "path": "f/team/send_report",
  "summary": "Send report",
  "language": "python3",
  "content": "def main(recipient: str):\n    ..."
}
```

### Spilled Output

When output is spilled (auto mode with large payload, or file mode):

Human mode:
```
Script saved to .wmx-output/script.json (45678 bytes)
```

JSON mode:
```json
{
  "label": "script",
  "saved_to": ".wmx-output/script.json",
  "bytes": 45678,
  "spilled": true
}
```

## Diagnostic Output

Diagnostics go to stderr, controlled by `--quiet` and `--verbose`:

```bash
# Normal: info messages to stderr
wmx scripts run f/team/script --wait
# stderr: "Waiting for job..."
# stderr: "Job completed in 2.3s"

# Quiet: suppress info messages
wmx scripts run f/team/script --wait --quiet

# Verbose: extra debug info
wmx scripts run f/team/script --wait --verbose
# stderr: "POST /api/w/workspace/jobs/run/p/f/team/script"
# stderr: "Response: 200 OK"
```

## Common Patterns

### Save Job Result to File

```bash
wmx scripts run f/team/script --wait --json --output-file ./result.json
```

### Export Resource for Backup

```bash
wmx resources get u/me/db --reveal --json --output-file ./backup/db.json
```

### Get Logs Without Cluttering Context

```bash
# Auto-spills if logs are large
wmx jobs logs <job-id>
# "Job logs saved to .wmx-output/job-abc123-logs.txt (98765 bytes)"

# Then read specific parts
head -50 .wmx-output/job-abc123-logs.txt
```

### Pipeline-Friendly JSON

```bash
# Force inline for piping
wmx scripts list --json --output-mode inline | jq '.[] | select(.language == "python3")'
```
