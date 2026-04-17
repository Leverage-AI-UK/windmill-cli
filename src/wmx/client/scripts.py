from __future__ import annotations

from typing import Any

from wmx.client.http import HttpClient


class ScriptsAPI:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def list(
        self,
        *,
        path_start: str | None = None,
        page: int = 1,
        per_page: int = 50,
        languages: str | None = None,
        include_draft_only: bool | None = None,
    ) -> list[dict[str, Any]]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/scripts/list",
            params={
                "path_start": path_start,
                "page": page,
                "per_page": per_page,
                "languages": languages,
                "include_draft_only": include_draft_only,
            },
        )

    def list_search(
        self,
        *,
        path_start: str | None = None,
        languages: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return scripts with path and content for client-side search."""
        return self.http.get_json(
            f"/w/{self.http.workspace}/scripts/list_search",
            params={
                "path_start": path_start,
                "languages": languages,
            },
        )

    def get(self, path: str) -> dict[str, Any]:
        return self.http.get_json(f"/w/{self.http.workspace}/scripts/get/p/{path}")

    def get_by_hash(self, script_hash: str) -> dict[str, Any]:
        return self.http.get_json(f"/w/{self.http.workspace}/scripts/get/h/{script_hash}")

    def create(self, payload: dict[str, Any]) -> str:
        return self.http.post_text(f"/w/{self.http.workspace}/scripts/create", payload=payload)

    def update(self, path: str, payload: dict[str, Any]) -> str:
        # Archive the current version first, then create new version
        self.archive(path)
        return self.create(payload)

    def archive(self, path: str) -> None:
        self.http.post_text(f"/w/{self.http.workspace}/scripts/archive/p/{path}")

    def delete_path(self, path: str, *, keep_captures: bool = False) -> str:
        return self.http.post_text(
            f"/w/{self.http.workspace}/scripts/delete/p/{path}",
            params={"keep_captures": keep_captures},
        )

    def delete_hash(self, script_hash: str) -> dict[str, Any]:
        return self.http.post_json(f"/w/{self.http.workspace}/scripts/delete/h/{script_hash}")

    def run_path(self, path: str, args: dict[str, Any]) -> str:
        return self.http.post_text(f"/w/{self.http.workspace}/jobs/run/p/{path}", payload=args)

    def run_hash(self, script_hash: str, args: dict[str, Any]) -> str:
        return self.http.post_text(f"/w/{self.http.workspace}/jobs/run/h/{script_hash}", payload=args)

    def preview(self, payload: dict[str, Any]) -> str:
        return self.http.post_text(f"/w/{self.http.workspace}/jobs/run/preview", payload=payload)

