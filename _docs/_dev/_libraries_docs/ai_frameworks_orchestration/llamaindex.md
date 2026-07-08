# LlamaIndex Documentation

## Overview
LlamaIndex is a data framework for building LLM applications, specializing in agentic workflows and Retrieval-Augmented Generation (RAG) to connect language models with private data. It provides tools for ingesting, indexing, and querying data.

## Key Components

### 1. Data Ingestion & Indexing
*   **SimpleDirectoryReader**: Loads data from local files.
*   **VectorStoreIndex**: Creates a vector index from documents for semantic search.
*   **SummaryIndex**: Creates a summary index for document summarization.
*   **KnowledgeGraphIndex**: Builds a knowledge graph from documents.
*   **SentenceSplitter**: Chunks text for indexing.

### 2. Query Engines & Retrievers
*   **QueryEngine**: The main interface for asking questions (e.g., `vector_index.as_query_engine()`).
*   **RetrieverQueryEngine**: A custom engine combining a retriever (like `FusionRetriever`) with response synthesis.
*   **RouterQueryEngine**: dynamically routes queries to different engines (e.g., summary vs. vector search) using an LLM.
*   **SubQuestionQueryEngine**: Decomposes complex queries into simpler sub-questions.

### 3. Agents & Tools
*   **FunctionAgent**: An agent that can use a set of tools (functions) to solve problems.
*   **OnDemandLoaderTool**: Wraps a data loader (like `WikipediaReader`) as a tool for agents.
*   **ToolSpec**: Defines tools for external services (e.g., `MetaphorToolSpec`, `TavilyToolSpec`, `YahooFinanceToolSpec`).

### 4. Storage & Integrations
*   **Vector Stores**: Integrates with Pinecone, Chroma, Weaviate, Milvus, and others.
*   **Graph Stores**: Supports Neo4j for knowledge graph storage (`Neo4jGraphStore`).
*   **LLMs**: Supports OpenAI, Anthropic, Gemini, Ollama (local), and more.

## Usage Examples

### Basic RAG Pipeline
```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# Load documents
documents = SimpleDirectoryReader("data").load_data()

# Build index
index = VectorStoreIndex.from_documents(documents)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("What did the author do?")
print(response)
```

### Knowledge Graph with Neo4j
```python
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core import KnowledgeGraphIndex, StorageContext

graph_store = Neo4jGraphStore(
    username="neo4j",
    password="password",
    url="bolt://localhost:7687",
    database="neo4j",
)

storage_context = StorageContext.from_defaults(graph_store=graph_store)
neo4j_index = KnowledgeGraphIndex.from_documents(
    documents,
    storage_context=storage_context,
)
```

### Agent with Tools
```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

agent = FunctionAgent(
    tools=my_tool_list,
    llm=OpenAI(model="gpt-4"),
)
response = agent.run("Perform a complex task")
```

## Detailed Reference (Code Snippets)

### Initialize Metaphor Load and Search Tool in LlamaIndex (Python)
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/tools/llama-index-tools-metaphor/examples/metaphor.ipynb

```python
wrapped_retrieve = LoadAndSearchToolSpec.from_defaults(
    metaphor_tool_list[2],
)
```

### Initialize OnDemandLoaderTool with Wikipedia Reader
Source: https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/module_guides/deploying/agents/tools.md

```python
from llama_index.readers.wikipedia import WikipediaReader
from llama_index.core.tools.ondemand_loader_tool import OnDemandLoaderTool

tool = OnDemandLoaderTool.from_defaults(
    reader,
    name="Wikipedia Tool",
    description="A tool for loading data and querying articles from Wikipedia",
)
```

### Initialize WikipediaReader
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/tools/OnDemandLoaderTool.ipynb

```python
reader = WikipediaReader()
```

### Initialize Basic Router Prompt Template in LlamaIndex
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/low_level/router.ipynb

```python
router_prompt0 = PromptTemplate(
    "Some choices are given below. It is provided in a numbered list (1 to"
    " {num_choices}), where each item in the list corresponds to a"
    " summary.\n---------------------\n{context_list}\n---------------------\nUsing"
    " only the choices above and not prior knowledge, return the top choices"
    " (no more than {max_outputs}, but only select what is needed) that are"
    " most relevant to the question: '{query_str}'\n"
)
```

### Initialize Query Engines from Indexes (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/low_level/router.ipynb

```python
vector_query_engine = vector_index.as_query_engine(llm=llm)
summary_query_engine = summary_index.as_query_engine(llm=llm)
```

