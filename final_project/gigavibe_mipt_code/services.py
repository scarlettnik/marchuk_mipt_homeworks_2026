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

    def chat(self, raw_text: str) -> str:
        prepared_text = self.attachment_expander.expand(raw_text)
        prepared_turn = self.session.prepare_turn(prepared_text)
        assistant_reply = self._generate(prepared_turn.messages)
        self.session.commit_turn(prepared_turn.user_message, assistant_reply)
        return assistant_reply

    def reset(self) -> None:
        self.session.clear()

    def load_chunks(self, file_path: Path, spec: ChunkSpec) -> list[str]:
        file_content = self.chunk_reader.read(file_path)
        return self.chunker.split(file_content, spec)

    def chunk_reply(self, prompt: str, chunk: str) -> str:
        chunk_request = f'{prompt}\n\n{chunk}'
        return self._generate(self.session.render_one_off(chunk_request))

    def _generate(self, messages: list[Message]) -> str:
        try:
            return self.client.generate(messages)
        except KeyboardInterrupt as error:
            raise RequestInterrupted from error
