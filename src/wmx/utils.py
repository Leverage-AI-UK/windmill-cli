from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import typer
import yaml

from wmx.errors import ConfirmationRequiredError, UsageError


LANGUAGE_BY_SUFFIX = {
    ".py": "python3",
    ".ts": "bun",
    ".js": "bun",
    ".go": "go",
    ".sh": "bash",
    ".bash": "bash",
    ".ps1": "powershell",
    ".php": "php",
    ".rs": "rust",
    ".cs": "csharp",
    ".java": "java",
    ".rb": "ruby",
    ".nu": "nu",
}


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_structured_file(path: Path) -> Any:
    text = load_text(path)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)


def parse_json_input(raw: str | None) -> dict[str, Any]:
    if raw is None:
        return {}
    if raw.startswith("@"):
        target = raw[1:]
        if target == "-":
            return json.loads(sys.stdin.read())
        return json.loads(Path(target).read_text(encoding="utf-8"))
    return json.loads(raw)


def parse_modules(module_specs: list[str]) -> dict[str, dict[str, str]] | None:
    if not module_specs:
        return None
    modules: dict[str, dict[str, str]] = {}
    for spec in module_specs:
        if "=" not in spec:
            raise UsageError(
                f"Invalid --module value: {spec}",
                hint="Use --module relative/path.py=./local_file.py",
            )
        relative_path, local_path = spec.split("=", 1)
        relative_path = relative_path.strip()
        local_file = Path(local_path.strip())
        if not relative_path:
            raise UsageError("Module relative path cannot be empty.")
        modules[relative_path] = {
            "content": load_text(local_file),
            "language": infer_language(local_file),
        }
    return modules


def infer_language(path: Path) -> str:
    language = LANGUAGE_BY_SUFFIX.get(path.suffix.lower())
    if not language:
        raise UsageError(
            f"Cannot infer script language from {path.name}.",
            hint="Pass --language explicitly.",
        )
    return language


def confirm_or_abort(*, yes: bool, message: str) -> None:
    if yes:
        return
    if not sys.stdin.isatty():
        raise ConfirmationRequiredError(
            message,
            hint="Re-run with --yes to confirm in non-interactive environments.",
        )
    if not typer.confirm(message):
        raise ConfirmationRequiredError("Aborted by user.", hint="Re-run with --yes to skip confirmation.")


def build_script_payload(
    *,
    path: str,
    file: Path,
    language: str | None,
    summary: str | None,
    description: str | None,
    kind: str,
    tag: str | None,
    deployment_message: str | None,
    draft_only: bool,
    modules: dict[str, dict[str, str]] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "path": path,
        "content": load_text(file),
        "language": language or infer_language(file),
        "summary": summary or path.split("/")[-1].replace("_", " "),
        "kind": kind,
    }
    if description:
        payload["description"] = description
    if tag:
        payload["tag"] = tag
    if deployment_message:
        payload["deployment_message"] = deployment_message
    if draft_only:
        payload["draft_only"] = True
    if modules:
        payload["modules"] = modules
    return payload


def sanitize_variable(item: dict[str, Any], *, reveal: bool = False, metadata_only: bool = False) -> dict[str, Any]:
    sanitized = dict(item)
    if metadata_only:
        sanitized.pop("value", None)
        return sanitized
    if sanitized.get("is_secret") and not reveal:
        sanitized.pop("value", None)
        sanitized["value_redacted"] = True
    return sanitized


def sanitize_resource(item: dict[str, Any], *, reveal: bool = False) -> dict[str, Any]:
    sanitized = dict(item)
    if not reveal:
        sanitized.pop("value", None)
        sanitized["value_redacted"] = True
    return sanitized


def read_stdin_value() -> str:
    return sys.stdin.read().rstrip("\n")

