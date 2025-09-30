import xml.etree.ElementTree as ET
from typing import Any

from llm_utils.openai_api.image_message_content import ImageMessageContent
from llm_utils.openai_api.message_content import MessageContent
from llm_utils.openai_api.message_content_type import MessageContentType
from llm_utils.openai_api.text_message_content import TextMessageContent
from llm_utils.openai_api.utils import ImageMap


class MessageContentFactory:
    def from_dict(self, data: Any) -> MessageContent:
        if isinstance(data, str):
            return TextMessageContent.from_string(text=data)
        elif isinstance(data, dict):
            assert "type" in data
            message_type = data["type"]
            if message_type == MessageContentType.TEXT:
                return TextMessageContent.from_string(text=data["text"])
            else:
                raise NotImplementedError()

    def from_xml(self, xml: ET.Element, images: ImageMap) -> MessageContent:
        message_type = xml.get("type", "text")
        if message_type == "text":
            return TextMessageContent.from_string(text=xml.text)
        elif message_type == "image":
            image_id = xml.get("id")
            return ImageMessageContent(image=images[image_id])
        else:
            raise NotImplementedError()

    def __call__(self, data):
        if "text" in data:
            return TextMessageContent
        else:
            raise ImageMessageContent
