from __future__ import annotations

from typing import Any

from wmx.client.http import HttpClient


class AppsAPI:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def list(self, *, path_start: str | None = None, page: int = 1, per_page: int = 50) -> list[dict[str, Any]]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/apps/list",
            params={"path_start": path_start, "page": page, "per_page": per_page},
        )

    def get(self, path: str) -> dict[str, Any]:
        return self.http.get_json(f"/w/{self.http.workspace}/apps/get/p/{path}")

    def create(self, payload: dict[str, Any]) -> str:
        return self.http.post_text(f"/w/{self.http.workspace}/apps/create", payload=payload)

    def update(self, path: str, payload: dict[str, Any]) -> str:
        return self.http.post_text(f"/w/{self.http.workspace}/apps/update/{path}", payload=payload)

    def delete(self, path: str) -> str:
        return self.http.delete_text(f"/w/{self.http.workspace}/apps/delete/{path}")

