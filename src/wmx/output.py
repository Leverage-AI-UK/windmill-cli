from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable

import typer


HumanRenderer = Callable[[Any], str]


@dataclass(frozen=True, slots=True)
class OutputOptions:
    json_mode: bool
    output_mode: str
    output_file: Path | None
    spill_dir: Path
    spill_threshold_bytes: int
    quiet: bool
    verbose: bool


class OutputManager:
    def __init__(self, options: OutputOptions) -> None:
        self.options = options

    def emit(
        self,
        payload: Any,
        *,
        label: str = "result",
        human_renderer: HumanRenderer | None = None,
        file_stem: str | None = None,
    ) -> None:
        rendered_human = human_renderer(payload) if human_renderer else render_human(payload)
        serialized = render_json(payload)
        structured = not isinstance(payload, str)
        bytes_len = len(serialized.encode("utf-8")) if structured else len(rendered_human.encode("utf-8"))
        should_spill = self._should_spill(bytes_len)

        if should_spill:
            path = self._write_payload(
                payload,
                structured=structured,
                file_stem=file_stem or label.replace(" ", "-"),
            )
            manifest = {
                "label": label,
                "saved_to": str(path),
                "bytes": path.stat().st_size,
                "spilled": True,
            }
            if self.options.json_mode:
                typer.echo(json.dumps(manifest, sort_keys=True))
            else:
                typer.echo(f"{label.capitalize()} saved to {path} ({manifest['bytes']} bytes)")
            return

        if self.options.json_mode:
            typer.echo(serialized)
            return

        typer.echo(rendered_human)

    def info(self, message: str) -> None:
        if not self.options.quiet:
            typer.echo(message, err=True)

    def debug(self, message: str) -> None:
        if self.options.verbose:
            typer.echo(message, err=True)

    def error(self, message: str) -> None:
        typer.echo(message, err=True)

    def _should_spill(self, size_bytes: int) -> bool:
        if self.options.output_mode == "file":
            return True
        if self.options.output_mode == "auto" and size_bytes >= self.options.spill_threshold_bytes:
            return True
        return False

    def _write_payload(self, payload: Any, *, structured: bool, file_stem: str) -> Path:
        if self.options.output_file:
            path = self.options.output_file
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.options.spill_dir.mkdir(parents=True, exist_ok=True)
            suffix = ".json" if structured else ".txt"
            path = self.options.spill_dir / f"{file_stem}{suffix}"

        if structured:
            path.write_text(render_json(payload), encoding="utf-8")
        else:
            path.write_text(str(payload), encoding="utf-8")
        return path


def render_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)


def render_human(payload: Any) -> str:
    if isinstance(payload, list):
        return render_list(payload)
    if isinstance(payload, dict):
        return render_record(payload)
    return str(payload)


def render_record(record: dict[str, Any], order: list[str] | None = None) -> str:
    keys = order or sorted(record.keys())
    lines: list[str] = []
    for key in keys:
        if key not in record:
            continue
        value = record[key]
        if isinstance(value, (dict, list)):
            pretty = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True)
            lines.append(f"{key}:")
            lines.extend(pretty.splitlines())
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


def render_list(items: list[Any]) -> str:
    if not items:
        return "No results."
    if all(isinstance(item, dict) for item in items):
        return render_table(items)
    return "\n".join(str(item) for item in items)


def render_table(items: list[dict[str, Any]], columns: list[str] | None = None) -> str:
    if not items:
        return "No results."
    selected_columns = columns or _infer_columns(items)
    widths = {column: len(column) for column in selected_columns}
    rows: list[list[str]] = []
    for item in items:
        row: list[str] = []
        for column in selected_columns:
            cell = _stringify_cell(item.get(column))
            widths[column] = max(widths[column], len(cell))
            row.append(cell)
        rows.append(row)

    header = "  ".join(column.ljust(widths[column]) for column in selected_columns)
    separator = "  ".join("-" * widths[column] for column in selected_columns)
    body = [
        "  ".join(cell.ljust(widths[selected_columns[index]]) for index, cell in enumerate(row))
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _infer_columns(items: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "path",
        "summary",
        "script_path",
        "schedule",
        "resource_type",
        "description",
        "id",
        "job_id",
        "job_kind",
        "success",
        "enabled",
        "workspace_id",
    ]
    keys: list[str] = []
    for item in items:
        for key in item:
            if key not in keys:
                keys.append(key)
    ordered = [key for key in preferred if key in keys]
    ordered.extend(key for key in keys if key not in ordered)
    return ordered[:6]


def _stringify_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        compact = json.dumps(value, separators=(",", ":"), ensure_ascii=True)
        if len(compact) > 48:
            return f"{compact[:45]}..."
        return compact
    return str(value)

