import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Terminal:
    prompt: str = '>>> '

    def read(self, prompt: str | None = None) -> str:
        return input(self.prompt if prompt is None else prompt)

    def write(self, text: str = '') -> None:
        print(text)

    def clear(self) -> None:
        command = 'cls' if os.name == 'nt' else 'clear'
        os.system(command)

