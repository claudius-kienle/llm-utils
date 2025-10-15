import json
import logging
import os
import time
from datetime import datetime
from typing import Generator, Optional, Union

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

    Supports both streaming and non-streaming responses:
    - Non-streaming: Returns a complete Message object
    - Streaming: Returns a Generator that yields text chunks as they arrive

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
        stream: bool = False,
        call_id: Optional[str] = None,
    ) -> Union[Message, Generator[str, None, None]]:
        connection = self.connections.get_connection(connection_id)
        logger.debug("call llm with %s", connection)
        system_message = next(filter(lambda m: m.role == "system", chat.messages), None)
        if "claude" in connection.identifier:
            chat = chat.copy_with(messages=list(filter(lambda m: m.role != "system", chat.messages)))
        data = {
            "model": connection.model,
            "messages": chat.to_dict(cache=True),
            "temperature": self.temperature,
            "stream": stream,
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
            connection.uri,
            headers={**self.headers, **connection.additional_headers},
            json=data,
            verify=False,
            stream=stream,
        )

        if response.status_code == 200:
            if stream:
                return self._handle_streaming_response(response, connection, call_id)
            else:
                return self._handle_non_streaming_response(response, connection, call_id)

        elif response.status_code == 429 or response.status_code == 529:
            logger.warning(
                "Rate Limit triggered. Should not occur, since we pause before calling the request when we expect a rate limit!\n    %s"
                % str(response.json())
            )
            time.sleep(60)
            return self.do_call(chat=chat, connection_id=connection_id, temperature=temperature, stream=stream, call_id=call_id)
        else:
            logger.warning(response.text)
            logger.error(response.status_code)
            return self.do_call(chat=chat, connection_id=connection_id, temperature=temperature, stream=stream, call_id=call_id)

    def _handle_non_streaming_response(self, response, connection, call_id: Optional[str] = None) -> Message:
        """Handle non-streaming response from the API."""
        response_data = response.json()
        self.usage.add_call(response_usage=response_data["usage"], call_id=call_id)

        self._update_rate_limits(response, connection)
        
        logger.debug(response_data["usage"])
        if "claude" in connection.identifier:
            message = MessageFactory().from_dict(response_data)
        else:
            choices = response_data["choices"]
            assert len(choices) > 0
            message = MessageFactory().from_dict(choices[0]["message"])

        return message

    def _handle_streaming_response(self, response, connection, call_id: Optional[str] = None) -> Generator[str, None, None]:
        """Handle streaming response from the API."""
        self._update_rate_limits(response, connection)
        
        accumulated_content = ""
        usage_data = None
        
        try:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        
                        if data_str.strip() == '[DONE]':
                            break
                            
                        try:
                            data = json.loads(data_str)
                            
                            # Handle different streaming formats
                            if "claude" in connection.identifier:
                                # Claude streaming format
                                if data.get("type") == "content_block_delta":
                                    delta = data.get("delta", {})
                                    text = delta.get("text", "")
                                    if text:
                                        accumulated_content += text
                                        yield text
                                elif data.get("type") == "message_delta":
                                    usage_data = data.get("usage")
                            else:
                                # OpenAI-compatible streaming format
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        accumulated_content += content
                                        yield content
                                
                                # Check for usage information
                                if "usage" in data:
                                    usage_data = data["usage"]
                                    
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse streaming data: {data_str}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            raise
        
        # Add usage information if available
        if usage_data and call_id:
            self.usage.add_call(response_usage=usage_data, call_id=call_id)

    def _update_rate_limits(self, response, connection):
        """Update rate limit information from response headers."""
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

    def stream_call(
        self,
        chat: Chat,
        connection_id: Optional[str] = None,
        temperature: Optional[float] = None,
        call_id: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        Convenience method for streaming calls.
        Returns a generator that yields text chunks as they arrive from the LLM.
        
        Args:
            chat: The conversation to send to the LLM
            connection_id: Optional connection identifier
            temperature: Optional temperature override
            call_id: Optional call identifier for usage tracking
            
        Returns:
            Generator yielding text chunks as strings
        """
        result = self.do_call(chat=chat, connection_id=connection_id, temperature=temperature, stream=True, call_id=call_id)
        if isinstance(result, Generator):
            yield from result
        else:
            # Fallback if streaming is not supported - yield the complete message
            yield result.content[0].text if hasattr(result, 'content') and result.content else str(result)

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
