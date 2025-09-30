import re
import textwrap
from typing import Tuple, Union


def replace_text(text: str, needle: Union[str, Tuple[int]], replacement: str) -> str:
    matches = [needle]
    while True:
        if isinstance(needle, str):
            matches = [m.span() for m in re.finditer(re.escape(needle), text)]
            matches = [(start_idx, end_idx) for start_idx, end_idx in matches if start_idx != -1]
            if len(matches) == 0:
                break
            match = matches[0]
        else:
            if len(matches) == 0:
                break
            match = matches.pop()

        start_idx, end_idx = match
        last_line = text[:start_idx].split("\n")[-1]  # not splitlines() since removes empty lines
        # if len(last_line.strip()) != 0:
        # only copy whitespace
        # last_line = ""

        replacement_w_prefix = textwrap.indent(text=replacement, prefix=last_line)
        start_idx = start_idx - len(last_line)

        text = text[:start_idx] + replacement_w_prefix + text[end_idx:]

    return text
