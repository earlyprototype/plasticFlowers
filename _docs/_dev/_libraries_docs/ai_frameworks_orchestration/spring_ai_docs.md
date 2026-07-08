# Spring AI Documentation

## Overview
Spring AI is an application framework for AI engineering that connects enterprise data and APIs with AI models. It provides portable support for major AI providers and vector databases, following Spring ecosystem principles for building production-ready AI applications in Java.

## Core Capabilities

### Chat Completions
- **Multi-Provider Support**: OpenAI, Azure OpenAI, Anthropic, Google Gemini, AWS Bedrock
- **Streaming Responses**: Real-time token streaming
- **Function Calling**: Structured tool use integration
- **Embeddings**: Text vectorisation for semantic search

### Key Features
- **Spring Boot Integration**: Auto-configuration and starters
- **Vector Store Support**: Pinecone, Milvus, Weaviate, Qdrant, PostgreSQL+pgvector
- **RAG Pipelines**: Built-in support for retrieval-augmented generation
- **Portability**: Switch providers without code changes

## Basic Usage

### Simple Chat Client

```java
@Bean
public CommandLineRunner runner(ChatClient.Builder builder) {
    return args -> {
        ChatClient chatClient = builder.build();
        String response = chatClient.prompt("Tell me a joke").call().content();
        System.out.println(response);
    };
}
```

### Configuration

```properties
spring.ai.openai.api-key=<YOUR OPENAI KEY>
spring.ai.openai.chat.model=gpt-4o
spring.ai.openai.chat.temperature=0.7
```

## Chat Client API

### Basic Prompt

```java
@Autowired
private ChatClient.Builder chatClientBuilder;

public String getResponse(String userInput) {
    ChatClient chatClient = chatClientBuilder.build();
    return chatClient.prompt(userInput).call().content();
}
```

### Streaming Response

```java
public Flux<String> streamResponse(String userInput) {
    ChatClient chatClient = chatClientBuilder.build();
    return chatClient.prompt(userInput).stream().content();
}
```

### System Messages

```java
ChatClient chatClient = chatClientBuilder
    .defaultSystem("You are a helpful financial advisor")
    .build();

String response = chatClient.prompt("Should I invest in stocks?")
    .call()
    .content();
```

## Function Calling

### Define Function

```java
public class WeatherService {
    @Bean
    @Description("Get current weather for a location")
    public Function<WeatherRequest, WeatherResponse> currentWeather() {
        return request -> {
            // Call weather API
            return new WeatherResponse(request.location(), 72.0, "Sunny");
        };
    }
}

record WeatherRequest(String location) {}
record WeatherResponse(String location, double temperature, String conditions) {}
```

### Use Function with Chat

```java
@Autowired
private Function<WeatherRequest, WeatherResponse> currentWeather;

public String getWeatherInfo(String userQuery) {
    ChatClient chatClient = chatClientBuilder
        .defaultFunctions("currentWeather")
        .build();
    
    return chatClient.prompt(userQuery).call().content();
}
```

## Embeddings

### Generate Embeddings

```java
@Autowired
private EmbeddingClient embeddingClient;

public List<Double> generateEmbedding(String text) {
    EmbeddingResponse response = embeddingClient.embedForResponse(
        List.of(text)
    );
    return response.getResults().get(0).getOutput();
}
```

## Vector Stores

### Pinecone Integration

```java
@Configuration
public class VectorStoreConfig {
    @Bean
    public VectorStore vectorStore(
        EmbeddingClient embeddingClient,
        PineconeConnectionDetails pineconeDetails
    ) {
        return new PineconeVectorStore(pineconeDetails, embeddingClient);
    }
}
```

### Store and Retrieve Documents

```java
@Autowired
private VectorStore vectorStore;

// Store documents
public void storeDocuments(List<Document> documents) {
    vectorStore.add(documents);
}

// Semantic search
public List<Document> searchSimilar(String query, int topK) {
    SearchRequest request = SearchRequest.query(query).withTopK(topK);
    return vectorStore.similaritySearch(request);
}
```

## RAG (Retrieval-Augmented Generation)