### Initialize Pinecone Client
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/low_level/ingestion.ipynb

```python
api_key = os.environ["PINECONE_API_KEY"]
pc = Pinecone(api_key=api_key)
```

### Create GoogleIndex Corpus and Ingest Documents (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/managed/GoogleDemo.ipynb

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.indices.managed.google import GoogleIndex
from llama_index.core import Response
import time

# Create a corpus.
index = GoogleIndex.create_corpus(
    corpus_id=SESSION_CORPUS_ID, display_name="My first corpus!"
)
print(f"Newly created corpus ID is {index.corpus_id}.")

# Ingestion.
documents = SimpleDirectoryReader("./data/paul_graham/").load_data()
index.insert_documents(documents)
```

### Create Vector and Summary Indexes from Documents (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/low_level/router.ipynb

```python
from llama_index.core import VectorStoreIndex
from llama_index.core import SummaryIndex
from llama_index.core.node_parser import SentenceSplitter

splitter = SentenceSplitter(chunk_size=1024)
vector_index = VectorStoreIndex.from_documents(
    documents, transformations=[splitter]
)
summary_index = SummaryIndex.from_documents(
    documents, transformations=[splitter]
)
```

### Initialize LlamaIndex Agent with Metaphor Tools
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/tools/llama-index-tools-metaphor/examples/metaphor.ipynb

```python
# We don't give the Agent our unwrapped retrieve document tools, instead passing the wrapped tools
agent = FunctionAgent(
    tools=metaphor_tool_list,
    llm=OpenAI(model="gpt-4.1"),
)

# Context to store chat history
ctx = Context(agent)
```

### Perform Basic Document Loading and Querying in LlamaIndex
Source: https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/getting_started/faq.mdx

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("What did the author do growing up?")
print(response)
```

### Initialize OllamaQueryEnginePack with Model and Documents
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/llama_hub/llama_pack_ollama.ipynb

```python
# You can use any llama-hub loader to get documents!
ollama_pack = OllamaQueryEnginePack(model="llama2", documents=documents)
```

### Initialize Sentence Window Retriever Pack (Python)
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-packs/llama-index-packs-sentence-window-retriever/examples/sentence_window.ipynb

```python
sentence_window_retriever_pack = SentenceWindowRetrieverPack(
    documents,
)
```

### Import LangChain Agent Components
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/tools/OnDemandLoaderTool.ipynb

```python
from langchain.agents import initialize_agent
from langchain.chat_models import ChatOpenAI
```

### Initialize LlamaIndex RouterQueryEngine (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/low_level/router.ipynb

```python
choices = [
    (
        "Useful for answering questions about specific sections of the Llama 2"
        " paper"
    ),
    "Useful for questions that ask for a summary of the whole paper",
]

router_query_engine = RouterQueryEngine(
    query_engines=[vector_query_engine, summary_query_engine],
    choice_descriptions=choices,
    verbose=True,
    router_prompt=router_prompt1,
    llm=OpenAI(model="gpt-4"),
)
```

### Load and Read Documents with Metaphor Retrieval Tool (Python)
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/tools/llama-index-tools-metaphor/examples/metaphor.ipynb

```python
wrapped_retrieve.load("This is the best explanation for machine learning transformers:")
print(wrapped_retrieve.read("what is a transformer"))
print(wrapped_retrieve.read("who wrote the first paper on transformers"))
```

### Initialize Exa Tool and List Available Functions (Python)
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/tools/llama-index-tools-exa/examples/exa.ipynb

```python
import os

# Set up OpenAI
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

# NOTE:
# You must have an OpenAI API key in the environment variable OPENAI_API_KEY
# You must have an Exa API key in the environment variable EXA_API_KEY

# Set up the Exa search tool
# from llama_index.tools.exa import ExaToolSpec

# Instantiate
exa_tool = ExaToolSpec(
    api_key=os.environ["EXA_API_KEY"],
    # max_characters=2000   # this is the default
)

# Get the list of tools to see what Exa offers
exa_tool_list = exa_tool.to_tool_list()
for tool in exa_tool_list:
    print(tool.metadata.name)
```

### Initialize SearChainPack Instance in Python
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-packs/llama-index-packs-searchain/examples/searchain.ipynb

```python
searchain = SearChainPack(
    data_path="data",
    dprtokenizer_path="./model/dpr_reader_multi",
    dprmodel_path="./model/dpr_reader_multi",
    crossencoder_name_or_path="./model/Quora_cross_encoder",
)
```

