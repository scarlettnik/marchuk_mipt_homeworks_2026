import json
import ssl
import time
from dataclasses import dataclass, field
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from .config import AppConfig
from .models import Message

TOKEN_REFRESH_GAP_SECONDS = 60


class LLMClientError(Exception):
    pass


@dataclass
class GigaChatClient:
    config: AppConfig
    timeout_seconds: int = 300
    _access_token: str | None = field(default=None, init=False)
    _expires_at: int = field(default=0, init=False)

    def generate(self, messages: list[Message]) -> str:
        try:
            with urlopen(
                self._build_request(messages),
                timeout=self.timeout_seconds,
                context=self._ssl_context(),
            ) as response:
                payload = json.loads(response.read())
                return str(payload['choices'][0]['message']['content'])
        except (URLError, OSError) as error:
            raise LLMClientError(error) from error
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise LLMClientError from error

    def _build_request(self, messages: list[Message]) -> Request:
        return Request(
            url=f'{self.config.api_host}/chat/completions',
            data=_build_payload(self.config, messages),
            headers={
                'Authorization': f'Bearer {self._get_access_token()}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )

    def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._expires_at - TOKEN_REFRESH_GAP_SECONDS:
            return self._access_token

        request = Request(
            url=self.config.token_url,
            data=urlencode({'scope': self.config.auth_scope}).encode(),
            headers={
                'Accept': 'application/json',
                'Authorization': _authorization_header(self.config.api_key),
                'Content-Type': 'application/x-www-form-urlencoded',
                'RqUID': str(uuid4()),
            },
            method='POST',
        )

        with urlopen(
            request,
            timeout=self.timeout_seconds,
            context=self._ssl_context(),
        ) as response:
            payload = json.loads(response.read())
            self._access_token = str(payload['access_token'])
            self._expires_at = int(payload['expires_at']) // 1000
            return self._access_token

    def _ssl_context(self) -> ssl.SSLContext | None:
        if self.config.verify_ssl:
            return None
        return ssl._create_unverified_context()


def _build_payload(config: AppConfig, messages: list[Message]) -> bytes:
    payload = {
        'model': config.model,
        'messages': [message.as_payload() for message in messages],
        'temperature': config.temperature,
    }
    return json.dumps(payload, ensure_ascii=False).encode('utf-8')


def _authorization_header(api_key: str) -> str:
    if api_key.startswith(('Basic ', 'Bearer ')):
        return api_key
    return f'Basic {api_key}'
