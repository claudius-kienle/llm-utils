from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional

from llm_utils.openai_api.chat import Chat
from llm_utils.openai_api.chat_factory import ChatFactory
from llm_utils.openai_api.utils import ImageMap
from llm_utils.prompt_generation.utils import replace_text


@dataclass
class Prompt:
    prompt: str

    def to_chat(self, images: Optional[ImageMap] = None) -> Chat:
        # assert re.search(r"\{[\w\-\_]+\}", self.prompt) is None, "Prompt contains unreplaced placeholders"
        return ChatFactory().from_xml_string(self.prompt, images=images)

    def replace_all(self, **kwargs):
        for needle, replacement in kwargs.items():
            assert "{" not in needle and "}" not in needle
            self.replace(needle="{%s}" % needle, replacement=replacement)

    def replace(self, needle: str, replacement: str):
        escaped_replacement = (
            replacement.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
        self.prompt = replace_text(needle=needle, replacement=escaped_replacement, text=self.prompt)

    @staticmethod
    def load_from_file(file_path: Path):
        with open(file_path) as f:
            prompt = f.read()
        return Prompt(prompt=prompt)
