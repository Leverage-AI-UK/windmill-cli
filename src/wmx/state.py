from __future__ import annotations

from dataclasses import dataclass

from typer import Context

from wmx.client import WindmillAPI
from wmx.config import ResolvedConfig
from wmx.output import OutputManager


@dataclass(slots=True)
class AppState:
    config: ResolvedConfig
    output: OutputManager
    yes: bool
    _client: WindmillAPI | None = None

    def client(self) -> WindmillAPI:
        if self._client is None:
            self._client = WindmillAPI(self.config.require_complete())
        return self._client


def get_state(ctx: Context) -> AppState:
    state = ctx.obj
    if not isinstance(state, AppState):
        raise RuntimeError("CLI state was not initialised.")
    return state

