import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import yaml

DEFAULT_MODEL = 'GigaChat'
DEFAULT_TEMPERATURE = 0.7
DEFAULT_STREAM = True
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
    stream: bool = DEFAULT_STREAM
    system_prompt: str | None = None


def load_config(config_path: Path) -> AppConfig:
    env_path = config_path.parent / ENV_FILE_NAME
    if not config_path.exists() and not env_path.exists() and not _has_supported_env():
        raise ConfigError(CONFIG_NOT_FOUND)

    raw_config: dict[str, object] = {}
    if config_path.exists():
        raw_config.update(_load_yaml_config(config_path))
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
    raw_config.update(_load_os_env_config())
    return _build_config(raw_config, config_path.parent)


def _has_supported_env() -> bool:
    return any(name in os.environ for name in SUPPORTED_ENV_VARS)


def _load_os_env_config() -> dict[str, object]:
    return _load_env_config(os.environ)


def _load_env_config(env_values: Mapping[str, str]) -> dict[str, object]:
    raw_config: dict[str, object] = {}
    for config_key, env_name in ENV_MAPPING.items():
        env_value = env_values.get(env_name)
        if env_value is None:
            continue
        raw_config[config_key] = env_value
    return raw_config


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
    api_host = _required_non_empty_str(raw_config, 'api_host')
    api_key = _required_non_empty_str(raw_config, 'api_key')
    auth_scope = _optional_non_empty_str(raw_config, 'auth_scope')
    cert_path = _optional_non_empty_str(raw_config, 'cert_path')
    model = _optional_non_empty_str(raw_config, 'model')
    token_url = _optional_non_empty_str(raw_config, 'token_url')
    limit_message = _optional_positive_int(raw_config, 'limit_message')
    limit_chars = _optional_positive_int(raw_config, 'limit_chars')
    system_prompt = _optional_non_empty_str(raw_config, 'system_prompt')
    temperature = _optional_temperature(raw_config, 'temperature')
    stream = raw_config.get('stream')
    if stream is not None and not isinstance(stream, bool):
        raise ConfigError

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
        stream=DEFAULT_STREAM if stream is None else stream,
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


def _required_non_empty_str(raw_config: dict[str, object], key: str) -> str:
    value = _optional_non_empty_str(raw_config, key)
    if value is None:
        raise ConfigError
    return value


def _optional_non_empty_str(raw_config: dict[str, object], key: str) -> str | None:
    value = raw_config.get(key)
    if value is None:
        return None
    return _parse_non_empty_str(value)


def _optional_positive_int(raw_config: dict[str, object], key: str) -> int | None:
    value = raw_config.get(key)
    if value is None:
        return None
    return _parse_positive_int(value)


def _optional_temperature(raw_config: dict[str, object], key: str) -> float | None:
    value = raw_config.get(key)
    if value is None:
        return None
    return _parse_temperature(value)


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
