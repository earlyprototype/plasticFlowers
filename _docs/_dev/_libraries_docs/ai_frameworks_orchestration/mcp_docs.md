# Model Context Protocol (MCP) Documentation

## Overview
The Model Context Protocol (MCP) is an open standard for connecting AI applications and LLMs with external data sources and tools. It provides a unified way to expose context, prompts, resources, and tools to language models, making AI systems more composable and extensible.

## Core Concepts

### Protocol Components
- **Servers**: Expose resources, prompts, and tools to clients
- **Clients**: Connect to servers and use exposed capabilities
- **Resources**: Data sources (files, APIs, databases)
- **Prompts**: Template messages for LLM interactions
- **Tools**: Executable functions the LLM can invoke

### Architecture
MCP uses JSON-RPC 2.0 for communication between clients and servers, with support for multiple transport mechanisms (HTTP, WebSocket, stdio).

## Capabilities

### Resources

Resources represent data sources that can be read by LLMs.

**List Resources**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/list",
  "params": {
    "cursor": "optional-cursor-value"
  }
}
```

**Read Resource**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/read",
  "params": {
    "uri": "file:///project/src/main.rs"
  }
}
```

**Subscribe to Changes**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/subscribe",
  "params": {
    "uri": "file:///project/src/main.rs"
  }
}
```

### Prompts

Prompts are reusable templates for LLM interactions.

**List Prompts**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "prompts/list",
  "params": {
    "cursor": "optional-cursor-value"
  }
}
```

**Get Prompt**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "prompts/get",
  "params": {
    "name": "code_review",
    "arguments": {
      "code": "def hello():\n    print('world')"
    }
  }
}
```

### Tools

Tools are functions that LLMs can invoke to perform actions.

**List Tools**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {
    "cursor": "optional-cursor-value"
  }
}
```

**Call Tool**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {
      "location": "New York"
    }
  }
}
```

**Tool Response**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Current weather in New York:\nTemperature: 72°F\nConditions: Partly cloudy"
      }
    ],
    "isError": false
  }
}
```

## Server Implementation

### Declaring Capabilities

```json
{
  "capabilities": {
    "resources": {
      "subscribe": true,
      "listChanged": true
    },
    "prompts": {
      "listChanged": true
    },
    "tools": {
      "listChanged": true
    }
  }
}
```

### Resource Definition

```json
{
  "uri": "file:///project/README.md",
  "name": "README.md",
  "title": "Project Documentation",
  "mimeType": "text/markdown",
  "annotations": {
    "audience": ["user"],
    "priority": 0.8,
    "lastModified": "2025-01-12T15:00:58Z"
  }
}
```

### Tool Definition

```json
{
  "name": "get_weather",
  "title": "Weather Information Provider",
  "description": "Get current weather information for a location",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City name or zip code"
      }
    },
    "required": ["location"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "temperature": {"type": "number"},
      "conditions": {"type": "string"},
      "humidity": {"type": "number"}
    },
    "required": ["temperature", "conditions"]
  }
}
```

## Client Usage

### Sampling with Tools

Clients can request LLM sampling with tool availability:

**Request**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "sampling/createMessage",
  "params": {
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "What's the weather like in Paris?"
        }
      }
    ],
    "tools": [
      {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "inputSchema": {
          "type": "object",
          "properties": {
            "city": {"type": "string"}
          },
          "required": ["city"]
        }
      }
    ],
    "maxTokens": 1000
  }
}
```

**Response (Tool Use)**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "role": "assistant",
    "content": [
      {
        "type": "tool_use",
        "id": "call_abc123",
        "name": "get_weather",
        "input": {"city": "Paris"}
      }
    ],
    "model": "claude-3-sonnet-20240307",
    "stopReason": "toolUse"
  }
}
```

### Multi-Turn Tool Loops

**Follow-up Request with Tool Results**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "sampling/createMessage",
  "params": {
    "messages": [
      {
        "role": "user",
        "content": {"type": "text", "text": "What's the weather like in Paris?"}
      },
      {
        "role": "assistant",
        "content": [
          {
            "type": "tool_use",
            "id": "call_abc123",
            "name": "get_weather",
            "input": {"city": "Paris"}
          }
        ]
      },
      {
        "role": "user",
        "content": [
          {
            "type": "tool_result",
            "toolUseId": "call_abc123",
            "content": [
              {"type": "text", "text": "Weather in Paris: 18°C, partly cloudy"}
            ]
          }
        ]
      }
    ],
    "tools": [...],
    "maxTokens": 1000
  }
}
```

## Notifications

### Resource Updates
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "uri": "file:///project/src/main.rs"
  }
}
```

### List Changes
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/prompts/list_changed"
}
```

## Resource Templates

For parameterised resources:

```json
{
  "uriTemplate": "file:///{path}",
  "name": "Project Files",
  "title": "📁 Project Files",
  "description": "Access files in the project directory",
  "mimeType": "application/octet-stream"
}
```

## Transport Mechanisms

### HTTP/SSE
- Standard HTTP requests and responses
- Server-sent events for notifications
- Stateless or session-based

### WebSocket
- Bidirectional communication
- Real-time notifications
- Connection persistence

### Stdio
- Standard input/output streams
- Process-based communication
- Local execution

## Security Considerations

1. **User Approval**: Clients SHOULD implement approval controls for requests
2. **Message Validation**: Validate message content to prevent malicious data
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Sensitive Data**: Handle sensitive data securely
5. **Tool Result Matching**: Ensure each tool use has a corresponding result
6. **Iteration Limits**: Prevent infinite tool loops

## Best Practices

1. **Capability Declaration**: Clearly declare supported capabilities
2. **Error Handling**: Return standard JSON-RPC errors
3. **Pagination**: Support cursor-based pagination for large lists
4. **Subscriptions**: Notify clients of changes when supported
5. **Tool Schemas**: Provide detailed input/output schemas
6. **Annotations**: Use annotations for rich metadata
7. **Testing**: Test with multiple clients/servers for interoperability

## Python SDK Example

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("example-server")

@app.list_resources()
async def list_resources():
    return [
        {
            "uri": "file:///example.txt",
            "name": "Example File",
            "mimeType": "text/plain"
        }
    ]

@app.read_resource()
async def read_resource(uri: str):
    return {
        "uri": uri,
        "mimeType": "text/plain",
        "text": "Example content"
    }

@app.list_tools()
async def list_tools():
    return [
        {
            "name": "calculate",
            "description": "Perform calculation",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "calculate":
        result = eval(arguments["expression"])
        return {"content": [{"type": "text", "text": str(result)}]}

if __name__ == "__main__":
    stdio_server(app)
```

## TypeScript SDK Example

```typescript
import { Server } from "@modelcontextprotocol/sdk/server";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio";

const server = new Server({
  name: "example-server",
  version: "1.0.0"
});

server.setRequestHandler("resources/list", async () => {
  return {
    resources: [
      {
        uri: "file:///example.txt",
        name: "Example File",
        mimeType: "text/plain"
      }
    ]
  };
});

server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;
  if (name === "calculate") {
    const result = eval(args.expression);
    return {
      content: [{ type: "text", text: String(result) }]
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Resources

- **Specification**: https://modelcontextprotocol.io/specification
- **GitHub**: https://github.com/modelcontextprotocol
- **Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **TypeScript SDK**: https://github.com/modelcontextprotocol/typescript-sdk





