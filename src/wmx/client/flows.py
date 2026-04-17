from __future__ import annotations

from typing import Any

from wmx.client.http import HttpClient


class FlowsAPI:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def list(self, *, path_start: str | None = None, page: int = 1, per_page: int = 50) -> list[dict[str, Any]]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/flows/list",
            params={"path_start": path_start, "page": page, "per_page": per_page},
        )

    def list_search(self, *, path_start: str | None = None) -> list[dict[str, Any]]:
        """Return flows with path and value for client-side search."""
        return self.http.get_json(
            f"/w/{self.http.workspace}/flows/list_search",
            params={"path_start": path_start},
        )

    def get(self, path: str) -> dict[str, Any]:
        return self.http.get_json(f"/w/{self.http.workspace}/flows/get/{path}")

    def create(self, payload: dict[str, Any]) -> str:
        return self.http.post_text(f"/w/{self.http.workspace}/flows/create", payload=payload)

    def update(self, path: str, payload: dict[str, Any]) -> str:
        return self.http.post_text(f"/w/{self.http.workspace}/flows/update/{path}", payload=payload)

    def delete(self, path: str, *, keep_captures: bool = False) -> str:
        return self.http.delete_text(
            f"/w/{self.http.workspace}/flows/delete/{path}",
            params={"keep_captures": keep_captures},
        )

    def run(self, path: str, args: dict[str, Any]) -> str:
        return self.http.post_text(f"/w/{self.http.workspace}/jobs/run/f/{path}", payload=args)

    def preview(self, payload: dict[str, Any]) -> str:
        return self.http.post_text(f"/w/{self.http.workspace}/jobs/run/preview_flow", payload=payload)