### Initialize LlamaIndex Embedding Finetune Engine (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/finetuning/embeddings/finetune_embedding_adapter.ipynb

```python
base_embed_model = resolve_embed_model("local:BAAI/bge-small-en")

finetune_engine = EmbeddingAdapterFinetuneEngine(
    train_dataset,
    base_embed_model,
    model_output_path="model_output_test",
    # bias=True,
    epochs=4,
    verbose=True,
    # optimizer_class=torch.optim.SGD,
    # optimizer_params={"lr": 0.01}
)
```

### Install LlamaIndex Ollama and HuggingFace Integrations (Bash)
Source: https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/getting_started/starter_example_local.mdx

```bash
pip install llama-index-llms-ollama llama-index-embeddings-huggingface
```

### Initialize Vector Store and Add Nodes (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/low_level/vector_store.ipynb

```python
vector_store = VectorStore3B()
# load data into the vector stores
vector_store.add(nodes)
```

### Initialize WordLift Vector Store and LlamaIndex Query Engine in Python
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/vector_stores/WordLiftDemo.ipynb

```python
# Let's configure WordliftVectorStore using our WL Key
vector_store = WordliftVectorStore(key=API_KEY)

# Create an index from the vector store
index = VectorStoreIndex.from_vector_store(
    vector_store, embed_model=embed_model
)

# Create a query engine
query_engine = index.as_query_engine()
```

### Integrate YouRetriever into LlamaIndex Query Engine
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/retrievers/you_retriever.ipynb

```python
from llama_index.core.query_engine import RetrieverQueryEngine

retriever = YouRetriever()
query_engine = RetrieverQueryEngine.from_args(retriever)
```

```python
response = query_engine.query("Tell me about national parks in the US")
print(str(response))
```

### Initialize Desearch ToolSpec and Discover Tools (Python)
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/tools/llama-index-tools-desearch/examples/desearch.ipynb

```python
from llama_index_desearch.tools import DesearchToolSpec
import os

# Instantiate
desearch_tool = DesearchToolSpec(
    api_key=os.environ["DESEARCH_API_KEY"],
)

# Get the list of tools to see what Desearch offers
exa_tool_list = desearch_tool.to_tool_list()
for tool in exa_tool_list:
    print(tool.metadata.name)
```

### Initialize LlamaIndex Evaluation Metrics
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/retrievers/ensemble_retrieval.ipynb

```python
from llama_index.core.evaluation import (
    CorrectnessEvaluator,
    SemanticSimilarityEvaluator,
    RelevancyEvaluator,
    FaithfulnessEvaluator,
    PairwiseComparisonEvaluator,
)

# NOTE: can uncomment other evaluators
evaluator_c = CorrectnessEvaluator(llm=eval_llm)
evaluator_s = SemanticSimilarityEvaluator(llm=eval_llm)
evaluator_r = RelevancyEvaluator(llm=eval_llm)
evaluator_f = FaithfulnessEvaluator(llm=eval_llm)

pairwise_evaluator = PairwiseComparisonEvaluator(llm=eval_llm)
```

### Load data from Mangopps Guides using Python
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/readers/llama-index-readers-mangoapps-guides/README.md

```python
from llama_index.readers.mangoapps_guides import MangoppsGuidesReader

loader = MangoppsGuidesReader()
documents = loader.load_data(
    domain_url="https://guides.mangoapps.com", limit=1
)
```

### Initialize Nebius LLM Client
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/llm/nebius.ipynb

```python
from llama_index.llms.nebius import NebiusLLM

llm = NebiusLLM(
    api_key=NEBIUS_API_KEY, model="meta-llama/Llama-3.3-70B-Instruct-fast"
)
```

### Initialize VectorStoreIndex from Documents (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/module_guides/indexing/vector_store_index.mdx

```python
documents = SimpleDirectoryReader(
    "../../examples/data/paul_graham"
).load_data()
index = VectorStoreIndex.from_documents(
    documents, storage_context=storage_context
)
```

### Initialize Query Rewriting Retriever Pack
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-packs/llama-index-packs-fusion-retriever/examples/query_rewrite/query_rewrite.ipynb

```python
query_rewriting_pack = QueryRewritingRetrieverPack(
    nodes,
    chunk_size=256,
    vector_similarity_top_k=2,
)
```

