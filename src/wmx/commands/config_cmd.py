from __future__ import annotations

import typer

from wmx.output import render_record
from wmx.state import get_state


app = typer.Typer(help="Inspect resolved CLI configuration.")


@app.command("show")
def show_config(ctx: typer.Context) -> None:
    state = get_state(ctx)
    state.output.emit(
        state.config.as_dict(),
        label="config",
        human_renderer=lambda payload: render_record(payload),
    )

