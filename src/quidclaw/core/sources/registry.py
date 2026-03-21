import os

from quidclaw.config import QuidClawConfig
from quidclaw.core.sources.base import DataSource

PROVIDERS: dict[str, type[DataSource]] = {}


def register_provider(cls: type[DataSource]) -> type[DataSource]:
    PROVIDERS[cls.provider_name()] = cls
    return cls


def get_provider(provider_name: str) -> type[DataSource]:
    if provider_name not in PROVIDERS:
        raise ValueError(
            f"Unknown provider: {provider_name}. Available: {list(PROVIDERS.keys())}"
        )
    return PROVIDERS[provider_name]


def resolve_env_refs(source_config: dict) -> dict:
    resolved = {}
    for key, value in source_config.items():
        if isinstance(value, str) and value.startswith("env:"):
            env_var = value[4:]
            resolved[key] = os.environ.get(env_var, "")
        else:
            resolved[key] = value
    return resolved


def create_source(
    source_name: str, source_config: dict, config: QuidClawConfig
) -> DataSource:
    provider_name = source_config["provider"]
    cls = get_provider(provider_name)
    resolved = resolve_env_refs(source_config)
    return cls(source_name=source_name, source_config=resolved, config=config)
