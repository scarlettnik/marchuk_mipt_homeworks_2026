import ast
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

DEFAULT_MODEL = 'GigaChat'
DEFAULT_TEMPERATURE = 0.7
DEFAULT_AUTH_SCOPE = 'GIGACHAT_API_PERS'
DEFAULT_TOKEN_URL = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
DEFAULT_CERT_PATH = 'linux_russian_trusted_root_ca_pem'
CONFIG_ERROR = 'Ошибка конфига.'
CONFIG_NOT_FOUND = 'Нет config.yaml или .env'

ENV_API_HOST = 'API_HOST'
ENV_API_KEY = 'API_KEY'
ENV_AUTH_SCOPE = 'AUTH_SCOPE'
ENV_CERT_PATH = 'CERT_PATH'
ENV_LIMIT_CHARS = 'LIMIT_CHARS'
ENV_LIMIT_MESSAGE = 'LIMIT_MESSAGE'
ENV_MODEL = 'MODEL'
ENV_TEMPERATURE = 'TEMPERATURE'
ENV_TOKEN_URL = 'TOKEN_URL'
ENV_FILE_NAME = '.env'

SUPPORTED_ENV_VARS = (
    ENV_API_HOST,
    ENV_API_KEY,
    ENV_AUTH_SCOPE,
    ENV_CERT_PATH,
    ENV_LIMIT_CHARS,
    ENV_LIMIT_MESSAGE,
    ENV_MODEL,
    ENV_TEMPERATURE,
    ENV_TOKEN_URL,
)

ENV_MAPPING = {
    'api_host': ENV_API_HOST,
    'api_key': ENV_API_KEY,
    'auth_scope': ENV_AUTH_SCOPE,
    'cert_path': ENV_CERT_PATH,
    'limit_chars': ENV_LIMIT_CHARS,
    'limit_message': ENV_LIMIT_MESSAGE,
    'model': ENV_MODEL,
    'temperature': ENV_TEMPERATURE,
    'token_url': ENV_TOKEN_URL,
}

FORBIDDEN_YAML_KEYS = {'api_key', 'verify_ssl'}
CERT_SUFFIXES = ('.crt', '.pem')


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class AppConfig:
    api_host: str
    api_key: str
    cert_paths: tuple[Path, ...]
    model: str = DEFAULT_MODEL
    auth_scope: str = DEFAULT_AUTH_SCOPE
    token_url: str = DEFAULT_TOKEN_URL
    limit_message: int | None = None
    limit_chars: int | None = None
    temperature: float = DEFAULT_TEMPERATURE
    system_prompt: str | None = None


def load_config(config_path: Path) -> AppConfig:
    env_path = config_path.parent / ENV_FILE_NAME
    if not config_path.exists() and not env_path.exists() and not _has_supported_env():
        raise ConfigError(CONFIG_NOT_FOUND)

    raw_config: dict[str, object] = {}
    if config_path.exists():
        raw_config.update(_load_yaml_config(config_path))
    if env_path.exists():
        raw_config.update(_load_env_file_config(env_path))
    raw_config.update(_load_os_env_config())
    return _build_config(raw_config, config_path.parent)


def _has_supported_env() -> bool:
    return any(name in os.environ for name in SUPPORTED_ENV_VARS)


def _load_os_env_config() -> dict[str, object]:
    return _load_env_config(os.environ)


def _load_env_file_config(env_path: Path) -> dict[str, object]:
    return _load_env_config(_load_env_file(env_path))


def _load_env_config(env_values: Mapping[str, str]) -> dict[str, object]:
    raw_config: dict[str, object] = {}
    for config_key, env_name in ENV_MAPPING.items():
        env_value = env_values.get(env_name)
        if env_value is None:
            continue
        raw_config[config_key] = env_value
    return raw_config


def _load_env_file(env_path: Path) -> dict[str, str]:
    env_values: dict[str, str] = {}
    content = env_path.read_text(encoding='utf-8')

    for raw_line in content.splitlines():
        stripped_line = raw_line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            continue
        if stripped_line.startswith('export '):
            stripped_line = stripped_line.removeprefix('export ').strip()
        if '=' not in stripped_line:
            raise ConfigError

        key_part, value_part = stripped_line.split('=', 1)
        key = key_part.strip()
        if not key:
            raise ConfigError
        env_values[key] = _parse_env_value(value_part.strip())
    return env_values


def _load_yaml_config(config_path: Path) -> dict[str, object]:
    try:
        loaded_config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    except yaml.YAMLError as error:
        raise ConfigError from error

    if loaded_config is None:
        return {}
    if not isinstance(loaded_config, Mapping):
        raise ConfigError

    config: dict[str, object] = {}
    for raw_key, value in loaded_config.items():
        if not isinstance(raw_key, str):
            raise ConfigError

        key = raw_key.strip()
        if not key or key in FORBIDDEN_YAML_KEYS:
            raise ConfigError
        config[key] = value
    return config


def _build_config(raw_config: dict[str, object], config_dir: Path) -> AppConfig:
    api_host = cast(str, _required(raw_config, 'api_host', _parse_non_empty_str))
    api_key = cast(str, _required(raw_config, 'api_key', _parse_non_empty_str))
    auth_scope = cast(
        str | None,
        _optional(raw_config, 'auth_scope', _parse_non_empty_str),
    )
    cert_path = cast(str | None, _optional(raw_config, 'cert_path', _parse_non_empty_str))
    model = cast(str | None, _optional(raw_config, 'model', _parse_non_empty_str))
    token_url = cast(str | None, _optional(raw_config, 'token_url', _parse_non_empty_str))
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
        cert_paths=_resolve_cert_paths(config_dir, cert_path or DEFAULT_CERT_PATH),
        model=model or DEFAULT_MODEL,
        auth_scope=auth_scope or DEFAULT_AUTH_SCOPE,
        token_url=(token_url or DEFAULT_TOKEN_URL).rstrip('/'),
        limit_message=limit_message,
        limit_chars=limit_chars,
        temperature=DEFAULT_TEMPERATURE if temperature is None else temperature,
        system_prompt=system_prompt,
    )


def _resolve_cert_paths(config_dir: Path, raw_cert_path: str) -> tuple[Path, ...]:
    cert_path = Path(raw_cert_path).expanduser()
    if not cert_path.is_absolute():
        cert_path = config_dir / cert_path

    if cert_path.is_file():
        if not _is_cert_file(cert_path):
            raise ConfigError
        return (cert_path.resolve(),)

    if cert_path.is_dir():
        cert_paths = tuple(
            sorted(
                path.resolve()
                for path in cert_path.iterdir()
                if path.is_file() and _is_cert_file(path)
            ),
        )
        if not cert_paths:
            raise ConfigError
        return cert_paths

    raise ConfigError


def _is_cert_file(path: Path) -> bool:
    return path.suffix.lower() in CERT_SUFFIXES


def _parse_env_value(raw_value: str) -> str:
    if not raw_value:
        return ''

    if raw_value[0] in {'"', "'"}:
        if raw_value[-1] != raw_value[0]:
            raise ConfigError
        try:
            parsed_value = ast.literal_eval(raw_value)
        except (SyntaxError, ValueError) as error:
            raise ConfigError from error
        if not isinstance(parsed_value, str):
            raise ConfigError
        return parsed_value

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
