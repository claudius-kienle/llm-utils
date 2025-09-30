import re
from dataclasses import dataclass
from typing import Callable, Dict, List

from llm_utils.textgen_api.textgen_api_connection import TextGenLLMConnection


@dataclass
class TextGenLLMConnections:
    connections: List[TextGenLLMConnection]

    def cheap_connection_id(self) -> str:
        return next(filter(lambda c: c.cheap, self.connections), self.connections[0]).identifier

    def expensive_connection_id(self) -> str:
        return next(filter(lambda c: not c.cheap, self.connections), self.connections[0]).identifier

    def get_connection(self, identifier: str) -> TextGenLLMConnection:
        """get connection, fallback to first entry"""
        for connection in self.connections:
            if connection.identifier == identifier:
                return connection
        return self.get_connection(self.expensive_connection_id())

    @staticmethod
    def all_connections() -> Dict[str, Callable[[], TextGenLLMConnection]]:
        return {
            "gpt3.5": lambda: TextGenLLMConnection.openai("gpt-3.5-turbo-0125"),
            "gpt4.1-mini": lambda: TextGenLLMConnection.openai("gpt-4.1-mini-2025-04-14"),
            "gpt4.1": lambda: TextGenLLMConnection.openai("gpt-4.1-2025-04-14"),
            "gpt4o-mini": lambda: TextGenLLMConnection.openai("gpt-4o-mini-2024-07-18"),
            "gpt4o": lambda: TextGenLLMConnection.openai("gpt-4o-2024-08-06"),
            "claude3.5-haiku": lambda: TextGenLLMConnection.anthropic("claude-3-5-haiku-20241022"),
            "claude3.7-sonnet": lambda: TextGenLLMConnection.anthropic("claude-3-7-sonnet-20250219"),
            "claude4-sonnet": lambda: TextGenLLMConnection.anthropic("claude-4-sonnet-20250514"),
            "gemini2.5-flash": lambda: TextGenLLMConnection.google("gemini-2.5-flash"),
        }

    @staticmethod
    def default(connection: str) -> "TextGenLLMConnections":
        if "self-hosted" in connection:
            match = re.match(r"self-hosted:(.*):(\d+)", connection)
            assert match is not None
            ip_address, port = match.groups()
            conn = TextGenLLMConnection.self_hosted(ip_address=ip_address, port=int(port))
        elif ":" in connection:
            provider, model = connection.split(":", 1)
            if provider == "openai":
                conn = TextGenLLMConnection.openai(model_name=model)
            elif provider == "anthropic":
                conn = TextGenLLMConnection.anthropic(model_name=model)
            elif provider == "google":
                conn = TextGenLLMConnection.google(model_name=model)
            elif provider == "cerebras":
                conn = TextGenLLMConnection.cerebras(model_name=model)
            elif provider == "openrouter":
                conn = TextGenLLMConnection.openrouter(model_name=model)
            else:
                raise ValueError(f"Unknown provider: {provider}")
        else:
            conn = TextGenLLMConnections.all_connections()[connection]()

        return TextGenLLMConnections(connections=[conn])
