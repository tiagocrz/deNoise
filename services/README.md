# Services Layer

Core business logic for orchestrating AI agents, database operations, and embedding generation.

## Services

### AgentsService (`agents_service.py`)

Orchestrates three specialized AI agents powered by Google Gemini (gemini-2.5-flash).

**AI Agents:**
- Conversational Agent - Agentic RAG with session memory and automatic function calling
- Report Generator - RAG for structured summaries
- Podcast Generator - Content generation with RAG and text-to-speech

**Features:** Per-user session management, user profile integration for personalization, Langfuse observability

**Tools Used:** rag_trigger (semantic search), scrape_url_realtime (real-time web search)

### CosmosDBService (`cosmos_db_service.py`)

Manages all interactions with Azure Cosmos DB across three containers: newsArticles, newsEmbeddings, and userProfiles.

**Capabilities:** Bulk article insertion, vector embedding storage, semantic similarity search, full article reconstruction, user profile persistence

**Features:** Dual embedding strategy (title and content), time-range filtering

### EmbeddingService (`embedding_service.py`)

Generates text embeddings using Google Gemini's embedding model (gemini-embedding-001).

**Configuration:** 3072 dimensions (configurable 128-3072)

**Features:** Batch processing for efficiency, Langfuse observability integration

## Architecture

All services use Langfuse `@observe` decorators for monitoring. AgentsService maintains stateful per-user conversation history.
