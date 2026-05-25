from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from .client import GigaChatClient
from .files import AttachmentExpander, ChunkSpec, TextChunker, TextFileReader
from .models import Message
from .session import ChatSession


class RequestInterrupted(Exception):
    pass


@dataclass
class AssistantService:
    client: GigaChatClient
    session: ChatSession
    attachment_expander: AttachmentExpander
    chunk_reader: TextFileReader
    chunker: TextChunker

    def chat(self, raw_text: str) -> Iterator[str]:
        prepared_text = self.attachment_expander.expand(raw_text)
        prepared_turn = self.session.prepare_turn(prepared_text)
        assistant_reply = ''
        for chunk in self._generate_stream(prepared_turn.messages):
            assistant_reply += chunk
            yield chunk

        self.session.commit_turn(prepared_turn.user_message, assistant_reply)

    def reset(self) -> None:
        self.session.clear()

    def load_chunks(self, file_path: Path, spec: ChunkSpec) -> list[str]:
        file_content = self.chunk_reader.read(file_path)
        return self.chunker.split(file_content, spec)

    def chunk_reply(self, prompt: str, chunk: str) -> Iterator[str]:
        chunk_request = f'{prompt}\n\n{chunk}'
        yield from self._generate_stream(self.session.render_one_off(chunk_request))

    def _generate_stream(self, messages: list[Message]) -> Iterator[str]:
        try:
            yield from self.client.generate(messages)
        except KeyboardInterrupt as error:
            raise RequestInterrupted from error
