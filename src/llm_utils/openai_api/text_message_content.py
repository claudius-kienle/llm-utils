import re
import textwrap
from dataclasses import dataclass
from typing import Dict

from llm_utils.openai_api.message_content import MessageContent
from llm_utils.openai_api.message_content_type import MessageContentType


@dataclass
class TextMessageContent(MessageContent):
    text: str

    def to_dict(self) -> Dict:
        return {"type": MessageContentType.TEXT.value, "text": self.text}

    @staticmethod
    def from_string(text: str) -> "TextMessageContent":
        text = textwrap.dedent(text)
        # text = re.sub(r"([^\n])\n([^\n])", r"\g<1> \g<2>", text)  # replace single \n with a whitespace
        # text = re.sub(r"\n(\n)+", r"\n", text)  # replace multiple \n with one \n
        # text = text.strip()  # remove leading and trailing whitespace and \n
        text = re.sub(r"^(\n)+", "", text)
        text = re.sub(r"(\n)+$", "", text)

        return TextMessageContent(text=text)

    def replace(self, needle, replacement):
        text = replace_text(needle=needle, replacement=replacement, text=self.text)
        return TextMessageContent(text=text)

    def __str__(self) -> str:
        return self.text
