from __future__ import annotations

from typing import Any

from wmx.client.http import HttpClient


class VariablesAPI:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def list(self, *, path_start: str | None = None, page: int = 1, per_page: int = 50) -> list[dict[str, Any]]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/variables/list",
            params={"path_start": path_start, "page": page, "per_page": per_page},
        )

    def get(
        self,
        path: str,
        *,
        decrypt_secret: bool = False,
        include_encrypted: bool = False,
    ) -> dict[str, Any]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/variables/get/{path}",
            params={
                "decrypt_secret": decrypt_secret,
                "include_encrypted": include_encrypted,
            },
        )

    def get_value(self, path: str) -> str:
        return self.http.get_json(f"/w/{self.http.workspace}/variables/get_value/{path}")

    def create(self, payload: dict[str, Any], *, already_encrypted: bool = False) -> str:
        return self.http.post_text(
            f"/w/{self.http.workspace}/variables/create",
            params={"already_encrypted": already_encrypted},
            payload=payload,
        )

    def update(self, path: str, payload: dict[str, Any], *, already_encrypted: bool = False) -> str:
        return self.http.post_text(
            f"/w/{self.http.workspace}/variables/update/{path}",
            params={"already_encrypted": already_encrypted},
            payload=payload,
        )

    def delete(self, path: str) -> str:
        return self.http.delete_text(f"/w/{self.http.workspace}/variables/delete/{path}")

