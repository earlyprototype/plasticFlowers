# Spring AI Documentation

## Overview
Spring AI provides a Spring-friendly API and abstractions for developing AI applications in Java/Kotlin. It standardizes interactions with AI models (Chat, Embedding, Image) and vector databases, following Spring ecosystem design principles.

## Key Concepts

### 1. Chat Client & Models
*   **ChatClient**: The fluent API for interacting with LLMs. Supports detailed prompt engineering (System, User, Messages).
*   **Models**: Supports OpenAI, Anthropic, Azure OpenAI, Bedrock, Ollama, etc.
*   **Streaming**: Supports reactive streams (Flux) for real-time responses.

### 2. Prompt Engineering
*   **PromptTemplate**: Supports parameterized prompts (e.g., `Tell me a {adjective} joke`).
*   **Roles**: SystemMessage, UserMessage, AssistantMessage.
*   **Techniques**: Supports Chain of Thought (CoT), Few-Shot, and Zero-Shot prompting patterns.

### 3. Vector Stores (RAG)
*   **VectorStore Interface**: Unified interface for storing and retrieving document embeddings.
*   **Implementations**: PGVector (PostgreSQL), Chroma, Neo4j, Milvus, Weaviate, etc.
*   **Document**: Core entity containing text and metadata.
*   **Similarity Search**: Retrieve documents based on vector similarity (`similaritySearch(query)`).
*   **Metadata Filtering**: SQL-like filter expressions (e.g., `country == 'BG' && year >= 2020`).

### 4. Advanced Features
*   **Function Calling / Tools**: Register Java functions as tools that LLMs can invoke.
*   **Multitenancy**: Strategies for caching tools or system prompts per tenant.
*   **Evaluation**: Frameworks for evaluating model responses.

## Usage Examples

### Basic Chat Client
```java
ChatClient chatClient = ...;

String response = chatClient.prompt()
    .user("Tell me a joke")
    .call()
    .content();
```

### Retrieval Augmented Generation (RAG)
```java
@Service
public class DocumentService {
    private final VectorStore vectorStore;

    public DocumentService(VectorStore vectorStore) {
        this.vectorStore = vectorStore;
    }

    public void addDocuments(List<String> texts) {
        List<Document> docs = texts.stream()
            .map(t -> new Document(t, Map.of("source", "user")))
            .toList();
        vectorStore.add(docs);
    }

    public List<Document> search(String query) {
        return vectorStore.similaritySearch(
            SearchRequest.builder().query(query).topK(3).build()
        );
    }
}
```

### Filter Expressions
```java
// Metadata filtering
vectorStore.similaritySearch(
    SearchRequest.builder()
        .query("renewable energy")
        .filterExpression("year > 2023 && category == 'report'")
        .build()
);
```

## Detailed Reference (Code Snippets)

### Prompt Template Example with Placeholders
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/concepts.adoc

```text
Tell me a {adjective} joke about {content}.
```

### Configure Multiple Spring Beans from a Single Instance Factory Class (XML, Java, Kotlin)
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-client-chat/src/test/resources/text_source.txt

```xml
<bean    id="serviceLocator"        class="examples.DefaultServiceLocator">
      <!--   inject   any   dependencies      required    by  this   locator    bean   -->
</bean>

<bean    id="clientService"
      factory-bean="serviceLocator"
      factory-method="createClientServiceInstance"/>

<bean    id="accountService"
      factory-bean="serviceLocator"
      factory-method="createAccountServiceInstance"/>
```

### Implement Step-back Prompting in Java
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chat/prompt-engineering-patterns.adoc

```java
    // First get high-level concepts
    String stepBack = chatClient
            .prompt("""
                    Based on popular first-person shooter action games, what are
                    5 fictional key settings that contribute to a challenging and
                    engaging level storyline in a first-person shooter video game?
                    """)
            .call()
            .content();

    // Then use those concepts in the main task
    String story = chatClient
            .prompt()
            .user(u -> u.text("""
                    Write a one paragraph storyline for a new level of a first-
                    person shooter video game that is challenging and engaging.

                    Context: {step-back}
                    """)
                    .param("step-back", stepBack))
            .call()
            .content();
```

### Tree of Thoughts Game Solving Strategy in Java
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chat/prompt-engineering-patterns.adoc

```java
// Step 1: Generate multiple initial moves
String initialMoves = chatClient
        .prompt("""
                You are playing a game of chess. The board is in the starting position.
                Generate 3 different possible opening moves. For each move:
                1. Describe the move in algebraic notation
                2. Explain the strategic thinking behind this move
                3. Rate the move's strength from 1-10
                """)
        .options(ChatOptions.builder()
                .temperature(0.7)
                .build())
        .call()
        .content();
```

