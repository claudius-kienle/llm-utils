from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from python_utils.communication_utils.utils.parsing_utils import obj_to_xml

from llm_utils.openai_api.message import Message
from llm_utils.openai_api.message_role import MessageRole
from llm_utils.openai_api.text_message_content import TextMessageContent


@dataclass
class Chat:
    messages: List[Message]

    def to_dict(self, cache: bool = False) -> Dict:
        response = []
        n_cached = 0
        for message in self.messages:
            cache = False
            if n_cached < 4:
                cache = message.role == MessageRole.ASSISTANT
                if cache:
                    n_cached += 1

            response.append(message.to_dict(cache=cache))
        return response
        return [
            message.to_dict(cache=cache if i == len(self.messages) - 1 else False)
            for i, message in enumerate(self.messages)
        ]

    def to_xml(self) -> Dict:
        return obj_to_xml(self)

    def add_message(self, message: Message) -> "Chat":
        assert isinstance(message, Message)
        return Chat(messages=self.messages + [message])

    def add_user_text(self, text: str) -> "Chat":
        return self.add_message(Message(role=MessageRole.USER, content=[TextMessageContent(text=text)]))

    def __str__(self) -> str:
        return "\n|".join(map(str, self.messages))

    def replace(self, needle: str, replacement: str) -> "Chat":
        return Chat(messages=[m.replace(needle, replacement) for m in self.messages])

    def copy_with(self, *, messages: Optional[List[Message]] = None) -> "Chat":
        return Chat(messages=messages if messages is not None else self.messages)

    def last_message(self) -> str:
        last_content = self.messages[-1].content[0]
        assert isinstance(last_content, TextMessageContent)
        return last_content.text

    def replace_last_message(self, text: str) -> "Chat":
        last_message = self.messages[-1]
        assert len(last_message.content) == 1
        new_messages = self.messages[:-1] + [Message(role=last_message.role, content=[TextMessageContent(text=text)])]
        return self.copy_with(messages=new_messages)

    @staticmethod
    def concat_chats(chat1: "Chat", chat2: "Chat") -> "Chat":
        return Chat(messages=chat1.messages + chat2.messages)

    def get_all_after(self, prior_chat: "Chat") -> "Chat":
        assert all(
            c_m == p_m for c_m, p_m in zip(self.messages, prior_chat.messages)
        ), "prior chat is not parent of current chat"
        return Chat(messages=self.messages[len(prior_chat.messages) :])

    def copy_with_system_message_only(self) -> "Chat":
        system_message = next(filter(lambda m: m.role == MessageRole.SYSTEM, self.messages), None)
        if system_message is None:
            assert len(self.messages) == 0, "No system message found, but chat is not empty"
            return Chat(messages=[])
        else:
            return Chat(messages=[system_message])

    def get_system_message(self) -> str:
        for message in self.messages:
            if message.role == MessageRole.SYSTEM:
                assert len(message.content) == 1
                return message.content[0].text
        raise ValueError("No system message found")

    def replace_system_message(self, other_chat: Union[str, "Chat"]) -> "Chat":
        if isinstance(other_chat, Chat):
            other_sys_msg = other_chat.get_system_message()
        else:
            other_sys_msg = other_chat
        new_messages = []
        found_system_message = False
        for message in self.messages:
            if message.role == MessageRole.SYSTEM:
                new_messages.append(Message(role=MessageRole.SYSTEM, content=[TextMessageContent(text=other_sys_msg)]))
                found_system_message = True
            else:
                new_messages.append(message)
        if not found_system_message:
            raise ValueError("No system message found to replace")

        return self.copy_with(messages=new_messages)

    def cap_after_first_assistant_message(self) -> "Chat":
        """Returns a new chat that only contains messages up to the first assistant message."""
        for i, message in enumerate(self.messages):
            if message.role == MessageRole.ASSISTANT:
                return self.copy_with(messages=self.messages[: i + 1])
        return self.copy_with(messages=self.messages)
