# Command Design

## Naming

The console entrypoint is `wmx`.

Reasons:

- short enough for repeated use by humans and agents
- clearly Windmill-related without colliding with `wmill`
- visually distinct in shell transcripts

## Group naming

Top-level groups are plural:

- `scripts`
- `flows`
- `resources`
- `variables`
- `jobs`
- `schedules`
- `apps`

Reasons:

- consistent with object collections
- easier to predict from examples
- aligns with how users tend to think about workspace surfaces

`queue` is kept as a top-level alias because queued jobs are a common operational view and the shorthand is useful.

## Output defaults

Default mode is human-readable, but with agent-oriented safeguards:

- `--json` gives stable machine output
- stdout contains only the primary payload
- stderr is reserved for logs and diagnostics
- `--output-mode auto` spills large payloads to the filesystem

This balances human usability with agent-context discipline.

## Sensitive data policy

Variables:

- non-secret variables can be shown normally
- secret variables are redacted by default
- `--reveal` returns plaintext intentionally
- `--encrypted` returns the encrypted secret intentionally

Resources:

- resource values are redacted by default because resources frequently contain structured credentials
- `--reveal` is required to surface raw values
- `--value-only` is blocked unless `--reveal` is also present

## Destructive action policy

Destructive commands require confirmation unless `--yes` is passed.

In non-interactive environments, absence of `--yes` is treated as an error instead of a prompt. That avoids hanging agents on an unexpected confirmation request.

## Run semantics

Deployed `run` commands default to asynchronous submission and return a job id unless `--wait` is passed.

Preview commands default to waiting because preview is primarily an interactive validation workflow.

All wait-capable commands support:

- `--wait`
- `--follow`
- `--timeout`
- `--poll-interval`

## File/input conventions

Structured inputs use common shell-friendly patterns:

- `--data '{"x":1}'`
- `--data @args.json`
- `--data @-`

Resource, flow, schedule, and app definitions are accepted from JSON or YAML files where that fits the object model.

Preview scripts and script creation support extra module injection with repeatable `--module RELATIVE=FILE`.

