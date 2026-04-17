from __future__ import annotations

from dataclasses import asdict, dataclass
import os

from wmx.errors import ConfigurationError


ENV_ALIASES = {
    "base_url": ("WMX_BASE_URL", "WINDMILL_BASE_URL"),
    "workspace": ("WMX_WORKSPACE", "WINDMILL_WORKSPACE"),
    "token": ("WMX_TOKEN", "WINDMILL_TOKEN"),
}


@dataclass(frozen=True, slots=True)
class ConfigValue:
    value: str | None
    source: str


@dataclass(frozen=True, slots=True)
class ResolvedConfig:
    base_url: ConfigValue
    workspace: ConfigValue
    token: ConfigValue

    def require_complete(self) -> "RuntimeConfig":
        missing: list[str] = []
        if not self.base_url.value:
            missing.append("base URL (--base-url or WMX_BASE_URL)")
        if not self.workspace.value:
            missing.append("workspace (--workspace or WMX_WORKSPACE)")
        if not self.token.value:
            missing.append("token (--token or WMX_TOKEN)")
        if missing:
            raise ConfigurationError(
                "Missing required configuration values.",
                hint=f"Provide {', '.join(missing)}.",
            )
        return RuntimeConfig(
            base_url=normalize_base_url(self.base_url.value),
            workspace=self.workspace.value,
            token=self.token.value,
        )

    def as_dict(self, *, redact_token: bool = True) -> dict[str, dict[str, str | None]]:
        data = asdict(self)
        if redact_token and data["token"]["value"]:
            data["token"]["value"] = redact_secret(data["token"]["value"])
        return data


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    base_url: str
    workspace: str
    token: str

    @property
    def api_base_url(self) -> str:
        if self.base_url.endswith("/api"):
            return self.base_url
        return f"{self.base_url}/api"


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def redact_secret(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def resolve_config(
    *,
    base_url: str | None,
    workspace: str | None,
    token: str | None,
) -> ResolvedConfig:
    return ResolvedConfig(
        base_url=_resolve_value(base_url, "base_url"),
        workspace=_resolve_value(workspace, "workspace"),
        token=_resolve_value(token, "token"),
    )


def _resolve_value(explicit: str | None, key: str) -> ConfigValue:
    if explicit:
        return ConfigValue(value=explicit, source="flag")

    for env_name in ENV_ALIASES[key]:
        env_value = os.getenv(env_name)
        if env_value:
            return ConfigValue(value=env_value, source=f"env:{env_name}")

    return ConfigValue(value=None, source="unset")

