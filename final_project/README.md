# Итоговый проект "GigaVibeMiptCode"

Консольный чат-бот для GigaChat OpenAI-compatible API.

Поддерживает streaming-ответы, историю диалога, лимиты контекста, вставку файлов через `@::path::`, chunk mode, `/reset` и `\q`.

## Сетап

```bash
cd final_project
uv sync
```

Запуск

```bash
uv run main.py
```

## Конфигурация

Несекретные настройки лежат в `config.yaml`:

```yml
api_host: https://gigachat.devices.sberbank.ru/api/v1
cert_path: linux_russian_trusted_root_ca_pem
model: GigaChat
limit_message: 20
limit_chars: 4000
temperature: 0.3
stream: true
system_prompt: |-
  You are an assistant for Python backend development tasks.
  Answer concisely and keep code changes focused.
```

Секреты лежат в `final_project/.env`; этот файл добавлен в `.gitignore`:

```env
API_KEY=your_authorization_key_here
```

`API_KEY` — это authorization key из Studio. Access token получать вручную не нужно:
бот делает это сам через OAuth, иначе токен пришлось бы обновлять каждые 30 минут.

TLS-сертификаты обязательны. Клиент всегда проверяет SSL через `cert_path`

## Команды

- `\q` — выход;
- `/reset` — очистка истории и экрана;
- `/filechunk` — обработка файла по абзацам;
- `/filechunk paragraph=3` — по 3 абзаца;
- `/filechunk len=150` — по 150 символов;
- `/filechunk paragraph=3 -y` — без ручного перехода между чанками.

## Проверки

```bash
uv sync --group test --group lint
uv run pytest tests
uv run mypy .
uv run ruff check . --config ruff.toml
```
