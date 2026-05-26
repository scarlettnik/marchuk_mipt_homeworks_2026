from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'


@dataclass(frozen=True)
class Message:
    role: Role
    content: str

    def as_payload(self) -> dict[str, str]:
        return {'role': self.role.value, 'content': self.content}
