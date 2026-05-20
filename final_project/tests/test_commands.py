import pytest

from final_project.gigavibe_mipt_code.commands import (
    ChatCommand,
    CommandError,
    CommandParser,
    EmptyCommand,
    ExitCommand,
    FileChunkCommand,
    ResetCommand,
)
from final_project.gigavibe_mipt_code.files import ChunkSpec


def test_command_parser_returns_empty_command_for_blank_input() -> None:
    parser = CommandParser()

    command = parser.parse('   ')

    assert isinstance(command, EmptyCommand)


def test_command_parser_parses_reset_and_exit() -> None:
    parser = CommandParser()

    assert isinstance(parser.parse('/reset'), ResetCommand)
    assert isinstance(parser.parse(r'\q'), ExitCommand)


def test_command_parser_parses_chat_message() -> None:
    parser = CommandParser()

    command = parser.parse('hello')

    assert command == ChatCommand('hello')


def test_command_parser_parses_chunk_command() -> None:
    parser = CommandParser()

    command = parser.parse('/filechunk len=4 -y')

    assert command == FileChunkCommand(ChunkSpec(chunk_length=4, auto_advance=True))


def test_command_parser_rejects_mixed_chunk_modes() -> None:
    parser = CommandParser()

    with pytest.raises(CommandError):
        parser.parse('/filechunk paragraph=2 len=4')
