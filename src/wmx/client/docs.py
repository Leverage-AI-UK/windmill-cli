from __future__ import annotations

from wmx.client.http import HttpClient


class DocsAPI:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def query(self, query: str) -> dict:
        return self.http.post_json("/inkeep", payload={"query": query})
