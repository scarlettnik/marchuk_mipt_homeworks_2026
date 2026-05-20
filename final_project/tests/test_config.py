from pathlib import Path

import pytest

from final_project.gigavibe_mipt_code.config import ConfigError, load_config

ENV_KEYS = (
    'API_HOST',
    'API_KEY',
    'AUTH_SCOPE',
    'LIMIT_CHARS',
    'LIMIT_MESSAGE',
    'MODEL',
    'TEMPERATURE',
    'TOKEN_URL',
    'VERIFY_SSL',
)


def test_load_config_from_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        '\n'.join(
            (
                'api_key: yaml-token',
                'api_host: https://gigachat.devices.sberbank.ru/api/v1',
                'limit_message: 10',
                'limit_chars: 2000',
                'temperature: 0.2',
                'verify_ssl: false',
                'system_prompt: Test prompt',
            ),
        ),
        encoding='utf-8',
    )

    config = load_config(config_path)

    assert config.api_key == 'yaml-token'
    assert config.api_host == 'https://gigachat.devices.sberbank.ru/api/v1'
    assert config.auth_scope == 'GIGACHAT_API_PERS'
    assert config.token_url == 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
    assert config.verify_ssl is False
    assert config.limit_message == 10
    assert config.limit_chars == 2000
    assert config.temperature == 0.2
    assert config.system_prompt == 'Test prompt'


def test_environment_overrides_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        '\n'.join(
            (
                'api_key: yaml-token',
                'api_host: https://yaml.example/v1',
                'limit_chars: 100',
                'temperature: 0.2',
                'system_prompt: Stored prompt',
            ),
        ),
        encoding='utf-8',
    )

    monkeypatch.setenv('API_KEY', 'env-token')
    monkeypatch.setenv('API_HOST', 'https://env.example/v1')
    monkeypatch.setenv('AUTH_SCOPE', 'CUSTOM_SCOPE')
    monkeypatch.setenv('LIMIT_CHARS', '300')
    monkeypatch.setenv('TEMPERATURE', '0.5')
    monkeypatch.setenv('TOKEN_URL', 'https://token.example/oauth')
    monkeypatch.setenv('VERIFY_SSL', 'false')

    config = load_config(config_path)

    assert config.api_key == 'env-token'
    assert config.api_host == 'https://env.example/v1'
    assert config.auth_scope == 'CUSTOM_SCOPE'
    assert config.token_url == 'https://token.example/oauth'
    assert config.verify_ssl is False
    assert config.limit_chars == 300
    assert config.temperature == 0.5
    assert config.system_prompt == 'Stored prompt'


def test_load_config_raises_without_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_env(monkeypatch)

    with pytest.raises(ConfigError):
        load_config(tmp_path / 'config.yaml')


def test_load_config_rejects_non_positive_limits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_env(monkeypatch)
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        '\n'.join(
            (
                'api_key: yaml-token',
                'api_host: https://gigachat.devices.sberbank.ru/api/v1',
                'limit_chars: 0',
            ),
        ),
        encoding='utf-8',
    )

    with pytest.raises(ConfigError):
        load_config(config_path)


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
