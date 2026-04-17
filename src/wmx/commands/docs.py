from __future__ import annotations

from typing import Annotated

import typer

from wmx.state import get_state


app = typer.Typer(
    help=(
        "Query the Windmill documentation assistant when the instance supports it.\n\n"
        "This maps to the /api/inkeep endpoint, which is Enterprise-only on current Windmill builds.\n"
    )
)


@app.command("query")
def query_docs(
    ctx: typer.Context,
    query: Annotated[str, typer.Argument(help="Documentation question to send to Windmill.")],
) -> None:
    state = get_state(ctx)
    result = state.client().docs.query(query)
    state.output.emit(result, label="docs query")

