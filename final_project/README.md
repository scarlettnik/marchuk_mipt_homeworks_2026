# Итоговый проект "GigaVibeMiptCode"

Консольный чат-бот для GigaChat OpenAI-compatible API.

Поддерживает историю диалога, лимиты контекста, вставку файлов через `@::path::`, chunk mode, `/reset` и `\q`.

## Конфигурация

`config.yaml`:

```yml
api_key: your_authorization_key_here
api_host: https://gigachat.devices.sberbank.ru/api/v1
model: GigaChat
limit_message: 20
limit_chars: 4000
temperature: 0.3
verify_ssl: false
system_prompt: You are an assistant for Python backend development tasks.
```

`api_key` — это authorization key из Studio. Access token получать вручную не нужно:
бот делает это сам через OAuth. Иначе пришлось обновлять каждый 30 минутю
В идеальное мире нужно добавить сертификат, но по умолчанию прописана работа без сертификата

## Команды

- `\q` — выход;
- `/reset` — очистка истории и экрана;
- `/filechunk` — обработка файла по абзацам;
- `/filechunk paragraph=3` — по 3 абзаца;
- `/filechunk len=150` — по 150 символов;
- `/filechunk paragraph=3 -y` — без ручного перехода между чанками.

## Проверки

```bash
python -m pytest final_project/tests
python -m mypy final_project
ruff check final_project --config final_project/ruff.toml
```
