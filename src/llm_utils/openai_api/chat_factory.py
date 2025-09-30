import xml.etree.ElementTree as ET
from typing import Dict, Optional

from python_utils.data_utils import asdict, fromdict

from llm_utils.openai_api.chat import Chat
from llm_utils.openai_api.message_factory import MessageFactory
from llm_utils.openai_api.utils import ImageMap


class ChatFactory:
    def from_xml_string(self, xml_data: str, images: Optional[ImageMap] = None) -> Chat:
        return self.from_xml(xml=ET.fromstring(xml_data), images=images)

    def from_xml(self, xml: ET.Element, images: Optional[ImageMap] = None) -> Chat:
        if images is None:
            images = {}
        children = list(xml.iter("message"))
        messages = [MessageFactory().from_xml(xml=message, images=images) for message in children]
        return Chat(messages=messages)

    def to_json(self, chat: Chat) -> Dict:
        return asdict(chat)

    def from_json(self, data: Dict) -> "Chat":
        if isinstance(data, list):
            data = {"messages": data}
        return fromdict(data, Chat)
