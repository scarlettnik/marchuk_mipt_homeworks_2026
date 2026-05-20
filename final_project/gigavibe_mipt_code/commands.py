from dataclasses import dataclass

from .files import ChunkSpec

EXIT_COMMAND = r'\q'
RESET_COMMAND = '/reset'
FILE_CHUNK_COMMANDS = {'/file_chunk', '/filechunk'}


class CommandError(Exception):
    pass


@dataclass(frozen=True)
class EmptyCommand:
    pass


@dataclass(frozen=True)
class ExitCommand:
    pass


@dataclass(frozen=True)
class ResetCommand:
    pass


@dataclass(frozen=True)
class ChatCommand:
    text: str


@dataclass(frozen=True)
class FileChunkCommand:
    spec: ChunkSpec


AppCommand = EmptyCommand | ExitCommand | ResetCommand | ChatCommand | FileChunkCommand


class CommandParser:
    def parse(self, raw_text: str) -> AppCommand:
        normalized = raw_text.strip()
        if not normalized:
            return EmptyCommand()
        if normalized == EXIT_COMMAND:
            return ExitCommand()
        if normalized == RESET_COMMAND:
            return ResetCommand()

        command_name = normalized.split(maxsplit=1)[0]
        if command_name in FILE_CHUNK_COMMANDS:
            return FileChunkCommand(self._parse_chunk_spec(normalized))
        return ChatCommand(raw_text)

    def _parse_chunk_spec(self, command: str) -> ChunkSpec:
        tokens = command.split()
        paragraph_count: int | None = None
        chunk_length: int | None = None
        auto_advance = False

        for token in tokens[1:]:
            if token == '-y':
                auto_advance = True
                continue

            option_name, separator, option_value = token.partition('=')
            if separator != '=' or option_name not in {'paragraph', 'len'}:
                raise CommandError

            parsed_value = _parse_positive_int(option_value)
            if option_name == 'paragraph':
                if paragraph_count is not None:
                    raise CommandError
                paragraph_count = parsed_value
                continue

            if chunk_length is not None:
                raise CommandError
            chunk_length = parsed_value

        if paragraph_count is not None and chunk_length is not None:
            raise CommandError
        if paragraph_count is None and chunk_length is None:
            paragraph_count = 1

        return ChunkSpec(
            paragraph_count=paragraph_count,
            chunk_length=chunk_length,
            auto_advance=auto_advance,
        )


def _parse_positive_int(raw_value: str) -> int:
    try:
        parsed_value = int(raw_value)
    except ValueError as error:
        raise CommandError from error

    if parsed_value <= 0:
        raise CommandError
    return parsed_value
