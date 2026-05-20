from final_project.gigavibe_mipt_code.models import Role
from final_project.gigavibe_mipt_code.session import ChatSession, ContextLimits


def test_prepare_turn_applies_message_limit() -> None:
    session = ChatSession(ContextLimits(message_count=3))
    first_turn = session.prepare_turn('first-user')
    session.commit_turn(first_turn.user_message, 'first-assistant')
    second_turn = session.prepare_turn('second-user')
    session.commit_turn(second_turn.user_message, 'second-assistant')

    prepared_turn = session.prepare_turn('third-user')

    assert [message.content for message in prepared_turn.messages] == [
        'second-user',
        'second-assistant',
        'third-user',
    ]


def test_prepare_turn_truncates_long_message_from_left() -> None:
    session = ChatSession(ContextLimits(char_count=5))

    prepared_turn = session.prepare_turn('abcdefgh')

    assert prepared_turn.user_message.content == 'defgh'
    assert prepared_turn.messages[-1].content == 'defgh'


def test_commit_turn_keeps_trimmed_history() -> None:
    session = ChatSession(ContextLimits(char_count=8))
    first_turn = session.prepare_turn('1234')
    session.commit_turn(first_turn.user_message, 'abcd')

    prepared_turn = session.prepare_turn('zz')

    assert [message.content for message in prepared_turn.messages] == ['abcd', 'zz']


def test_render_one_off_includes_system_prompt() -> None:
    session = ChatSession(
        limits=ContextLimits(char_count=20),
        system_prompt='system',
    )

    messages = session.render_one_off('payload')

    assert messages[0].role is Role.SYSTEM
    assert messages[1].content == 'payload'
