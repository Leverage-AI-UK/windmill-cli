from __future__ import annotations

from wmx.client.http import HttpClient


class AuthAPI:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def version(self) -> str:
        return self.http.get_text("/version")

    def global_whoami(self) -> dict:
        return self.http.get_json("/users/whoami")

    def workspace_whoami(self) -> dict:
        return self.http.get_json(f"/w/{self.http.workspace}/users/whoami")

