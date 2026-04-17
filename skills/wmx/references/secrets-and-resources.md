# Secrets and Resources

wmx redacts sensitive values by default. You must explicitly opt-in to see secret data.

## Variables

Variables can be either plain values or secrets. Secret values require explicit flags to view.

### Listing Variables

```bash
wmx variables list
# Values are always omitted in list view
```

### Getting a Variable

```bash
# Default: secret values show "[REDACTED]"
wmx variables get u/me/api_key

# Reveal plaintext value
wmx variables get u/me/api_key --reveal

# Get the encrypted form instead
wmx variables get u/me/api_key --encrypted

# Metadata only (no value field at all)
wmx variables get u/me/api_key --metadata-only
```

### Getting Just the Value

```bash
# Non-secret: works without --reveal
wmx variables get u/me/config --value-only

# Secret: REQUIRES --reveal or --encrypted
wmx variables get u/me/api_key --value-only --reveal
wmx variables get u/me/api_key --value-only --encrypted

# ERROR: --value-only on secret without reveal flag
wmx variables get u/me/api_key --value-only
# UsageError: --value-only for secret variables requires --reveal or --encrypted
```

### Invalid Flag Combinations

```bash
# ERROR: mutually exclusive
wmx variables get u/me/api_key --reveal --encrypted

# ERROR: mutually exclusive
wmx variables get u/me/api_key --metadata-only --value-only
```

### Creating and Updating Variables

```bash
# Create a secret variable
wmx variables create u/me/api_key --secret --value "sk-..."

# Create from file
wmx variables create u/me/cert --value-file ./cert.pem --secret

# Create from stdin (useful for piping from password managers)
echo "secret-value" | wmx variables create u/me/token --secret --value-from-stdin

# Update value
wmx variables update u/me/api_key --value "sk-new..."

# Mark as non-secret (demote)
wmx variables update u/me/api_key --no-secret
```

Value input requires exactly one of:
- `--value "..."` (inline)
- `--value-file path` (from file)
- `--value-from-stdin` (from stdin)

## Resources

Resources always contain structured values (JSON objects) and are treated as potentially sensitive by default.

### Listing Resources

```bash
wmx resources list
# Values are always omitted in list view

wmx resources list --type postgresql
# Filter by resource type
```

### Getting a Resource

```bash
# Default: value shows "[REDACTED]"
wmx resources get u/me/db

# Reveal the raw value
wmx resources get u/me/db --reveal
```

### Getting Just the Resource Value

```bash
# REQUIRES --reveal (always, unlike variables)
wmx resources get u/me/db --value-only --reveal

# ERROR: --value-only without --reveal
wmx resources get u/me/db --value-only
# UsageError: --value-only requires --reveal for resources

# Get interpolated value (variable references resolved)
wmx resources get u/me/db --value-only --reveal --interpolate
```

### Creating and Updating Resources

Resources are defined in JSON or YAML files:

```bash
# From a file with path, resource_type, and value
wmx resources create u/me/db --file ./db.json

# From a raw value file (requires --type)
wmx resources create u/me/db --file ./db_value.json --type postgresql

# Upsert pattern
wmx resources create u/me/db --file ./db.json --update-if-exists

# Update existing
wmx resources update u/me/db --file ./db.json
```

Example resource file (`db.json`):
```json
{
  "resource_type": "postgresql",
  "value": {
    "host": "localhost",
    "port": 5432,
    "user": "admin",
    "password": "secret123",
    "dbname": "myapp"
  }
}
```

## Writing Secrets to Files

Combine `--value-only --reveal` with output redirection:

```bash
# Write variable value to file
wmx variables get u/me/cert --value-only --reveal > ./cert.pem

# Write resource to JSON file
wmx resources get u/me/db --value-only --reveal --json > ./db.json

# Use output-file flag for automatic directory creation
wmx resources get u/me/db --value-only --reveal --output-mode file --output-file ./secrets/db.json
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `--value-only for secret variables requires --reveal or --encrypted` | Trying to get secret value without explicit flag | Add `--reveal` or `--encrypted` |
| `--value-only requires --reveal for resources` | Resources always require reveal for value-only | Add `--reveal` |
| `--reveal and --encrypted are mutually exclusive` | Can't use both flags | Pick one |
| `--metadata-only and --value-only cannot be used together` | Conflicting output modes | Pick one |
| `Provide exactly one of --value, --value-file, or --value-from-stdin` | Missing or multiple value sources | Provide exactly one |
