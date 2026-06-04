# Anthropic Claude API Documentation

## Overview
Claude is a family of highly capable, secure AI models by Anthropic, known for safety, helpfulness, and honesty. The API provides access to Claude models for text generation, vision, reasoning, and tool use.

## Models

### Claude 3.5 Sonnet
- **Context Window**: 200K tokens
- **Best For**: Most tasks, balance of intelligence and speed
- **Strengths**: Coding, analysis, creative writing

### Claude 3 Opus
- **Context Window**: 200K tokens
- **Best For**: Complex tasks requiring top-tier intelligence
- **Strengths**: Advanced reasoning, research, analysis

### Claude 3 Haiku
- **Context Window**: 200K tokens
- **Best For**: Fast, lightweight tasks
- **Strengths**: Speed, cost-effectiveness

## API Access

### Base URL
```
https://api.anthropic.com/v1/
```

### Authentication
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

## Basic Usage

### Python

```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Explain quantum computing"
    }]
)

print(message.content[0].text)
```

### JavaScript

```javascript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY
});

const message = await client.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 1024,
    messages: [{
        role: 'user',
        content: 'Explain quantum computing'
    }]
});

console.log(message.content[0].text);
```

## Messages API

### Endpoint
```
POST https://api.anthropic.com/v1/messages
```

### Request Structure

```python
{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "messages": [
        {
            "role": "user",
            "content": "Your message here"
        }
    ],
    "system": "Optional system prompt",
    "temperature": 1.0,
    "top_p": 1.0,
    "stream": false
}
```

## Vision Capabilities

### Image Understanding

```python
import base64

with open("image.jpg", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_data
                }
            },
            {
                "type": "text",
                "text": "Describe this image"
            }
        ]
    }]
)
```

## Tool Use (Function Calling)

### Define Tools

```python
tools = [{
    "name": "get_weather",
    "description": "Get the current weather in a given location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and state, e.g. San Francisco, CA"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit"
            }
        },
        "required": ["location"]
    }
}]

# Initial request
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[{
        "role": "user",
        "content": "What's the weather in London?"
    }]
)

# Handle tool use
if response.stop_reason == "tool_use":
    tool_use = next(block for block in response.content if block.type == "tool_use")
    
    # Execute function
    result = get_weather(**tool_use.input)
    
    # Continue conversation with result
    final_response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=tools,
        messages=[
            {"role": "user", "content": "What's the weather in London?"},
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": str(result)
                }]
            }
        ]
    )
```

## Streaming

```python
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Tell me a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## System Prompts

```python
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system="You are a helpful AI assistant specialising in knowledge graphs and Neo4j.",
    messages=[{
        "role": "user",
        "content": "How do I model relationships in Neo4j?"
    }]
)
```

## Prompt Caching (Beta)

Reduce costs for repetitive prompts:

```python
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "Large system prompt...",
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[...]
)
```

## Pricing (Approximate)

### Claude 3.5 Sonnet
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens
- Cached Input: $0.30 per 1M tokens (90% savings)

### Claude 3 Haiku
- Input: $0.25 per 1M tokens
- Output: $1.25 per 1M tokens

## Best Practices

### Prompt Engineering
- Be clear and specific
- Use XML tags for structure: `<documents>`, `<instructions>`
- Provide examples for complex tasks

### Safety and Alignment
- Claude trained with Constitutional AI for safety
- Strong at following instructions precisely
- Excellent refusal behavior for harmful requests

### Long Context
- 200K context window across all models
- Good at "needle in haystack" retrieval
- Use for document Q&A, analysis

## PlasticFlower Integration Use Cases

1. **Knowledge Extraction**: Analyse documents, extract entities and relationships
2. **Graph Query Generation**: Convert natural language to Cypher queries
3. **Content Summarisation**: Summarise large knowledge graph sections
4. **Tool Use**: Integrate with Neo4j driver for database operations
5. **Vision**: Analyse images within knowledge nodes
6. **Long Context**: Process entire research papers, documentation

## Resources

- **Documentation**: https://docs.anthropic.com/
- **Cookbook**: https://github.com/anthropics/anthropic-cookbook
- **API Reference**: https://docs.anthropic.com/en/api/
- **Console**: https://console.anthropic.com/

## Client Libraries

### Python
```bash
pip install anthropic
```

### JavaScript/TypeScript
```bash
npm install @anthropic-ai/sdk
```

## Rate Limits

- **Free tier**: Available via console (limited)
- **Paid tiers**: Based on usage tier
- **Batch processing**: Available for large-scale operations

## Key Advantages for PlasticFlower

1. **Safety**: Constitutional AI training for reliable, safe responses
2. **Long Context**: 200K tokens ideal for processing extensive documents
3. **Tool Use**: Sophisticated function calling for database integration
4. **Vision**: Native image understanding without separate API
5. **Prompt Caching**: Cost savings for repetitive system prompts
6. **Precise Following**: Excellent at adhering to complex instructions

## Notable Limitations

- No built-in embedding model (use third-party)
- No audio/video capabilities (text and images only)
- No web search integration (requires external tools)





