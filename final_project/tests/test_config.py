from pathlib import Path

import pytest

from final_project.gigavibe_mipt_code.config import ConfigError, load_config

ENV_KEYS = (
    'API_HOST',
    'API_KEY',
    'AUTH_SCOPE',
    'CERT_PATH',
    'LIMIT_CHARS',
    'LIMIT_MESSAGE',
    'MODEL',
    'TEMPERATURE',
    'TOKEN_URL',
)


def test_load_config_from_yaml_and_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    cert_path = _write_cert(tmp_path)
    _write_dotenv(tmp_path, 'dotenv-token')
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        '\n'.join(
            (
                'api_host: https://gigachat.devices.sberbank.ru/api/v1',
                'limit_message: 10',
                'limit_chars: 2000',
                'temperature: 0.2',
                'system_prompt: Test prompt',
            ),
        ),
        encoding='utf-8',
    )

    config = load_config(config_path)

    assert config.api_key == 'dotenv-token'
    assert config.api_host == 'https://gigachat.devices.sberbank.ru/api/v1'
    assert config.cert_paths == (cert_path.resolve(),)
    assert config.auth_scope == 'GIGACHAT_API_PERS'
    assert config.token_url == 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
    assert config.limit_message == 10
    assert config.limit_chars == 2000
    assert config.temperature == 0.2
    assert config.system_prompt == 'Test prompt'


def test_environment_overrides_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    _write_cert(tmp_path)
    _write_dotenv(tmp_path, 'dotenv-token')
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        '\n'.join(
            (
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

    config = load_config(config_path)

    assert config.api_key == 'env-token'
    assert config.api_host == 'https://env.example/v1'
    assert config.auth_scope == 'CUSTOM_SCOPE'
    assert config.token_url == 'https://token.example/oauth'
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
    _write_cert(tmp_path)
    _write_dotenv(tmp_path, 'dotenv-token')
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        '\n'.join(
            (
                'api_host: https://gigachat.devices.sberbank.ru/api/v1',
                'limit_chars: 0',
            ),
        ),
        encoding='utf-8',
    )

    with pytest.raises(ConfigError):
        load_config(config_path)


def test_load_config_rejects_secret_in_yaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_env(monkeypatch)
    _write_cert(tmp_path)
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        '\n'.join(
            (
                'api_key: yaml-token',
                'api_host: https://gigachat.devices.sberbank.ru/api/v1',
            ),
        ),
        encoding='utf-8',
    )

    with pytest.raises(ConfigError):
        load_config(config_path)


def test_load_config_rejects_verify_ssl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_env(monkeypatch)
    _write_cert(tmp_path)
    _write_dotenv(tmp_path, 'dotenv-token')
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        '\n'.join(
            (
                'api_host: https://gigachat.devices.sberbank.ru/api/v1',
                'verify_ssl: false',
            ),
        ),
        encoding='utf-8',
    )

    with pytest.raises(ConfigError):
        load_config(config_path)


def test_load_config_requires_certificate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_env(monkeypatch)
    _write_dotenv(tmp_path, 'dotenv-token')
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        'api_host: https://gigachat.devices.sberbank.ru/api/v1',
        encoding='utf-8',
    )

    with pytest.raises(ConfigError):
        load_config(config_path)


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _write_dotenv(tmp_path: Path, api_key: str) -> None:
    (tmp_path / '.env').write_text(f'API_KEY={api_key}', encoding='utf-8')


def _write_cert(tmp_path: Path) -> Path:
    cert_dir = tmp_path / 'linux_russian_trusted_root_ca_pem'
    cert_dir.mkdir()
    cert_path = cert_dir / 'root.crt'
    cert_path.write_text('test certificate', encoding='utf-8')
    return cert_path
