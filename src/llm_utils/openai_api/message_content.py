from dataclasses import dataclass
from typing import Dict


@dataclass
class MessageContent:
    def to_dict(self) -> Dict:
        raise NotImplementedError()

    def replace(self, needle: str, text: str) -> "MessageContent":
        raise NotImplementedError()