### Initialize LlamaIndex Guidance Pydantic Program
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/output_parsing/guidance_pydantic_program.ipynb

```python
program = GuidancePydanticProgram(
    output_cls=Album,
    prompt_template_str=(
        "Generate an example album, with an artist and a list of songs. Using"
        " the movie {{movie_name}} as inspiration"
    ),
    guidance_llm=OpenAI("text-davinci-003"),
    verbose=True,
)
```

### Load documents and build VectorStoreIndex in LlamaIndex
Source: https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/module_guides/indexing/vector_store_index.mdx

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# Load documents and build index
documents = SimpleDirectoryReader(
    "../../examples/data/paul_graham"
).load_data()
index = VectorStoreIndex.from_documents(documents)
```

### Import LlamaIndex Ollama and HuggingFace Modules (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/getting_started/starter_example_local.mdx

```python
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
```

### Initialize GuidancePydanticProgram for Album Generation
Source: https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/community/integrations/guidance.md

```python
program = GuidancePydanticProgram(
    output_cls=Album,
    prompt_template_str="Generate an example album, with an artist and a list of songs. Using the movie {{movie_name}} as inspiration",
    guidance_llm=OpenAI("text-davinci-003"),
    verbose=True,
)
```

### Initialize Neo4jGraphStore and KnowledgeGraphIndex with LlamaIndex
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/cookbooks/llama3_cookbook_gaudi.ipynb

```python
import neo4j
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core import PropertyGraphIndex
from llama_index.core import (
    KnowledgeGraphIndex,
    StorageContext,
)

graph_store = Neo4jGraphStore(
    username="<user_name for NEO4J server>",
    password="<password for NEO4J server>",
    url="<URL for NEO4J server>",
    database="neo4j",
)

storage_context = StorageContext.from_defaults(graph_store=graph_store)
neo4j_index = KnowledgeGraphIndex.from_documents(
    documents=documents,
    max_triplets_per_chunk=3,
    storage_context=storage_context,
    embed_model=embed_model,
    include_embeddings=True,
)
```

### Initialize Gemini LLM and Prepare Image Input
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/multi_modal/gemini.ipynb

```python
from llama_index.llms.gemini import Gemini
from llama_index.core.llms import ChatMessage, ImageBlock


image_urls = [
    "https://storage.googleapis.com/generativeai-downloads/data/scene.jpg",
    # Add yours here!
]
gemini_pro = Gemini(model_name="models/gemini-1.5-flash")
msg = ChatMessage("Identify the city where this photo was taken.")
for img_url in image_urls:
    msg.blocks.append(ImageBlock(url=img_url))
```

### Load LlamaIndex from an Existing Vector Store
Source: https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/getting_started/starter_example_local.mdx

```python
index = VectorStoreIndex.from_vector_store(
    vector_store,
    # it's important to use the same embed_model as the one used to build the index
    # embed_model=Settings.embed_model,
)
```

### Initialize RaptorRetriever from Persistent Vector Store in Python
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-packs/llama-index-packs-raptor/examples/raptor.ipynb

```python
from llama_index.packs.raptor import RaptorRetriever

retriever = RaptorRetriever(
    [],
    embed_model=OpenAIEmbedding(
        model="text-embedding-3-small"
    ),  # used for embedding clusters
    llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1),  # used for generating summaries
    vector_store=vector_store,  # used for storage
    similarity_top_k=2,  # top k for each layer, or overall top-k for collapsed
    mode="tree_traversal",  # sets default mode
)
```

### Importing and Instantiating LlamaIndex Semantic Chunking Pack
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-packs/llama-index-packs-node-parser-semantic-chunking/examples/semantic_chunking.ipynb

```python
# option 1: if importing llama-hub as a package
from llama_index.packs.node_parser_semantic_chunking import (
    SemanticChunkingQueryEnginePack,
)

# # option 2: if downloading from llama_hub
from llama_index.core.llama_pack import download_llama_pack

# download_llama_pack(
#     "SemanticChunkingQueryEnginePack",
#     "./semantic_chunking_pack",
#     skip_load=True,
#     # leave the below line commented out if using the notebook on main
#     llama_hub_url="https://raw.githubusercontent.com/run-llama/llama-hub/jerry/add_semantic_chunking/llama_hub"
# )
# from semantic_chunking.base import SemanticChunkingQueryEnginePack
```

```python
pack = SemanticChunkingQueryEnginePack(documents)
```

### Initialize Tavily ToolSpec and List Available Tools (Python)
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/tools/llama-index-tools-tavily-research/examples/tavily.ipynb

```python
from llama_index.tools.tavily_research.base import TavilyToolSpec

