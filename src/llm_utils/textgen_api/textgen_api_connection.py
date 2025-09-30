import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class TextGenLLMConnection:
    identifier: str
    ip_address: str
    port: int
    use_https: bool
    model: str
    additional_headers: Dict[str, str]
    path: str = "v1/chat/completions"
    cheap: bool = False
    has_seed: bool = True
    max_tokens: Optional[int] = None
    ratelimit_remaining_tokens_key: Optional[str] = "x-ratelimit-remaining-tokens"
    ratelimit_reset_key: Optional[str] = "x-ratelimit-reset-tokens"
    additional_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.model_dir = self.model.replace("/", "-").replace(":", "-")

    @property
    def host(self) -> str:
        return self.ip_address + ":" + str(self.port)

    @property
    def protocol(self) -> str:
        return "https" if self.use_https else "http"

    @property
    def uri(self) -> str:
        return f"{self.protocol}://{self.host}/{self.path}"

    @staticmethod
    def self_hosted(ip_address: str, port: int) -> "TextGenLLMConnection":
        return TextGenLLMConnection(
            identifier="self-hosted",
            ip_address=ip_address,
            port=port,
            use_https=False,
            model="google/gemma-3-1b-it",
            additional_headers={},
            cheap=True,
            ratelimit_remaining_tokens_key=None,
            ratelimit_reset_key=None,
        )

    @staticmethod
    def openai(model_name: str, api_key: Optional[str] = None) -> "TextGenLLMConnection":
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        assert api_key is not None, "OpenAI API key must be set in environment variable OPENAI_API_KEY"
        return TextGenLLMConnection(
            identifier=model_name,
            ip_address="api.openai.com",
            port=443,
            use_https=True,
            model=model_name,
            additional_headers={"Authorization": "Bearer %s" % api_key},
            cheap=False,
        )

    @staticmethod
    def cerebras(model_name: str, api_key: Optional[str] = None) -> "TextGenLLMConnection":
        if api_key is None:
            api_key = os.getenv("CEREBRAS_API_KEY")
        assert api_key is not None, "Cerebras API key must be set in environment variable CEREBRAS_API_KEY"
        return TextGenLLMConnection(
            identifier=model_name,
            ip_address="api.cerebras.ai",
            port=443,
            use_https=True,
            model=model_name,
            additional_headers={"Authorization": "Bearer %s" % api_key},
            cheap=False,
        )

    @staticmethod
    def openrouter(model_name: str, api_key: Optional[str] = None) -> "TextGenLLMConnection":
        if api_key is None:
            api_key = os.getenv("OPENROUTER_API_KEY")
        assert api_key is not None, "OpenRouter API key must be set in environment variable OPENROUTER_API_KEY"
        return TextGenLLMConnection(
            identifier=model_name,
            ip_address="openrouter.ai",
            path="api/v1/chat/completions",
            port=443,
            use_https=True,
            model=model_name,
            additional_headers={"Authorization": "Bearer %s" % api_key},
            cheap=False,
            additional_params={
                "provider": {
                    "sort": "throughput",
                },
                "usage": {
                    "include": True,
                },
            },
        )

    @staticmethod
    def anthropic(model_name: str, api_key: Optional[str] = None) -> "TextGenLLMConnection":
        if api_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
        assert api_key is not None, "Anthropic API key must be set in environment variable ANTHROPIC_API_KEY"
        return TextGenLLMConnection(
            identifier=model_name,
            ip_address="api.anthropic.com",
            port=443,
            use_https=True,
            has_seed=False,
            model=model_name,
            additional_headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            cheap=False,
            path="v1/messages",
            max_tokens=8192,
            ratelimit_remaining_tokens_key="anthropic-ratelimit-tokens-remaining",
            ratelimit_reset_key="anthropic-ratelimit-tokens-reset",
        )

    @staticmethod
    def google(model_name: str, api_key: Optional[str] = None) -> "TextGenLLMConnection":
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
        assert api_key is not None, "Please set the GOOGLE_API_KEY or GEMINI_API_KEY environment variable."
        return TextGenLLMConnection(
            identifier=model_name,
            ip_address="generativelanguage.googleapis.com",
            port=443,
            use_https=True,
            has_seed=False,
            model=model_name,
            additional_headers={"Authorization": "Bearer %s" % api_key},
            cheap=False,
            path="v1beta/openai/chat/completions",
        )
