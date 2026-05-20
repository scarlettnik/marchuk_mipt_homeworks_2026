from pathlib import Path

from .commands import (
    ChatCommand,
    CommandError,
    CommandParser,
    EmptyCommand,
    ExitCommand,
    FileChunkCommand,
    ResetCommand,
    EXIT_COMMAND,
)
from .client import GigaChatClient, LLMClientError
from .console import Terminal
from .config import CONFIG_ERROR, AppConfig, ConfigError, load_config
from .files import (
    MAX_ATTACHMENT_SIZE_BYTES,
    AttachmentExpander,
    FileError,
    TextChunker,
    TextFileReader,
)
from .services import AssistantService, RequestInterrupted
from .session import ChatSession, ContextLimits

APP_HEADER = 'GigaVibeMiptCode'
EXIT_HINT = f'{EXIT_COMMAND} exit'
NEXT_CHUNK_HINT = f'Enter | {EXIT_COMMAND}'


class ConsoleAssistant:
    def __init__(
        self,
        service: AssistantService,
        console: Terminal | None = None,
        parser: CommandParser | None = None,
    ) -> None:
        self._service = service
        self._console = Terminal() if console is None else console
        self._parser = CommandParser() if parser is None else parser

    @classmethod
    def from_config(cls, config: AppConfig) -> 'ConsoleAssistant':
        session = ChatSession(
            limits=ContextLimits(config.limit_message, config.limit_chars),
            system_prompt=config.system_prompt,
        )
        service = AssistantService(
            client=GigaChatClient(config),
            session=session,
            attachment_expander=AttachmentExpander(
                TextFileReader(max_size_bytes=MAX_ATTACHMENT_SIZE_BYTES),
            ),
            chunk_reader=TextFileReader(),
            chunker=TextChunker(),
        )
        return cls(service=service)

    def run(self) -> None:
        self._console.write(f'{APP_HEADER} | {EXIT_HINT} | /reset | /filechunk')
        while True:
            try:
                raw_input = self._console.read()
            except EOFError:
                self._console.write()
                return

            try:
                command = self._parser.parse(raw_input)
            except CommandError as error:
                self._console.write(str(error) or 'Ошибка команды.')
                continue

            if isinstance(command, EmptyCommand):
                continue
            if isinstance(command, ExitCommand):
                return
            if isinstance(command, ResetCommand):
                self._reset_chat()
                continue
            if isinstance(command, FileChunkCommand):
                self._run_file_chunk_mode(command)
                continue
            if isinstance(command, ChatCommand):
                self._handle_chat_message(command.text)

    def _handle_chat_message(self, user_input: str) -> None:
        try:
            assistant_reply = self._service.chat(user_input)
        except FileError as error:
            self._console.write(str(error))
            return
        except LLMClientError as error:
            self._console.write(str(error))
            return
        except RequestInterrupted:
            self._console.write('\nПрервано.')
            return

        self._console.write(assistant_reply)

    def _run_file_chunk_mode(self, command: FileChunkCommand) -> None:
        file_path = self._read_mode_value('Путь: ')
        if file_path is None:
            return

        try:
            chunks = self._service.load_chunks(Path(file_path).expanduser(), command.spec)
        except FileError as error:
            self._console.write(str(error))
            return

        chunk_prompt = self._read_mode_value('Задача: ')
        if chunk_prompt is None:
            return
        if not chunk_prompt.strip():
            self._console.write('Пустой prompt.')
            return

        if not chunks:
            self._console.write('Пустой файл.')
            return

        self._console.write('Старт.')
        for index, chunk in enumerate(chunks, 1):
            if not self._process_chunk(chunk_prompt, chunk):
                return
            if index == len(chunks):
                self._console.write('Сделано.')
                return
            if command.spec.auto_advance:
                continue
            if not self._wait_for_next_chunk():
                return

    def _process_chunk(self, chunk_prompt: str, chunk: str) -> bool:
        try:
            chunk_response = self._service.chunk_reply(chunk_prompt, chunk)
        except LLMClientError as error:
            self._console.write(str(error))
            return False
        except RequestInterrupted:
            self._console.write('\nПрервано.')
            return False

        self._console.write(chunk_response)
        return True

    def _wait_for_next_chunk(self) -> bool:
        while True:
            try:
                next_chunk_command = self._console.read()
            except EOFError:
                self._console.write()
                return False

            if next_chunk_command == '':
                return True
            if next_chunk_command.strip() == EXIT_COMMAND:
                return False
            self._console.write(NEXT_CHUNK_HINT)

    def _reset_chat(self) -> None:
        self._service.reset()
        self._console.clear()
        self._console.write(APP_HEADER)

    def _read_mode_value(self, prompt: str) -> str | None:
        try:
            value = self._console.read(prompt)
        except EOFError:
            self._console.write()
            return None
        if value.strip() == EXIT_COMMAND:
            return None
        return value


def run_application(config_path: Path) -> int:
    try:
        config = load_config(config_path)
    except ConfigError as error:
        print(str(error) or CONFIG_ERROR)
        return 1

    ConsoleAssistant.from_config(config).run()
    return 0