tavily_tool = TavilyToolSpec(
    api_key="tvly-api-key",
)

tavily_tool_list = tavily_tool.to_tool_list()
for tool in tavily_tool_list:
    print(tool.metadata.name)
```

### Initialize OpenAI Finetune Engine for Knowledge Distillation (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/finetuning/llm_judge/pairwise/finetune_llm_judge.ipynb

```python
from llama_index.finetuning import OpenAIFinetuneEngine

finetune_engine = OpenAIFinetuneEngine(
    "gpt-3.5-turbo",
    "resolved_pairwise_finetuning_events.jsonl",
)
```

### Initialize LlamaIndex Function Agent with Dappier Tools in Python
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/tools/llama-index-tools-dappier/examples/dappier_real_time_search.ipynb

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

agent = FunctionAgent(
    tools=dappier_tool_list,
    llm=OpenAI(model="gpt-4o"),
)
```

### Initialize OpenAI LLM and Query General Information with LlamaIndex
Source: https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/presentations/materials/2024-04-02-otpp.ipynb

```python
from llama_index.llms.openai import OpenAI

llm = OpenAI(model="gpt-4-turbo-preview")
response = llm.complete("What is Ontario Teacher's Pension Plan all about?")
```

### Set Up Weaviate Sub-Question Pack with Python
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-packs/llama-index-packs-sub-question-weaviate/README.md

```python
from llama_index.core.vector_stores import MetadataInfo, VectorStoreInfo

vector_store_info = VectorStoreInfo(
    content_info="brief biography of celebrities",
    metadata_info=[
        MetadataInfo(
            name="category",
            type="str",
            description=(
                "Category of the celebrity, one of [Sports Entertainment, Business, Music]"
            ),
        ),
    ],
)

import weaviate

client = weaviate.Client()

nodes = [...]

# create the pack
weaviate_pack = WeaviateSubQuestion(
    collection_name="test",
    vector_store_info=vector_store_index,
    nodes=nodes,
    client=client,
)
```

### Initialize DatabaseReader and Load Data in Python
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/readers/llama-index-readers-database/README.md

```python
from llama_index.readers.database import DatabaseReader

# Initialize DatabaseReader with the SQL database connection details
reader = DatabaseReader(
    sql_database="<SQLDatabase Object>",  # Optional: SQLDatabase object
    engine="<SQLAlchemy Engine Object>",  # Optional: SQLAlchemy Engine object
    uri="<Connection URI>",  # Optional: Connection URI
    scheme="<Scheme>",  # Optional: Scheme
    host="<Host>",  # Optional: Host
    port="<Port>",  # Optional: Port
    user="<Username>",  # Optional: Username
    password="<Password>",  # Optional: Password
    dbname="<Database Name>",  # Optional: Database Name
)

# Load data from the database using a query
documents = reader.load_data(
    query="<SQL Query>"  # SQL query parameter to filter tables and rows
)
```

### Initialize Yahoo Finance Tools and List Available Functions
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/tools/llama-index-tools-yahoo-finance/examples/yahoo_finance.ipynb

```python
from llama_index.tools.yahoo_finance.base import YahooFinanceToolSpec

finance_tool = YahooFinanceToolSpec()

finance_tool_list = finance_tool.to_tool_list()
for tool in finance_tool_list:
    print(tool.metadata.name)
```

### Initialize Faiss Index for LlamaIndex Integration
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/data_connectors/FaissDemo.ipynb

```python
import faiss

id_to_text_map = {
    "id1": "text blob 1",
    "id2": "text blob 2"
}
index = ...
```

### Initialize Custom Adapter and Finetuning Engine (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/finetuning/embeddings/finetune_embedding_adapter.ipynb

```python
custom_adapter = CustomNN(
    384,  # input dimension
    1024,  # hidden dimension
    384,  # output dimension
    bias=True,
    add_residual=True,
)

finetune_engine = EmbeddingAdapterFinetuneEngine(
    train_dataset,
    base_embed_model,
    model_output_path="custom_model_output",
    model_checkpoint_path="custom_model_ck",
    adapter_model=custom_adapter,
    epochs=25,
    verbose=True,
)
```

### Initialize Local Gel Project
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/vector_stores/gel.ipynb

```python
! gel project init --non-interactive
```

