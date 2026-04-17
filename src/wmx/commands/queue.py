from __future__ import annotations

from typing import Annotated, Optional

import typer

from wmx.output import render_table
from wmx.state import get_state


app = typer.Typer(
    help=(
        "Inspect queued and running jobs.\n\n"
        "Example:\n"
        "  wmx queue list --running true\n"
    )
)


@app.command("list")
def list_queue(
    ctx: typer.Context,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    per_page: Annotated[int, typer.Option(help="Items per page.")] = 50,
    running: Annotated[Optional[bool], typer.Option(help="Filter queued jobs by running state.")] = None,
) -> None:
    state = get_state(ctx)
    items = state.client().jobs.list_queue(page=page, per_page=per_page, running=running)
    state.output.emit(items, label="queue", human_renderer=lambda payload: render_table(payload))
