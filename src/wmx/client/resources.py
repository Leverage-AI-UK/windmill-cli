from __future__ import annotations

from typing import Any

from wmx.client.http import HttpClient


class ResourcesAPI:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def list(
        self,
        *,
        path_start: str | None = None,
        resource_type: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> list[dict[str, Any]]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/resources/list",
            params={
                "path_start": path_start,
                "resource_type": resource_type,
                "page": page,
                "per_page": per_page,
            },
        )

    def get(self, path: str) -> dict[str, Any]:
        return self.http.get_json(f"/w/{self.http.workspace}/resources/get/{path}")

    def get_value(self, path: str, *, interpolate: bool = False) -> Any:
        endpoint = "get_value_interpolated" if interpolate else "get_value"
        return self.http.get_json(f"/w/{self.http.workspace}/resources/{endpoint}/{path}")

    def create(self, payload: dict[str, Any], *, update_if_exists: bool = False) -> str:
        return self.http.post_text(
            f"/w/{self.http.workspace}/resources/create",
            params={"update_if_exists": update_if_exists},
            payload=payload,
        )

    def update(self, path: str, payload: dict[str, Any]) -> str:
        return self.http.post_text(f"/w/{self.http.workspace}/resources/update/{path}", payload=payload)

    def delete(self, path: str) -> str:
        return self.http.delete_text(f"/w/{self.http.workspace}/resources/delete/{path}")

    def list_types(self) -> list[dict[str, Any]]:
        return self.http.get_json(f"/w/{self.http.workspace}/resources/type/list")

