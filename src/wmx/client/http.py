from __future__ import annotations

import json
from typing import Any

import httpx

from wmx.config import RuntimeConfig
from wmx.errors import ApiError


class HttpClient:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self._client = httpx.Client(
            base_url=config.api_base_url,
            headers={
                "Authorization": f"Bearer {config.token}",
                "Content-Type": "application/json",
                "User-Agent": "wmx/0.1.0",
            },
            timeout=httpx.Timeout(60.0),
        )

    @property
    def workspace(self) -> str:
        return self.config.workspace

    def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params).json()

    def get_text(self, path: str, *, params: dict[str, Any] | None = None) -> str:
        return self._request("GET", path, params=params).text

    def post_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: Any = None,
    ) -> Any:
        return self._request("POST", path, params=params, json_body=payload).json()

    def post_text(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: Any = None,
    ) -> str:
        return self._request("POST", path, params=params, json_body=payload).text

    def delete_text(self, path: str, *, params: dict[str, Any] | None = None) -> str:
        return self._request("DELETE", path, params=params).text

    def delete_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: Any = None,
    ) -> Any:
        return self._request("DELETE", path, params=params, json_body=payload).json()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
    ) -> httpx.Response:
        response = self._client.request(method, path, params=_compact(params), json=json_body)
        if response.is_success:
            return response
        raise self._to_api_error(response)

    def _to_api_error(self, response: httpx.Response) -> ApiError:
        body = _response_message(response)
        status = response.status_code
        hint = None
        if status == 401:
            hint = "Check your token and base URL."
        elif status == 403:
            hint = "The authenticated user/token does not have permission for this path."
        elif status == 404:
            hint = "Verify the workspace and target path."
        elif status == 409:
            hint = "The requested change conflicts with an existing Windmill object."
        return ApiError(
            f"{response.request.method} {response.request.url.path} failed with {status}: {body}",
            status_code=status,
            hint=hint,
        )


def _compact(values: dict[str, Any] | None) -> dict[str, Any] | None:
    if values is None:
        return None
    return {key: value for key, value in values.items() if value is not None}


def _response_message(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data = response.json()
            if isinstance(data, dict):
                for key in ("error", "message", "msg"):
                    if key in data:
                        return str(data[key])
            return json.dumps(data, ensure_ascii=True)
        except json.JSONDecodeError:
            pass
    return response.text.strip() or "No response body."