### Separate Write and Read Operations with Spring Services
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/vectordbs.adoc

```java
// Write operations in a service that needs full access
@Service
class DocumentIndexer {
    private final VectorStore vectorStore;

    DocumentIndexer(VectorStore vectorStore) {
        this.vectorStore = vectorStore;
    }

    public void indexDocuments(List<Document> documents) {
        vectorStore.add(documents);
    }
}
```

### Understand Relational Operators for Filter Expressions in Spring AI
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/vectordbs.adoc

```text
EQUALS: '=='
MINUS : '-'
PLUS: '+'
GT: '>'
GE: '>='
LT: '<'
LE: '<='
NE: '!='
```

### Implement Self-Consistency in Java
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chat/prompt-engineering-patterns.adoc

```java
// Implementation of Section 2.6: Self-consistency
public void pt_self_consistency(ChatClient chatClient) {
    String email = """
            Hi,
            I have seen you use Wordpress for your website. A great open
            source content management system. I have used it in the past
            too. It comes with lots of great user plugins. And it's pretty
            easy to set up.
```

### Define Abstract CommandManager Class (Java & Kotlin)
Source: https://github.com/spring-projects/spring-ai/blob/main/models/spring-ai-openai/src/test/resources/text_source.txt

```Java
package fiona.apple;

// no more Spring imports!

public abstract class CommandManager {

    public Object process(Object commandState) {
        // grab a new instance of the appropriate Command interface
        Command command = createCommand();
        // set the state on the (hopefully brand new) Command instance
        command.setState(commandState);
        return command.execute();
    }

    // okay... but where is the implementation of this method?
    protected abstract Command createCommand();
}
```

### Email Classification with Self-Consistency Voting in Java
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chat/prompt-engineering-patterns.adoc

```java
record EmailClassification(Classification classification, String reasoning) {
    enum Classification {
        IMPORTANT, NOT_IMPORTANT
    }
}

int importantCount = 0;
int notImportantCount = 0;

// Run the model 5 times with the same input
for (int i = 0; i < 5; i++) {
    EmailClassification output = chatClient
            .prompt()
            .user(u -> u.text("""
                    Email: {email}
                    Classify the above email as IMPORTANT or NOT IMPORTANT. Let's
                    think step by step and explain why.
                    """)
                    .param("email", email))
            .options(ChatOptions.builder()
                    .temperature(1.0)  // Higher temperature for more variation
                    .build())
            .call()
            .entity(EmailClassification.class);
```

### Implement Document Retrieval Service with VectorStoreRetriever in Spring AI
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/vectordbs.adoc

```java
@Service
public class DocumentRetrievalService {

    private final VectorStoreRetriever retriever;

    public DocumentRetrievalService(VectorStoreRetriever retriever) {
        this.retriever = retriever;
    }

    public List<Document> findSimilarDocuments(String query) {
        return retriever.similaritySearch(query);
    }
}
```

### Document Versioning with Delete and Add - Java
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/vectordbs.adoc

```java
// Create initial document (v1) with version metadata
Document documentV1 = new Document(
    "AI and Machine Learning Best Practices",
    Map.of(
        "docId", "AIML-001",
        "version", "1.0",
        "lastUpdated", "2024-01-01"
    )
);

// Add v1 to the vector store
vectorStore.add(List.of(documentV1));
```

### Zero-Shot Prompting for Sentiment Classification in Spring AI
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chat/prompt-engineering-patterns.adoc

```java
public void pt_zero_shot(ChatClient chatClient) {
    enum Sentiment {
        POSITIVE, NEUTRAL, NEGATIVE
    }

    Sentiment reviewSentiment = chatClient.prompt("""
            Classify movie reviews as POSITIVE, NEUTRAL or NEGATIVE.
            Review: "Her" is a disturbing study revealing the direction
            humanity is headed if AI is allowed to keep evolving,
            unchecked. I wish there were more movies like this masterpiece.
            Sentiment:
            """)
            .options(ChatOptions.builder()
                    .model("claude-3-7-sonnet-latest")
                    .temperature(0.1)
                    .maxTokens(5)
                    .build())
            .call()
            .entity(Sentiment.class);

    System.out.println("Output: " + reviewSentiment);
}
```

### Configure PostgreSQL Vector Store for Semantic Search in Spring AI
Source: https://context7.com/spring-projects/spring-ai/llms.txt

```java
@Configuration
public class VectorStoreConfig {

    @Bean
    public VectorStore vectorStore(EmbeddingModel embeddingModel, JdbcTemplate jdbcTemplate) {
        // Configure PostgreSQL vector store
        return PgVectorStore.builder(jdbcTemplate, embeddingModel)
            .dimensions(1536) // OpenAI embedding dimensions
            .schemaName("public")
            .tableName("vector_store")
            .build();
    }
}
```

