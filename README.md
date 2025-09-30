# LLM Utils

[![Version](https://img.shields.io/badge/version-0.0.5-blue.svg)](https://git.ias.informatik.tu-darmstadt.de/kienle1/llm-interface)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive Python package providing utilities for working with Large Language Models (LLMs). This package offers a universal interface to connect your applications to various LLM providers including OpenAI ChatGPT, Anthropic Claude, Google Gemini, and self-hosted models.

## Features

- 🚀 **Universal LLM Interface**: Connect to multiple LLM providers with a single, consistent API
- 🔧 **Communication Utilities**: Tools for CAD applications and data visualization
- 🎨 **Color Management**: Unique color generation and web color utilities
- 📝 **Prompt Management**: XML-based prompt templates with variable substitution
- 🖼️ **Multi-modal Support**: Handle text and image content in conversations
- ⚙️ **Flexible Configuration**: Environment-based configuration and provider switching

## Installation

### From Git Repository
```bash
pip install git+ssh://git@git.ias.informatik.tu-darmstadt.de:kienle1/llm-interface.git
```

### For Development
```bash
git clone git@git.ias.informatik.tu-darmstadt.de:kienle1/llm-interface.git
cd llm-interface
pip install -e .
```

## Quick Start

### Basic Usage

```python
from llm_utils import TextGenApi, Chat, UserMessage, TextMessageContent

# Initialize API with your preferred model
api = TextGenApi.default("gpt-4o-mini")  # Requires OPENAI_API_KEY

# Create a simple chat
chat = Chat(messages=[
    UserMessage(content=TextMessageContent(text="Hello! How are you?"))
])

# Get response
response = api.do_call(chat)
print(response.content[0].text)
```

### Using Prompt Templates

```python
from llm_utils import Prompt
from pathlib import Path

# Define XML prompt template
prompt_template = """
<data>
    <message role='system'>
        You are a helpful assistant specialized in {domain}.
    </message>
    <message role="user">
        What is the weather like in {city} on {date}?
    </message>
</data>
"""

# Create and configure prompt
prompt = Prompt(prompt_template)
prompt.replace_all(
    domain="meteorology",
    city="Berlin",
    date="tomorrow"
)

# Convert to chat and get response
chat = prompt.to_chat()
response = api.do_call(chat)
print(response.content[0].text)
```

## Configuration

### Environment Variables

Set up your API credentials using environment variables:

| Provider | Environment Variable | Example Model |
|----------|---------------------|---------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` |
| Cerebras | `CEREBRAS_API_KEY` | `llama3.1-70b` |
| OpenRouter | `OPENROUTER_API_KEY` | `openrouter:meta-llama/llama-3.1-8b` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-3-sonnet` |
| Google | `GOOGLE_API_KEY` | `gemini-pro` |

You can also set the default model via:
```bash
export LLM_MODEL="gpt-4o-mini"
```

### Supported Model Formats

```python
# OpenAI models
api = TextGenApi.default("gpt-4o-mini")
api = TextGenApi.default("gpt-4")

# Self-hosted models
api = TextGenApi.default("self-hosted:127.0.0.1:8080")

# Provider-specific models
api = TextGenApi.default("openrouter:meta-llama/llama-3.1-8b")
api = TextGenApi.default("anthropic:claude-3-sonnet")
```

## Advanced Usage

### Multi-modal Conversations

```python
from llm_utils import ImageMessageContent, MessageContentFactory

# Create message with both text and image
content = [
    TextMessageContent(text="What's in this image?"),
    ImageMessageContent(image_url="path/to/image.jpg")
]

message = UserMessage(content=content)
chat = Chat(messages=[message])
response = api.do_call(chat)
```

### Communication Utilities

```python
from llm_utils import UniqueColorSupplier, CADPart

# Generate unique colors for visualization
color_supplier = UniqueColorSupplier()
colors = [color_supplier.get_next_color() for _ in range(5)]

# Work with CAD components (requires additional setup)
cad_part = CADPart(name="housing", material="aluminum")
```

## API Reference

### Core Classes

- **`TextGenApi`**: Main interface for LLM communication
- **`Chat`**: Represents a conversation with messages
- **`Message`**: Base class for conversation messages
- **`UserMessage`**, **`AssistantMessage`**, **`SystemMessage`**: Specific message types
- **`Prompt`**: XML-based prompt template management

### Content Types

- **`TextMessageContent`**: Plain text content
- **`ImageMessageContent`**: Image content for multi-modal models
- **`MessageContentFactory`**: Factory for creating content objects

### Utilities

- **`UniqueColorSupplier`**: Generate distinct colors
- **`CADPart`**: CAD/manufacturing utilities
- **`ViewOrientation`**, **`Direction`**: 3D visualization helpers

## Examples

Check out the `test.py` file for more usage examples, or explore the test suite for comprehensive API usage patterns.

## Development

### Building the Package

```bash
python -m build
```

### Publishing to Registry

```bash
python -m twine upload --repository-url https://git.ias.informatik.tu-darmstadt.de/api/v4/projects/2282/packages/pypi dist/*
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Setup Pre-Commit (`pre-commit install`)
3. Create a feature branch (`git checkout -b feature/amazing-feature`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Support

For questions and support, please contact [Claudius Kienle](mailto:claudius.kienle@tu-darmstadt.de).
