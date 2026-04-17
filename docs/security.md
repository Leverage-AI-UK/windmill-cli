# Security Model

## Core rule

`wmx` runs as the authenticated Windmill user token and relies on Windmill's existing permission system.

It does not:

- bypass path permissions
- emulate elevated access
- create an out-of-band auth model

## Auth handling

Authentication inputs come from:

- `--token`
- `WMX_TOKEN`
- `WINDMILL_TOKEN`

Tokens are sent as bearer tokens to the Windmill HTTP API. The CLI does not print tokens in normal output, and `wmx config show` redacts them.

## Variables

Variable handling is intentionally explicit.

Default behavior:

- `variables list` redacts secret values
- `variables get` does not decrypt secrets by default

Explicit behaviors:

- `--reveal` asks Windmill for plaintext secret values
- `--encrypted` asks Windmill to include encrypted secret material
- `--value-only` is blocked for secret values unless `--reveal` or `--encrypted` is present

The CLI does not silently decrypt and re-encrypt values on round trips.

## Resources

Resources are treated as sensitive by default because they usually contain structured credentials or connection details.

Default behavior:

- `resources list` redacts the `value` field
- `resources get` redacts the `value` field

Explicit behaviors:

- `--reveal` returns raw resource values
- `--value-only` requires `--reveal`
- `--interpolate` is only allowed when returning the value explicitly

## Logs and output

Normal command results go to stdout.
Diagnostics and streamed logs go to stderr.

This matters for automation because:

- `--json` output stays parseable
- streamed logs do not corrupt JSON payloads
- agents can capture primary outputs separately from diagnostics

## Large payload spill

Large payloads can be automatically written to disk instead of stdout.

This reduces the chance of:

- leaking bulky sensitive material into agent context
- overwhelming terminal transcripts
- mixing large outputs with subsequent automation steps

Controls:

- `--output-mode auto|inline|file`
- `--output-file`
- `--spill-dir`
- `--spill-threshold-bytes`

## Destructive operations

Delete commands require confirmation unless `--yes` is passed.

In non-interactive mode, missing `--yes` is an error. That is safer and more predictable for agents than prompting implicitly.

## Preview runs

Preview execution uses Windmill preview endpoints directly, so preview code still runs under Windmill's normal job and permission model.

That means:

- preview code receives Windmill runtime context according to the run
- preview code can access only the variables/resources the run is allowed to access
- preview does not need temp deployed artifacts

