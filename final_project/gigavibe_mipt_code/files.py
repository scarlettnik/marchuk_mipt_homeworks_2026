import re
from dataclasses import dataclass
from pathlib import Path

FILE_REFERENCE_PATTERN = re.compile(r'@::(.*?)::')
MAX_ATTACHMENT_SIZE_BYTES = 5 * 1024 * 1024
TEXT_ENCODINGS = ('utf-8', 'utf-8-sig', 'cp1251')


class FileError(Exception):
    pass


@dataclass(frozen=True)
class ChunkSpec:
    paragraph_count: int | None = None
    chunk_length: int | None = None
    auto_advance: bool = False


@dataclass(frozen=True)
class TextFileReader:
    max_size_bytes: int | None = None
    encodings: tuple[str, ...] = TEXT_ENCODINGS

    def read(self, path: Path) -> str:
        if not path.exists():
            raise FileError(f'Файл не найден: {path}')
        if not path.is_file():
            raise FileError(f'Указан не файл: {path}')

        file_size = path.stat().st_size
        if self.max_size_bytes is not None and file_size > self.max_size_bytes:
            size_in_mb = self.max_size_bytes / (1024 * 1024)
            raise FileError(f'Файл {path} превышает лимит {size_in_mb:.0f}.')

        return self._decode(path.read_bytes(), path)

    def _decode(self, content: bytes, path: Path) -> str:
        if b'\x00' in content:
            raise FileError(f'Файл {path} не текстовый.')

        for encoding in self.encodings:
            try:
                decoded_text = content.decode(encoding)
            except UnicodeDecodeError:
                continue
            if _looks_like_text(decoded_text):
                return decoded_text

        raise FileError(f'Не удалось прочитать как текст: {path}')


@dataclass(frozen=True)
class AttachmentExpander:
    file_reader: TextFileReader

    def expand(self, text: str) -> str:
        if not FILE_REFERENCE_PATTERN.search(text):
            return text

        def replace(match: re.Match[str]) -> str:
            raw_path = match.group(1).strip()
            if not raw_path:
                raise FileError('Пустой путь в @::filepath::.')

            content = self.file_reader.read(Path(raw_path).expanduser())
            if match.start() == 0:
                return content
            return f'\n{content}'

        expanded_text = FILE_REFERENCE_PATTERN.sub(replace, text)
        return expanded_text.replace(' \n', '\n')


class TextChunker:
    def split(self, text: str, spec: ChunkSpec) -> list[str]:
        normalized_text = text.strip()
        if not normalized_text:
            return []

        if spec.chunk_length is not None:
            return [
                normalized_text[index : index + spec.chunk_length]
                for index in range(0, len(normalized_text), spec.chunk_length)
            ]

        paragraph_count = spec.paragraph_count or 1
        paragraphs = _split_paragraphs(normalized_text)
        return [
            '\n\n'.join(paragraphs[index : index + paragraph_count])
            for index in range(0, len(paragraphs), paragraph_count)
        ]


def _looks_like_text(content: str) -> bool:
    if not content:
        return True

    printable_count = 0
    for symbol in content:
        if symbol.isprintable() or symbol in {'\n', '\r', '\t'}:
            printable_count += 1
    return printable_count / len(content) >= 0.9


def _split_paragraphs(text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r'\n\s*\n+', text) if part.strip()]
    if len(paragraphs) > 1:
        return paragraphs
    return [line.strip() for line in text.splitlines() if line.strip()]