### Initialize LlamaIndex Ollama Embedding Client
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/embeddings/ollama_embedding.ipynb

```python
from llama_index.embeddings.ollama import OllamaEmbedding

ollama_embedding = OllamaEmbedding(
    model_name="embeddinggemma",
    base_url="http://localhost:11434",
    # Can optionally pass additional kwargs to ollama
    # ollama_additional_kwargs={"mirostat": 0},
)
```

### Complete Example: Initialize and Load Data with ZyteWebReader in Python
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/readers/llama-index-readers-web/llama_index/readers/web/zyte_web/README.md

```python
# Initialize the ZyteWebReader with your API key and desired mode
zyte_reader = ZyteWebReader(
    api_key="your_api_key_here",  # Replace with your actual API key
    mode="article",  # Choose between "article", "html-text", and "html"
    download_kwargs={
        "additional": "parameters"
    },  # Optional additional parameters
)

# Load documents from Paul Graham's essay URL
documents = zyte_reader.load_data(urls=["http://www.paulgraham.com/"])

# Display the document
print(documents)
```

### Initialize FusionRetriever and RetrieverQueryEngine (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/low_level/fusion_retriever.ipynb

```python
from llama_index.core.query_engine import RetrieverQueryEngine

fusion_retriever = FusionRetriever(
    llm, [vector_retriever, bm25_retriever], similarity_top_k=2
)

query_engine = RetrieverQueryEngine(fusion_retriever)
```

### Initialize LlamaIndex DatasetGenerator for question creation
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/finetuning/llm_judge/correctness/finetune_llm_judge_single_grading_correctness.ipynb

```python
# generate questions against chunks
from llama_index.core.evaluation import DatasetGenerator
from llama_index.llms.openai import OpenAI

# set context for llm provider
gpt_35_llm = OpenAI(model="gpt-3.5-turbo", temperature=0.3)

# instantiate a DatasetGenerator
dataset_generator = DatasetGenerator.from_documents(
    documents,
    question_gen_query=QUESTION_GEN_PROMPT,
    llm=gpt_35_llm,
    num_questions_per_chunk=25,
)
```

### Initialize and Query Metaphor Tool with LlamaIndex Agent (Python)
Source: https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/tools/llama-index-tools-metaphor/README.md

```python
from llama_index.tools.metaphor import MetaphorToolSpec
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

metaphor_tool = MetaphorToolSpec(
    api_key="your-key",
)
agent = FunctionAgent(
    tools=metaphor_tool.to_tool_list(),
    llm=OpenAI(model="gpt-4.1"),
)

print(
    await agent.run(
        "Can you summarize the news published in the last month on superconductors"
    )
)
```

### Initialize SubQuestionQueryEngine with Tools
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/usecases/10k_sub_question.ipynb

```python
query_engine_tools = [
    QueryEngineTool(
        query_engine=lyft_engine,
        metadata=ToolMetadata(
            name="lyft_10k",
            description=(
                "Provides information about Lyft financials for year 2021"
            ),
        ),
    ),
    QueryEngineTool(
        query_engine=uber_engine,
        metadata=ToolMetadata(
            name="uber_10k",
            description=(
                "Provides information about Uber financials for year 2021"
            ),
        ),
    ),
]

s_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=query_engine_tools
)
```

### Install LlamaIndex and Wikipedia Reader
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/tools/OnDemandLoaderTool.ipynb

```python
%pip install llama-index-readers-wikipedia
```

```python
!pip install llama-index
```

### Initialize LlamaIndex Query Engine with Vector Store
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/evaluation/UpTrain.ipynb

```python
Settings.chunk_size = 512

documents = SimpleDirectoryReader("./nyc_wikipedia/").load_data()

vector_index = VectorStoreIndex.from_documents(
    documents,
)

query_engine = vector_index.as_query_engine()
```

### Initialize Two-Layer Adapter and Finetuning Engine (Python)
Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/finetuning/embeddings/finetune_embedding_adapter.ipynb

```python
base_embed_model = resolve_embed_model("local:BAAI/bge-small-en")
adapter_model = TwoLayerNN(
    384,  # input dimension
    1024,  # hidden dimension
    384,  # output dimension
    bias=True,
    add_residual=True,
)

finetune_engine = EmbeddingAdapterFinetuneEngine(
    train_dataset,
    base_embed_model,
    model_output_path="model5_output_test",
    model_checkpoint_path="model5_ck",
    adapter_model=adapter_model,
    epochs=25,
    verbose=True,
)
```


