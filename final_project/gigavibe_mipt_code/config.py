import ast
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

DEFAULT_MODEL = 'GigaChat'
DEFAULT_TEMPERATURE = 0.7
DEFAULT_AUTH_SCOPE = 'GIGACHAT_API_PERS'
DEFAULT_TOKEN_URL = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
CONFIG_ERROR = 'Ошибка конфига.'
CONFIG_NOT_FOUND = 'Нет config.yaml'

ENV_API_HOST = 'API_HOST'
ENV_API_KEY = 'API_KEY'
ENV_AUTH_SCOPE = 'AUTH_SCOPE'
ENV_LIMIT_CHARS = 'LIMIT_CHARS'
ENV_LIMIT_MESSAGE = 'LIMIT_MESSAGE'
ENV_MODEL = 'MODEL'
ENV_TEMPERATURE = 'TEMPERATURE'
ENV_TOKEN_URL = 'TOKEN_URL'
ENV_VERIFY_SSL = 'VERIFY_SSL'

SUPPORTED_ENV_VARS = (
    ENV_API_HOST,
    ENV_API_KEY,
    ENV_AUTH_SCOPE,
    ENV_LIMIT_CHARS,
    ENV_LIMIT_MESSAGE,
    ENV_MODEL,
    ENV_TEMPERATURE,
    ENV_TOKEN_URL,
    ENV_VERIFY_SSL,
)


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class AppConfig:
    api_host: str
    api_key: str
    model: str = DEFAULT_MODEL
    auth_scope: str = DEFAULT_AUTH_SCOPE
    token_url: str = DEFAULT_TOKEN_URL
    verify_ssl: bool = True
    limit_message: int | None = None
    limit_chars: int | None = None
    temperature: float = DEFAULT_TEMPERATURE
    system_prompt: str | None = None


def load_config(config_path: Path) -> AppConfig:
    if not config_path.exists() and not _has_supported_env():
        raise ConfigError(CONFIG_NOT_FOUND)

    raw_config: dict[str, object] = {}
    if config_path.exists():
        raw_config.update(_load_yaml_config(config_path))
    raw_config.update(_load_env_config())
    return _build_config(raw_config)


def _has_supported_env() -> bool:
    return any(name in os.environ for name in SUPPORTED_ENV_VARS)


def _load_env_config() -> dict[str, object]:
    raw_config: dict[str, object] = {}
    env_mapping = {
        'api_host': ENV_API_HOST,
        'api_key': ENV_API_KEY,
        'auth_scope': ENV_AUTH_SCOPE,
        'limit_chars': ENV_LIMIT_CHARS,
        'limit_message': ENV_LIMIT_MESSAGE,
        'model': ENV_MODEL,
        'temperature': ENV_TEMPERATURE,
        'token_url': ENV_TOKEN_URL,
        'verify_ssl': ENV_VERIFY_SSL,
    }

    for config_key, env_name in env_mapping.items():
        env_value = os.environ.get(env_name)
        if env_value is None:
            continue
        raw_config[config_key] = env_value
    return raw_config


def _load_yaml_config(config_path: Path) -> dict[str, object]:
    content = config_path.read_text(encoding='utf-8')
    config: dict[str, object] = {}

    for raw_line in content.splitlines():
        stripped_line = raw_line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            continue
        if ':' not in raw_line:
            raise ConfigError

        key_part, value_part = raw_line.split(':', 1)
        key = key_part.strip()
        if not key:
            raise ConfigError

        config[key] = _parse_scalar(value_part.strip())
    return config


def _build_config(raw_config: dict[str, object]) -> AppConfig:
    api_host = cast(str, _required(raw_config, 'api_host', _parse_non_empty_str))
    api_key = cast(str, _required(raw_config, 'api_key', _parse_non_empty_str))
    auth_scope = cast(
        str | None,
        _optional(raw_config, 'auth_scope', _parse_non_empty_str),
    )
    model = cast(str | None, _optional(raw_config, 'model', _parse_non_empty_str))
    token_url = cast(str | None, _optional(raw_config, 'token_url', _parse_non_empty_str))
    verify_ssl = cast(bool | None, _optional(raw_config, 'verify_ssl', _parse_bool))
    limit_message = cast(
        int | None,
        _optional(raw_config, 'limit_message', _parse_positive_int),
    )
    limit_chars = cast(
        int | None,
        _optional(raw_config, 'limit_chars', _parse_positive_int),
    )
    system_prompt = cast(
        str | None,
        _optional(raw_config, 'system_prompt', _parse_non_empty_str),
    )
    temperature = cast(
        float | None,
        _optional(raw_config, 'temperature', _parse_temperature),
    )

    return AppConfig(
        api_host=api_host.rstrip('/'),
        api_key=api_key,
        model=model or DEFAULT_MODEL,
        auth_scope=auth_scope or DEFAULT_AUTH_SCOPE,
        token_url=(token_url or DEFAULT_TOKEN_URL).rstrip('/'),
        verify_ssl=True if verify_ssl is None else verify_ssl,
        limit_message=limit_message,
        limit_chars=limit_chars,
        temperature=DEFAULT_TEMPERATURE if temperature is None else temperature,
        system_prompt=system_prompt,
    )


def _parse_scalar(raw_value: str) -> object:
    if not raw_value:
        return ''

    normalized_value = raw_value.lower()
    if normalized_value in {'null', 'none', '~'}:
        return None
    if normalized_value == 'true':
        return True
    if normalized_value == 'false':
        return False

    if raw_value[0] in {'"', "'"} and raw_value[-1] == raw_value[0]:
        try:
            return ast.literal_eval(raw_value)
        except (SyntaxError, ValueError) as error:
            raise ConfigError from error

    try:
        return int(raw_value)
    except ValueError:
        pass

    try:
        return float(raw_value)
    except ValueError:
        return raw_value


def _required(
    raw_config: dict[str, object],
    key: str,
    parser: Callable[[object], object],
) -> object:
    value = _optional(raw_config, key, parser)
    if value is None:
        raise ConfigError
    return value


def _optional(
    raw_config: dict[str, object],
    key: str,
    parser: Callable[[object], object],
) -> object | None:
    value = raw_config.get(key)
    if value is None:
        return None
    return parser(value)


def _parse_non_empty_str(value: object) -> str:
    if not isinstance(value, str):
        raise ConfigError

    stripped_value = value.strip()
    if not stripped_value:
        raise ConfigError
    return stripped_value


def _parse_positive_int(value: object) -> int:
    if isinstance(value, bool):
        raise ConfigError
    if isinstance(value, int):
        parsed_value = value
    elif isinstance(value, str):
        try:
            parsed_value = int(value.strip())
        except ValueError as error:
            raise ConfigError from error
    else:
        raise ConfigError

    if parsed_value <= 0:
        raise ConfigError
    return parsed_value


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized_value = value.strip().lower()
        if normalized_value in {'1', 'true', 'yes'}:
            return True
        if normalized_value in {'0', 'false', 'no'}:
            return False
    raise ConfigError


def _parse_temperature(value: object) -> float:
    if isinstance(value, bool):
        raise ConfigError
    if isinstance(value, float):
        parsed_value = value
    elif isinstance(value, int):
        parsed_value = float(value)
    elif isinstance(value, str):
        try:
            parsed_value = float(value.strip())
        except ValueError as error:
            raise ConfigError from error
    else:
        raise ConfigError

    if not 0 <= parsed_value <= 1:
        raise ConfigError
    return parsed_value
