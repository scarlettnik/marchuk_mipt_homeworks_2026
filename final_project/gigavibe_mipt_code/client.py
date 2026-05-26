import json
import ssl
import time
from collections.abc import Iterable, Iterator
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
    _ssl_context_cache: ssl.SSLContext | None = field(default=None, init=False)

    def generate(self, messages: list[Message]) -> Iterator[str]:
        try:
            with urlopen(
                self._build_request(messages, stream=self.config.stream),
                timeout=self.timeout_seconds,
                context=self._ssl_context(),
            ) as response:
                if self.config.stream:
                    yield from _read_stream_response(response)
                else:
                    yield _read_completion_response(response.read())
        except (URLError, OSError) as error:
            raise LLMClientError(error) from error
        except (
            KeyError,
            IndexError,
            TypeError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise LLMClientError from error

    def _build_request(self, messages: list[Message], *, stream: bool) -> Request:
        return Request(
            url=f'{self.config.api_host}/chat/completions',
            data=_build_payload(self.config, messages, stream=stream),
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

    def _ssl_context(self) -> ssl.SSLContext:
        if self._ssl_context_cache is None:
            context = ssl.create_default_context()
            for cert_path in self.config.cert_paths:
                _load_verify_cert(context, cert_path.read_bytes(), str(cert_path))
            self._ssl_context_cache = context
        return self._ssl_context_cache


def _load_verify_cert(context: ssl.SSLContext, cert_data: bytes, cert_path: str) -> None:
    if cert_data.lstrip().startswith(b'-----BEGIN CERTIFICATE-----'):
        context.load_verify_locations(cafile=cert_path)
        return
    context.load_verify_locations(cadata=cert_data)


def _build_payload(config: AppConfig, messages: list[Message], *, stream: bool) -> bytes:
    payload = {
        'model': config.model,
        'messages': [message.as_payload() for message in messages],
        'stream': stream,
        'temperature': config.temperature,
    }
    return json.dumps(payload, ensure_ascii=False).encode('utf-8')


def _read_stream_response(lines: Iterable[bytes]) -> Iterator[str]:
    for raw_line in lines:
        line = raw_line.decode('utf-8').strip()
        if not line or line.startswith(':'):
            continue
        if not line.startswith('data:'):
            continue

        raw_payload = line.removeprefix('data:').strip()
        if raw_payload == '[DONE]':
            return

        payload = json.loads(raw_payload)
        content = payload['choices'][0].get('delta', {}).get('content')
        if content is not None:
            yield str(content)


def _read_completion_response(raw_response: bytes) -> str:
    payload = json.loads(raw_response)
    return str(payload['choices'][0]['message']['content'])


def _authorization_header(api_key: str) -> str:
    if api_key.startswith(('Basic ', 'Bearer ')):
        return api_key
    return f'Basic {api_key}'
