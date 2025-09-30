import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UsageCall:
    input_tokens: int
    input_tokens_cached: int
    output_tokens: int
    output_tokens_cached: int
    call_id: Optional[str] = None

    def to_dumps(self) -> str:
        return {
            "input_tokens": self.input_tokens,
            "input_tokens_cached": self.input_tokens_cached,
            "output_tokens": self.output_tokens,
            "output_tokens_cached": self.output_tokens_cached,
            "call_id": self.call_id,
        }


@dataclass
class Usage:
    calls: List[UsageCall] = field(default_factory=list)

    def add_call(self, response_usage: dict, call_id: Optional[str]):
        if "prompt_tokens" in response_usage:
            input_tokens = response_usage["prompt_tokens"]
        else:
            input_tokens = response_usage["input_tokens"]

        if "prompt_tokens_details" in response_usage:
            input_tokens_cached = response_usage["prompt_tokens_details"]["cached_tokens"]
        elif "cache_read_input_tokens" in response_usage:
            input_tokens_cached = response_usage["cache_read_input_tokens"]
        else:
            input_tokens_cached = 0

        if "completion_tokens" in response_usage:
            output_tokens = response_usage["completion_tokens"]
        else:
            output_tokens = response_usage["output_tokens"]
        output_tokens_cached = 0

        self.calls.append(
            UsageCall(
                input_tokens=input_tokens,
                input_tokens_cached=input_tokens_cached,
                output_tokens_cached=output_tokens_cached,
                output_tokens=output_tokens,
                call_id=call_id,
            )
        )

    def reset(self):
        self.calls = []

    def to_json(self) -> dict:
        return {"calls": list(map(lambda c: c.to_dumps(), self.calls))}

    def to_dumps(self) -> str:
        return json.dumps(self.to_json())
