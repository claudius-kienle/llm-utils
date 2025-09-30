import xml.etree.ElementTree as ET
from typing import Dict

from llm_utils.openai_api.message import Message
from llm_utils.openai_api.message_content_factory import MessageContentFactory
from llm_utils.openai_api.message_role import MessageRole
from llm_utils.openai_api.text_message_content import TextMessageContent
from llm_utils.openai_api.utils import ImageMap


class MessageFactory:
    def from_dict(self, dict_data: Dict) -> Message:
        content_dict = dict_data["content"]
        # try:
        #     # try to parse response as json
        #     content_dict = json.loads(content_dict.replace('\'', '\"'))
        #     if not isinstance(content_dict, (dict, list)):
        #         # if can't parse as dict, must be a text message
        #         content_dict = str(content_dict)
        # except json.decoder.JSONDecodeError:
        #     pass
        if not isinstance(content_dict, list):
            # a message with only one content might be flattened. Undo that flattening
            content_dict = [content_dict]

        content = [MessageContentFactory().from_dict(c) for c in content_dict]

        return Message(role=MessageRole(dict_data["role"]), content=content)

    def from_xml(self, xml: ET.Element, images: ImageMap) -> Message:
        role = xml.get("role")
        children = list(xml.iter("content"))
        if len(children) == 0:
            # text directly in message
            content = [TextMessageContent.from_string(text=xml.text)]
        else:
            content = [MessageContentFactory().from_xml(xml=content, images=images) for content in children]
        return Message(role=MessageRole(role), content=content)
