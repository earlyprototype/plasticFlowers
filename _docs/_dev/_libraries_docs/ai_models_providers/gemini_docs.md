# Google Gemini API Documentation

## Overview
Google Gemini is a multimodal AI platform providing state-of-the-art language models with native support for text, image, audio, and video understanding. It offers both Google AI Studio (free tier) and Vertex AI (enterprise) deployment options.

## Models

### Gemini 2.5 Flash
- **Context Window**: Up to 1M tokens
- **Capabilities**: Multimodal (text, image, audio, video)
- **Best For**: Fast, cost-effective applications
- **Features**: Streaming, function calling, code execution

### Gemini Pro
- **Context Window**: Up to 2M tokens
- **Capabilities**: Advanced reasoning, long-context tasks
- **Best For**: Complex analysis, document processing

## API Access

### Base URLs
- **Google AI Studio**: `https://generativelanguage.googleapis.com/v1beta/`
- **OpenAI-Compatible**: `https://generativelanguage.googleapis.com/v1beta/openai/`

### Authentication
```python
export GEMINI_API_KEY="your-api-key"
```

## Basic Text Generation

### Python

```python
from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain quantum computing"
)

print(response.text)
```

### JavaScript

```javascript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});

const response = await ai.models.generateContent({
    model: "gemini-2.5-flash",
    contents: "Explain quantum computing"
});

console.log(response.text);
```

## Multimodal Capabilities

### Image Understanding

```python
from PIL import Image

image = Image.open("path/to/image.png")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[image, "Describe this image in detail"]
)
```

### Video Analysis

```python
import base64

with open("video.mp4", "rb") as f:
    video_data = base64.b64encode(f.read()).decode('utf-8')

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        {"type": "text", "text": "Summarise this video with timestamps"},
        {"type": "video", "data": video_data, "mime_type": "video/mp4"}
    ]
)
```

### Audio Transcription

```python
with open("audio.wav", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode('utf-8')

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        {"type": "text", "text": "What does this audio say?"},
        {"type": "audio", "data": audio_data, "mime_type": "audio/wav"}
    ]
)
```

## Function Calling

### Define Tools

```python
weather_tool = {
    "type": "function",
    "name": "get_weather",
    "description": "Gets the weather for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and state, e.g. San Francisco, CA"
            }
        },
        "required": ["location"]
    }
}

# Initial request
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What's the weather in Paris?",
    tools=[weather_tool]
)

# Handle function call
if response.function_calls:
    func_call = response.function_calls[0]
    result = get_weather(**func_call.arguments)
    
    # Send result back
    final_response = client.models.generate_content(
        model="gemini-2.5-flash",
        previous_interaction_id=response.id,
        contents=[{
            "type": "function_result",
            "name": func_call.name,
            "call_id": func_call.id,
            "result": result
        }]
    )
```

## OpenAI-Compatible API

### Chat Completions

```python
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=[{
        "role": "user",
        "content": "Explain neural networks"
    }]
)
```

### Vision with OpenAI Format

```python
response = client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
        ]
    }]
)
```

## Code Execution Tool

```python
response = client.interactions.create(
    model="gemini-2.5-flash",
    input="Calculate the 50th Fibonacci number",
    tools=[{"type": "code_execution"}]
)
```

## Embeddings

```
POST /v1beta/models/{model}:embedContent
```

```python
embed_response = client.models.embed_content(
    model="text-embedding-004",
    contents="Text to embed"
)

embedding = embed_response.embedding
```

## API Endpoints

- **Generate Content**: `POST /v1beta/models/{model}:generateContent`
- **Stream Generate**: `POST /v1beta/models/{model}:streamGenerateContent`
- **Embed Content**: `POST /v1beta/models/{model}:embedContent`
- **Batch Embed**: `POST /v1beta/models/{model}:batchEmbedContents`
- **Count Tokens**: `POST /v1beta/models/{model}:countTokens`

## Pricing (Google AI Studio - Free Tier)

### Gemini 2.5 Flash
- **Free Quota**: 15 requests/minute, 1M tokens/minute, 1,500 requests/day
- **Paid**: $0.075 per 1M input tokens, $0.30 per 1M output tokens

### Gemini Pro
- **Free Quota**: Lower limits
- **Paid**: Higher rates for advanced capabilities

## Best Practices

### Context Length Management
- Gemini excels at long-context tasks (up to 2M tokens)
- Use for document analysis, codebase understanding

### Multimodal Input
- Native support eliminates need for separate vision APIs
- Combine text, images, audio, video in single request

### Safety Settings

```python
from google.genai import types

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="...",
    safety_settings=[
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]
)
```

## PlasticFlower Integration Use Cases

1. **Multimodal Knowledge Nodes**: Handle text, images, audio, video in graph
2. **Long-Context Analysis**: Process entire documents, codebases
3. **Free Tier**: Generous quotas for development/prototyping
4. **Code Execution**: Built-in tool for computational tasks
5. **Function Calling**: Native tool use for Neo4j integration
6. **Embeddings**: Cost-effective semantic search

## Resources

- **Official Docs**: https://ai.google.dev/gemini-api/docs/
- **Cookbook**: https://github.com/google-gemini/cookbook
- **Google AI Studio**: https://aistudio.google.com/
- **Vertex AI**: https://cloud.google.com/vertex-ai

## Client Libraries

### Python
```bash
pip install google-genai
```

### JavaScript/TypeScript
```bash
npm install @google/genai
```

### Go
```bash
go get google.golang.org/genai
```

## Key Advantages for PlasticFlower

1. **Multimodal Native**: No separate APIs for different media types
2. **Long Context**: Excellent for analysing entire knowledge graph sections
3. **Free Tier**: Generous quotas for development
4. **OpenAI Compatible**: Easy migration path
5. **Code Execution**: Built-in computational capabilities
6. **Google Integration**: Potential for Google Workspace, Drive integration





