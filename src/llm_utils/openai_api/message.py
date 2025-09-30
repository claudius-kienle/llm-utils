from dataclasses import dataclass
from typing import Dict, List

from python_utils.data_utils import fromdict

from llm_utils.openai_api.message_content import MessageContent
from llm_utils.openai_api.message_content_factory import MessageContentFactory
from llm_utils.openai_api.message_role import MessageRole


@dataclass
class Message:
    role: MessageRole
    content: List[MessageContent]

    def to_dict(self, cache: bool = False) -> Dict:
        if len(self.content) == 1:
            content_dict = self.content[0].to_dict()
            assert content_dict["type"] == "text"
            if cache:
                content_dict["cache_control"] = {"type": "ephemeral"}
            content_dict = content_dict["text"]
            # content_dict = [content_dict]
        else:
            assert not cache, "unusuported cache for multiple content items"
            content_dict = [content.to_dict() for content in self.content]

        return {"role": self.role.value, "content": content_dict}

    def __str__(self) -> str:
        content_repr = [c for cs in self.content for c in str(cs).split("\n")]
        content_repr = "\n    ".join(content_repr)
        return "- %s\n    %s" % (self.role.value, content_repr)

    def replace(self, needle: str, text: str) -> "Message":
        return Message(role=self.role, content=[c.replace(needle, text) for c in self.content])

    @staticmethod
    def from_json(data: Dict) -> "MessageContent":
        if isinstance(data["content"], str):
            data["content"] = [{"text": data["content"]}]
        return Message(
            role=fromdict(data["role"], MessageRole),
            content=[fromdict(item, MessageContentFactory()(item)) for item in data["content"]],
        )

    @property
    def text(self) -> str:
        assert len(self.content) == 1, "Message.text only works for single content messages"
        return self.content[0].text
