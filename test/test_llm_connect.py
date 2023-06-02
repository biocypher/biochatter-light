from chatgse._llm_connect import GptConversation, SystemMessage, HumanMessage, AIMessage
import pytest

def test_empty_messages():
    convo = GptConversation()
    assert convo.get_msg_json() == "[]"

def test_single_message():
    convo = GptConversation()
    convo.messages.append(SystemMessage(content="Hello, world!"))
    assert convo.get_msg_json() == '[{"system": "Hello, world!"}]'

def test_multiple_messages():
    convo = GptConversation()
    convo.messages.append(SystemMessage(content="Hello, world!"))
    convo.messages.append(HumanMessage(content="How are you?"))
    convo.messages.append(AIMessage(content="I'm doing well, thanks!"))
    assert convo.get_msg_json() == '[{"system": "Hello, world!"}, {"user": "How are you?"}, {"ai": "I\'m doing well, thanks!"}]'

def test_unknown_message_type():
    convo = GptConversation()
    convo.messages.append(None)
    with pytest.raises(ValueError):
        convo.get_msg_json()