### Multi-Tenant SaaS with Bedrock Tools-Only Caching
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chat/bedrock-converse.adoc

```java
// Shared tool definitions (cached once, used across all tenants)
List<FunctionToolCallback> sharedTools = createLargeToolRegistry(); // ~2000 tokens

// Tenant-specific configuration
@Service
public class MultiTenantAIService {

    public String processRequest(String tenantId, String userQuery) {
        // Load tenant-specific system prompt (changes per tenant)
        String tenantPrompt = loadTenantSystemPrompt(tenantId);

        ChatResponse response = chatModel.call(
            new Prompt(
                List.of(
                    new SystemMessage(tenantPrompt), // Tenant-specific, not cached
                    new UserMessage(userQuery)
                ),
                BedrockChatOptions.builder()
                    .model("us.anthropic.claude-3-7-sonnet-20250219-v1:0")
                    .cacheOptions(BedrockCacheOptions.builder()
                        .strategy(BedrockCacheStrategy.TOOLS_ONLY)
                        .build())
                    .toolCallbacks(sharedTools) // Shared tools - cached
                    .maxTokens(500)
                    .build()
            )
        );

        return response.getResult().getOutput().getText();
    }
}
```

### VectorStore Interface - Full-Featured Vector Database Operations
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/vectordbs.adoc

```java
public interface VectorStore extends DocumentWriter, VectorStoreRetriever {

    default String getName() {
		return this.getClass().getSimpleName();
	}

    void add(List<Document> documents);

    void delete(List<String> idList);

    void delete(Filter.Expression filterExpression);
}
```

### Cache Legal Documents for Repeated Analysis (Spring AI Java)
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chat/bedrock-converse.adoc

```java
// Load a legal contract (PDF or text)
String legalContract = loadDocument("merger-agreement.pdf"); // ~3000 tokens

// System prompt with legal expertise
String legalSystemPrompt = "You are an expert legal analyst specializing in corporate law. " +
    "Analyze the following contract and provide precise answers about terms, obligations, and risks: " +
    legalContract;

// First analysis - creates cache
ChatResponse riskAnalysis = chatModel.call(
    new Prompt(
        List.of(
            new SystemMessage(legalSystemPrompt),
            new UserMessage("What are the key termination clauses and associated penalties?")
        ),
        BedrockChatOptions.builder()
            .model("us.anthropic.claude-3-7-sonnet-20250219-v1:0")
            .cacheOptions(BedrockCacheOptions.builder()
                .strategy(BedrockCacheStrategy.SYSTEM_ONLY)
                .build())
            .maxTokens(1000)
            .build()
    )
);
```

### Add and Search Documents in Vector Store with Spring AI
Source: https://context7.com/spring-projects/spring-ai/llms.txt

```java
@Service
public class DocumentService {
    private final VectorStore vectorStore;

    public DocumentService(VectorStore vectorStore) {
        this.vectorStore = vectorStore;
    }

    public void addDocuments(List<String> texts) {
        // Create documents with metadata
        List<Document> documents = texts.stream()
            .map(text -> Document.builder()
                .text(text)
                .metadata("source", "user_upload")
                .metadata("timestamp", System.currentTimeMillis())
                .build())
            .collect(Collectors.toList());

        // Add to vector store (automatically embedded)
        vectorStore.add(documents);
    }
}
```

### Build Customer Support with Knowledge Base and Anthropic SYSTEM_ONLY Caching (Java)
Source: https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chat/anthropic-chat.adoc

```java
String knowledgeBase = """
    PRODUCT DOCUMENTATION:
    - API endpoints and authentication methods
    - Common troubleshooting procedures
    - Billing and subscription details
    - Integration guides and examples
    - Known issues and workarounds
    """ + loadProductDocs(); // ~2500 tokens

@Service
public class CustomerSupportService {

    public String handleCustomerQuery(String customerQuery, String customerId) {
        ChatResponse response = chatModel.call(
            new Prompt(
                List.of(
                    new SystemMessage("You are a helpful customer support agent. " +
                        "Use this knowledge base to provide accurate solutions: " + knowledgeBase),
                    new UserMessage("Customer " + customerId + " asks: " + customerQuery)
                ),
                AnthropicChatOptions.builder()
                    .model("claude-sonnet-4")
                    .cacheOptions(AnthropicCacheOptions.builder()
                        .strategy(AnthropicCacheStrategy.SYSTEM_ONLY)
                        .build())
                    .maxTokens(600)
                    .build()
            )
        );

        return response.getResult().getOutput().getText();
    }
}
```


