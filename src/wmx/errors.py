from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WmxError(Exception):
    message: str
    exit_code: int = 1
    hint: str | None = None

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message}\nHint: {self.hint}"
        return self.message


class ConfigurationError(WmxError):
    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message=message, exit_code=2, hint=hint)


class UsageError(WmxError):
    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message=message, exit_code=2, hint=hint)


class ConfirmationRequiredError(WmxError):
    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message=message, exit_code=3, hint=hint)


class ApiError(WmxError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        hint: str | None = None,
    ) -> None:
        super().__init__(message=message, exit_code=self._map_exit_code(status_code), hint=hint)
        self.status_code = status_code

    @staticmethod
    def _map_exit_code(status_code: int) -> int:
        if status_code == 401:
            return 10
        if status_code == 403:
            return 11
        if status_code == 404:
            return 12
        if status_code == 409:
            return 13
        return 14

