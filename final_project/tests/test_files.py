from pathlib import Path

import pytest

from final_project.gigavibe_mipt_code.files import (
    AttachmentExpander,
    ChunkSpec,
    FileError,
    MAX_ATTACHMENT_SIZE_BYTES,
    TextChunker,
    TextFileReader,
)

EXPANDER = AttachmentExpander(TextFileReader(max_size_bytes=MAX_ATTACHMENT_SIZE_BYTES))
CHUNKER = TextChunker()


def test_attachment_expander_inserts_file_contents(tmp_path: Path) -> None:
    source_file = tmp_path / 'a.txt'
    source_file.write_text('b\n', encoding='utf-8')

    assert EXPANDER.expand(f'a @::{source_file}::') == 'a\nb\n'


def test_attachment_expander_rejects_large_files(tmp_path: Path) -> None:
    source_file = tmp_path / 'large.txt'
    source_file.write_bytes(b'a' * (MAX_ATTACHMENT_SIZE_BYTES + 1))

    with pytest.raises(FileError):
        EXPANDER.expand(f'a @::{source_file}::')


def test_split_into_chunks_by_paragraphs() -> None:
    text = 'a\n\nb\n\nc'

    assert CHUNKER.split(text, ChunkSpec(paragraph_count=2)) == ['a\n\nb', 'c']


def test_split_into_chunks_by_length() -> None:
    assert CHUNKER.split('abcdefghij', ChunkSpec(chunk_length=4)) == ['abcd', 'efgh', 'ij']
