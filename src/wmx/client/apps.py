from __future__ import annotations

from typing import Any

from wmx.bundler import bundle_raw_app
from wmx.client.http import HttpClient


class AppsAPI:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def list(self, *, path_start: str | None = None, page: int = 1, per_page: int = 50) -> list[dict[str, Any]]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/apps/list",
            params={"path_start": path_start, "page": page, "per_page": per_page},
        )

    def list_search(self, *, path_start: str | None = None) -> list[dict[str, Any]]:
        """Return apps with path and value for client-side search."""
        return self.http.get_json(
            f"/w/{self.http.workspace}/apps/list_search",
            params={"path_start": path_start},
        )

    def get(self, path: str) -> dict[str, Any]:
        return self.http.get_json(f"/w/{self.http.workspace}/apps/get/p/{path}")

    def create(self, payload: dict[str, Any], *, raw: bool = False) -> str:
        if raw:
            return self._create_raw(payload)
        return self.http.post_text(f"/w/{self.http.workspace}/apps/create", payload=payload)

    def _create_raw(self, payload: dict[str, Any]) -> str:
        """Create a raw app using the multipart endpoint.

        Raw apps require the /apps/create_raw endpoint with multipart form data.
        Source files are bundled using esbuild before upload.
        """
        value = payload.get("value", {})
        bundled_js, bundled_css = bundle_raw_app(value)

        return self.http.post_multipart(
            f"/w/{self.http.workspace}/apps/create_raw",
            data={"app": payload},
            files={
                "js": ("bundle.js", bundled_js, "application/javascript"),
                "css": ("bundle.css", bundled_css or "/* empty */", "text/css"),
            },
        )

    def update(self, path: str, payload: dict[str, Any], *, raw: bool = False) -> str:
        if raw:
            return self._update_raw(path, payload)
        return self.http.post_text(f"/w/{self.http.workspace}/apps/update/{path}", payload=payload)

    def _update_raw(self, path: str, payload: dict[str, Any]) -> str:
        """Update a raw app using the multipart endpoint."""
        value = payload.get("value", {})
        bundled_js, bundled_css = bundle_raw_app(value)

        return self.http.post_multipart(
            f"/w/{self.http.workspace}/apps/update_raw/{path}",
            data={"app": payload},
            files={
                "js": ("bundle.js", bundled_js, "application/javascript"),
                "css": ("bundle.css", bundled_css or "/* empty */", "text/css"),
            },
        )

    def delete(self, path: str) -> str:
        return self.http.delete_text(f"/w/{self.http.workspace}/apps/delete/{path}")

