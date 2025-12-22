# Tools Layer

Function-based utilities for AI agent automatic function calling. Implemented as functions (not classes) for compatibility with Gemini's function calling feature.

## Tools

### RAG Trigger (`choosing_rag.py`)

Searches the internal news database for relevant articles based on semantic similarity.

**Time Scopes:** "daily" (24h), "weekly" (7d), "monthly" (30d)

**Use Cases:** User makes a query that requires specific information to be answered

### Tavily Web Scraper (`choosing_tavily.py`)

Scrapes and summarizes content from external URLs in real-time using Tavily API.

**Use Cases:** User provides an explicit URL to analyze or summarize

### Text-to-Speech Converter (`text_to_speech.py`)

Converts text scripts to audio using ElevenLabs API, returning Base64-encoded data URI for playback.

## Integration

All tools are decorated with `@observe(as_type="tool")` for Langfuse monitoring and can be called by AI agents through automatic function calling.
