import base64
from dataclasses import dataclass
from tempfile import NamedTemporaryFile
from typing import Dict

from PIL import Image

from llm_utils.openai_api.message_content import MessageContent
from llm_utils.openai_api.message_content_type import MessageContentType


@dataclass
class ImageMessageContent(MessageContent):
    image: Image.Image

    def to_dict(self) -> Dict:
        with NamedTemporaryFile(mode="wb", suffix=".jpeg", delete=False) as tf:
            self.image.save(tf)
        with open(tf.name, "rb") as image_file:
            image_data = "data:image/jpeg;base64,%s" % base64.b64encode(image_file.read()).decode("utf-8")
        tf.close()
        return {"type": MessageContentType.IMAGE.value, "image_url": {"url": image_data}}

    def replace(self, needle, text):
        return self

    def __str__(self) -> str:
        return "IMAGE"
