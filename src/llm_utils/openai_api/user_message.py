from dataclasses import dataclass
from typing import List, Union

from llm_utils.openai_api.message import Message
from llm_utils.openai_api.message_content import MessageContent
from llm_utils.openai_api.message_role import MessageRole


@dataclass
class UserMessage(Message):
    def __init__(self, content: Union[List[MessageContent], MessageContent]):
        if isinstance(content, MessageContent):
            content = [content]
        return super().__init__(role=MessageRole.USER, content=content)
