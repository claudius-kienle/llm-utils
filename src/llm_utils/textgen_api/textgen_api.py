import logging
import os
import time
from datetime import datetime
from typing import Optional

import requests
import tiktoken
import urllib3
from python_utils.string_utils import parse_timedelta

from llm_utils.openai_api.chat import Chat
from llm_utils.openai_api.message import Message
from llm_utils.openai_api.message_factory import MessageFactory
from llm_utils.textgen_api.textgen_api_connections import TextGenLLMConnections
from llm_utils.textgen_api.usage import Usage

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)


class TextGenApi:
    """
    Interface for convenient access to our textgen backend.
    Note that the robustness of the methods supplied by this class highly depend on the model running in the backend.

    Robustness can be improved by:
            1. reworking/adding to the prompt
            2. improve the pre-, post-processing, and parsing of the LLM output
            3. run a larger/better model in the backend
    """

    def __init__(self, connections: TextGenLLMConnections, temperature: float = 1.0, seed: Optional[int] = None):
        self.connections = connections
        self.headers = {"Content-Type": "application/json"}
        self.remaining_tokens = None
        self.temperature = temperature
        self.seed = seed
        self.usage = Usage()

    @staticmethod
    def default(connection: Optional[str] = None) -> "TextGenApi":
        if connection is None:
            connection = os.getenv("LLM_MODEL")
        return TextGenApi(connections=TextGenLLMConnections.default(connection=connection))

    def do_call(
        self,
        chat: Chat,
        connection_id: Optional[str] = None,
        temperature: Optional[float] = None,
        call_id: Optional[str] = None,
    ) -> Message:
        connection = self.connections.get_connection(connection_id)
        logger.debug("call llm with %s", connection)
        system_message = next(filter(lambda m: m.role == "system", chat.messages), None)
        if "claude" in connection.identifier:
            chat = chat.copy_with(messages=list(filter(lambda m: m.role != "system", chat.messages)))
        data = {
            "model": connection.model,
            "messages": chat.to_dict(cache=True),
            "temperature": self.temperature,
            "stream": False,
            "max_tokens": connection.max_tokens,
            **connection.additional_params,
        }
        if temperature is not None:
            data["temperature"] = temperature
        if connection.has_seed and self.seed is not None:
            data["seed"] = self.seed
        if "claude" in connection.identifier and system_message is not None:
            data["system"] = system_message.content[0].text

        tokens_for_request = self._num_tokens_consumed_from_request(
            request_json=data, token_encoding_name="cl100k_base"
        )

        if self.remaining_tokens is not None and self.remaining_tokens < tokens_for_request:
            seconds_to_sleep = (self.resets_tokens_at - datetime.now()).total_seconds()
            if seconds_to_sleep > 0:
                logger.info("Waiting until rate limits reset (%d seconds)" % seconds_to_sleep)
                time.sleep(seconds_to_sleep)

        response = requests.post(
            connection.uri, headers={**self.headers, **connection.additional_headers}, json=data, verify=False
        )

        if response.status_code == 200:
            self.usage.add_call(response_usage=response.json()["usage"], call_id=call_id)

            if (
                connection.ratelimit_remaining_tokens_key is not None
                and connection.ratelimit_remaining_tokens_key in response.headers
            ):
                self.remaining_tokens = int(response.headers[connection.ratelimit_remaining_tokens_key])
                if "claude" in connection.identifier:
                    self.resets_tokens_at = datetime.strptime(
                        response.headers[connection.ratelimit_reset_key], "%Y-%m-%dT%H:%M:%SZ"
                    )
                else:
                    self.resets_tokens_at = datetime.now() + parse_timedelta(
                        response.headers[connection.ratelimit_reset_key]
                    )
            logger.debug(response.json()["usage"])
            if "claude" in connection.identifier:
                message = MessageFactory().from_dict(response.json())
            else:
                choices = response.json()["choices"]
                assert len(choices) > 0
                message = MessageFactory().from_dict(choices[0]["message"])

            return message

        elif response.status_code == 429 or response.status_code == 529:
            logger.warning(
                "Rate Limit triggered. Should not occur, since we pause before calling the request when we expect a rate limit!\n    %s"
                % str(response.json())
            )
            time.sleep(60)
            return self.do_call(chat=chat, connection_id=connection_id, temperature=temperature, call_id=call_id)
        else:
            logger.warning(response.text)
            logger.error(response.status_code)
            return self.do_call(chat=chat, connection_id=connection_id, temperature=temperature, call_id=call_id)

    def _num_tokens_consumed_from_request(
        self,
        request_json: dict,
        token_encoding_name: str,
    ):
        """Count the number of tokens in the request. Only supports completion and embedding requests."""
        # if "v1beta/" in api_endpoint:
        #     api_endpoint = api_endpoint.split("v1beta/")[1]
        # else:
        #     api_endpoint = api_endpoint.split("v1/")[1]

        encoding = tiktoken.get_encoding(token_encoding_name)
        # if completions request, tokens = prompt + n * max_tokens
        max_tokens = request_json.get("max_tokens")
        if max_tokens is None:
            max_tokens = 15
        n = request_json.get("n", 1)
        completion_tokens = n * max_tokens

        # chat completions
        num_tokens = 0
        for message in request_json["messages"]:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            assert "role" in message
            assert "content" in message
            if isinstance(message["content"], str):
                num_tokens += len(encoding.encode(message["content"]))
            else:
                for message_content in message["content"]:
                    for key, value in message_content.items():
                        if key == "cache_control":
                            continue
                        value = "".join([v if isinstance(v, str) else v["text"] for v in value])
                        num_tokens += len(encoding.encode(value))
                        if key == "name":  # if there's a name, the role is omitted
                            num_tokens -= 1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens + completion_tokens
