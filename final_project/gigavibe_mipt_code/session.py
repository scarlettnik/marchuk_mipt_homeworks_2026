from dataclasses import dataclass, field

from .models import Message, Role


@dataclass(frozen=True)
class ContextLimits:
    message_count: int | None = None
    char_count: int | None = None


@dataclass(frozen=True)
class PreparedTurn:
    user_message: Message
    messages: list[Message]


@dataclass
class MessageWindow:
    limits: ContextLimits
    _messages: list[Message] = field(default_factory=list, init=False)

    def clear(self) -> None:
        self._messages.clear()

    def preview(self, message: Message) -> list[Message]:
        return self._trim([*self._messages, message])

    def standalone(self, message: Message) -> list[Message]:
        return self._trim([message])

    def append(self, message: Message) -> None:
        self._messages = self._trim([*self._messages, message])

    def _trim(self, messages: list[Message]) -> list[Message]:
        trimmed_messages = list(messages)
        if not trimmed_messages:
            return trimmed_messages

        char_limit = self.limits.char_count
        if char_limit is not None:
            trimmed_messages[-1] = _clip_message(trimmed_messages[-1], char_limit)

        while True:
            changed = False
            if (
                self.limits.message_count is not None
                and len(trimmed_messages) > self.limits.message_count
            ):
                trimmed_messages.pop(0)
                changed = True

            if char_limit is not None and _count_chars(trimmed_messages) > char_limit:
                if len(trimmed_messages) == 1:
                    trimmed_messages[0] = _clip_message(trimmed_messages[0], char_limit)
                else:
                    trimmed_messages.pop(0)
                changed = True

            if not changed:
                return trimmed_messages


@dataclass
class ChatSession:
    limits: ContextLimits
    system_prompt: str | None = None
    _window: MessageWindow = field(init=False)

    def __post_init__(self) -> None:
        self._window = MessageWindow(self.limits)

    def clear(self) -> None:
        self._window.clear()

    def prepare_turn(self, user_text: str) -> PreparedTurn:
        user_message = Message(Role.USER, user_text)
        prepared_messages = self._window.preview(user_message)
        prepared_user_message = prepared_messages[-1]
        return PreparedTurn(
            user_message=prepared_user_message,
            messages=self._with_system_prompt(prepared_messages),
        )

    def commit_turn(self, user_message: Message, assistant_text: str) -> None:
        self._window.append(user_message)
        self._window.append(Message(Role.ASSISTANT, assistant_text))

    def render_one_off(self, user_text: str) -> list[Message]:
        user_message = Message(Role.USER, user_text)
        return self._with_system_prompt(self._window.standalone(user_message))

    def _with_system_prompt(self, messages: list[Message]) -> list[Message]:
        if not self.system_prompt:
            return messages
        system_message = Message(Role.SYSTEM, self.system_prompt)
        return [system_message, *messages]


def _clip_message(message: Message, char_limit: int) -> Message:
    if len(message.content) <= char_limit:
        return message
    return Message(message.role, message.content[-char_limit:])


def _count_chars(messages: list[Message]) -> int:
    return sum(len(message.content) for message in messages)
