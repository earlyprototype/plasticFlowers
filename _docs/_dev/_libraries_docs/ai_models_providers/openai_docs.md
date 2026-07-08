# OpenAI API Documentation

## Overview
OpenAI provides state-of-the-art language models including GPT-4, GPT-4o, and GPT-4o-mini through a comprehensive REST API. The API supports text generation, image understanding, audio processing, embeddings, and more.

## Models

### GPT-4 Family
- **GPT-4**: Most capable model, best for complex reasoning tasks
- **GPT-4 Turbo**: Optimized performance with 128K context window
- **GPT-4o**: Multimodal flagship model with vision, audio, text capabilities
- **GPT-4o-mini**: Fast and affordable model for lightweight tasks

### Key Features
- **Context Windows**: Up to 128K tokens (GPT-4 Turbo), 16K-32K (GPT-4o mini)
- **Streaming**: Real-time response streaming
- **Function Calling**: Structured tool use
- **Structured Outputs**: JSON mode for reliable formatting

## Chat Completions API

### Basic Request

```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### API Endpoint

```
POST https://api.openai.com/v1/chat/completions
```

**Request Body:**
- `model` (string, required): Model identifier
- `messages` (array, required): Conversation history
- `temperature` (number, optional): Sampling temperature (0-2)
- `max_tokens` (integer, optional): Maximum response length
- `stream` (boolean, optional): Enable streaming
- `tools` (array, optional): Function definitions
- `tool_choice` (string/object, optional): Tool selection strategy

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1699564200,
  "model": "gpt-4o",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

## Function Calling

### Define Functions

```python
functions = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and state, e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"]
                }
            },
            "required": ["location"]
        }
    }
}]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What's the weather in London?"}],
    tools=functions,
    tool_choice="auto"  # or "required" to force tool use
)
```

### Tool Choice Options
- `"auto"`: Model decides whether to call functions (default)
- `"required"`: Model must call a function
- `{"type": "function", "function": {"name": "func_name"}}`: Force specific function

## Multimodal Capabilities

### Vision - Image Understanding

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/jpeg;base64,{base64_image}"
                }
            }
        ]
    }]
)
```

### Audio Input/Output

```python
response = client.chat.completions.create(
    model="gpt-4o-audio-preview",
    modalities=["text", "audio"],
    audio={
        "voice": "alloy",
        "format": "mp3"
    },
    messages=[{
        "role": "user",
        "content": [{
            "type": "input_audio",
            "input_audio": {
                "data": base64_audio,
                "format": "wav"
            }
        }]
    }]
)
```

## Embeddings

### Generate Embeddings

```
POST https://api.openai.com/v1/embeddings
```

```python
response = client.embeddings.create(
    model="text-embedding-ada-002",
    input="Your text to embed"
)

embedding = response.data[0].embedding
```

**Use Cases:**
- Semantic search
- Clustering
- Recommendations
- Classification

## Streaming Responses

```python
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

## Available Endpoints

### Core
- `POST /v1/chat/completions` - Chat completions
- `POST /v1/embeddings` - Generate embeddings
- `POST /v1/responses` - Structured responses (new)

### Assistants
- `POST /v1/assistants` - Create AI assistants
- `POST /v1/threads` - Manage conversation threads

### Media
- `POST /v1/images/generations` - Generate images (DALL-E)
- `POST /v1/audio/speech` - Text-to-speech
- `POST /v1/audio/transcriptions` - Speech-to-text (Whisper)

### Advanced
- `POST /v1/batch` - Batch processing
- `POST /v1/fine-tuning` - Fine-tune models
- `POST /v1/moderations` - Content moderation

## Pricing (Approximate)

### GPT-4o
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens

### GPT-4o-mini
- Input: $0.15 per 1M tokens  
- Output: $0.60 per 1M tokens

### Embeddings
- text-embedding-ada-002: $0.10 per 1M tokens

## Best Practices

### Temperature Control
- **0.0-0.3**: Factual, deterministic responses
- **0.4-0.7**: Balanced creativity
- **0.8-1.0**: High creativity, more random

### Token Management
```python
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-4o")
tokens = encoding.encode("Your text here")
print(f"Token count: {len(tokens)}")
```

### Error Handling

```python
from openai import OpenAI, OpenAIError

try:
    response = client.chat.completions.create(...)
except OpenAIError as e:
    print(f"Error: {e}")
```

## Rate Limits

- **Free tier**: Limited requests per minute
- **Paid tiers**: Higher limits based on usage tier
- **Batch API**: Lower cost for non-urgent workloads

## PlasticFlower Integration Use Cases

1. **Content Generation**: Generate descriptions for knowledge nodes
2. **Embeddings**: Semantic search within knowledge graphs
3. **Function Calling**: Tool integration for data retrieval
4. **Multi-turn Conversations**: Interactive knowledge exploration
5. **Classification**: Categorise and tag content automatically

## Resources

- **API Documentation**: https://platform.openai.com/docs/
- **API Reference**: https://platform.openai.com/docs/api-reference
- **Cookbook**: https://cookbook.openai.com/
- **Community Forum**: https://community.openai.com/

## Python Client Library

```bash
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    organization="org-id"  # Optional
)
```

## Key Capabilities for PlasticFlower

1. **GPT-4 for Complex Reasoning**: Analyse relationships, generate insights
2. **Embeddings for Semantic Search**: Find similar concepts in knowledge graph
3. **Function Calling**: Integrate with Neo4j queries, external APIs
4. **Streaming**: Real-time progressive responses for better UX
5. **Vision**: Analyse images within knowledge nodes
6. **Audio**: Voice-based knowledge exploration