### Basic RAG Pipeline

```java
@Service
public class RagService {
    @Autowired
    private ChatClient.Builder chatClientBuilder;
    
    @Autowired
    private VectorStore vectorStore;
    
    public String answerWithContext(String question) {
        // Retrieve relevant documents
        List<Document> relevantDocs = vectorStore.similaritySearch(
            SearchRequest.query(question).withTopK(3)
        );
        
        // Build context
        String context = relevantDocs.stream()
            .map(Document::getContent)
            .collect(Collectors.joining("\n\n"));
        
        // Generate answer with context
        ChatClient chatClient = chatClientBuilder.build();
        String prompt = String.format(
            "Context:\n%s\n\nQuestion: %s\nAnswer based on the context:",
            context, question
        );
        
        return chatClient.prompt(prompt).call().content();
    }
}
```

## Multi-Provider Configuration

### OpenAI

```properties
spring.ai.openai.api-key=${OPENAI_API_KEY}
spring.ai.openai.chat.model=gpt-4o
spring.ai.openai.embedding.model=text-embedding-3-large
```

### Azure OpenAI

```properties
spring.ai.azure.openai.api-key=${AZURE_OPENAI_API_KEY}
spring.ai.azure.openai.endpoint=${AZURE_OPENAI_ENDPOINT}
spring.ai.azure.openai.chat.deployment-name=gpt-4o
```

### Anthropic Claude

```properties
spring.ai.anthropic.api-key=${ANTHROPIC_API_KEY}
spring.ai.anthropic.chat.model=claude-3-sonnet-20240229
```

### Google Gemini

```properties
spring.ai.google.api-key=${GOOGLE_API_KEY}
spring.ai.google.chat.model=gemini-pro
```

## Advanced Features

### Conversation Memory

```java
@Service
public class ConversationalService {
    private final Map<String, ChatHistory> sessions = new ConcurrentHashMap<>();
    
    public String chat(String sessionId, String userMessage) {
        ChatHistory history = sessions.computeIfAbsent(
            sessionId, 
            k -> new ChatHistory()
        );
        
        history.add(new UserMessage(userMessage));
        
        ChatClient chatClient = chatClientBuilder.build();
        String response = chatClient
            .prompt()
            .messages(history.getMessages())
            .call()
            .content();
        
        history.add(new AssistantMessage(response));
        return response;
    }
}
```

### Multi-Modal Support

```java
public String analyzeImage(String imageUrl, String question) {
    ChatClient chatClient = chatClientBuilder.build();
    
    return chatClient
        .prompt()
        .user(u -> u
            .text(question)
            .media(MimeTypeUtils.IMAGE_PNG, imageUrl)
        )
        .call()
        .content();
}
```

## Observability

### Logging

```properties
logging.level.org.springframework.ai=DEBUG
spring.ai.chat.client.observations.enabled=true
```

### Metrics

```java
@Configuration
public class ObservabilityConfig {
    @Bean
    public ChatClientObservationConvention customObservation() {
        return new CustomChatObservationConvention();
    }
}
```

## Best Practices

1. **API Keys**: Store in environment variables or secure vault
2. **Error Handling**: Implement retry logic for API failures
3. **Rate Limiting**: Use caching for repeated queries
4. **Streaming**: Use streaming for long responses to improve UX
5. **Function Calling**: Keep functions focused and well-documented
6. **Vector Stores**: Choose based on scale and latency requirements
7. **Embeddings**: Reuse embeddings when possible to reduce costs
8. **Testing**: Mock AI providers for unit tests

## Dependencies

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-openai-spring-boot-starter</artifactId>
</dependency>

<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-pinecone-spring-boot-starter</artifactId>
</dependency>
```

```gradle
implementation 'org.springframework.ai:spring-ai-openai-spring-boot-starter'
implementation 'org.springframework.ai:spring-ai-pinecone-spring-boot-starter'
```

## Resources

- **Documentation**: https://spring.io/projects/spring-ai
- **GitHub**: https://github.com/spring-projects/spring-ai
- **Community**: Spring AI Discord





