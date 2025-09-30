from dataclasses import dataclass
from typing import List

from llm_utils.openai_api.message import Message
from llm_utils.openai_api.message_content import MessageContent
from llm_utils.openai_api.message_role import MessageRole


@dataclass
class SystemMessage(Message):
    def __init__(self, content: List[MessageContent]):
        return super().__init__(role=MessageRole.SYSTEM, content=content)
