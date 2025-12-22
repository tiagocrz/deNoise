# deNoise

**AI-Powered News Processing Platform with RAG Capabilities**

> A Capstone Project for the Data Science Degree at NOVA IMS

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)

---

## Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Detailed Setup](#-detailed-setup)
- [Project Structure](#-project-structure)

---

## Overview

[deNoise](https://denoise.lovable.app/) is an intelligent news processing platform that leverages AI technologies to help users cut through information overload. The system combines Retrieval-Augmented Generation (RAG), vector databases, and large language models to provide three core capabilities, seamlessly accessible whether you’re on a PC or mobile device:

1. **Conversational Chat Interface** - Natural language interaction with your news database
2. **Automated Report Generation** - Create structured, topic-focused news summaries
3. **AI-Powered Podcast Creation** - Convert news content into engaging audio formats

The platform can automatically scrape and process news from email newsletters, store them with semantic embeddings in a vector database, and provide intelligent retrieval.
In the implementation, the current date corresponds to 2025/12/22 (date of final scraping), to make daily, weekly and monthly time windows work; however, the scraping could be performed at any time. This was a deliberate choice to keep the setup unchanged until the project defence day.

---

## Key Features

### Gmail Newsletter Scraping Pipeline

- **Authenticated Email Access**: Secure OAuth2 authentication with Gmail API
- **Multi-Source Newsletter Extraction**: Custom scrapers for TLDR, Morning Brew, and Startup Portugal
- **Automated News Parsing**: Extracts individual news articles from newsletter digests
- **Direct Database Integration**: Scraped content flows directly into CosmosDB

### Tavily Web Scraping Integration

- **API-Powered Extraction**: Leverages Tavily's intelligent web scraping capabilities
- **Real-Time Information**: On-demand pipeline ensures up-to-date news availability

### Azure Cosmos DB Infrastructure

- **Database Architecture**: 
  - **newsArticles container**: Stores raw news articles with metadata
  - **newsEmbeddings container**: Embedded news articles for semantic search (3072-dimensional vectors)
  - **userProfiles container**: User data including their custom system instructions
- **Direct Scraping Integration**: The Gmail extraction pipeline uploads directly to Cosmos
- **RAG-Ready**: Fully configured for Retrieval-Augmented Generation workflows

### RAG (Retrieval-Augmented Generation) Pipeline

- **Multi-Agent Support**: Powers Chat, Report, and Podcast generation
- **Semantic Document Retrieval**: Vector similarity search based on user queries
- **Dual Source Search**: The conversational agent can combine database RAG with real-time Tavily web search
- **Context-Aware Responses**: Retrieves most relevant news articles for accurate AI generation

### Three Specialized AI Agents

- **Conversational Agent (Chat)**: 
  - Real-time question answering with session memory
  - Automatic function calling for RAG and Tavily search
  - Personalized responses using user profile instructions
  
- **Report Generator**: 
  - Structured, topic-focused news summaries
  - Customizable time ranges (daily, weekly, monthly)
  - Multiple output formats (executive summary, bullet points, detailed analysis, etc.)
  
- **Podcast Generator**: 
  - Converts news articles into natural audio narratives
  - ElevenLabs text-to-speech integration
  - Configurable podcast styles and formats

### Lovable Frontend Application

- **Live and Functional**: Fully deployed interface at [lovable.app](https://denoise.lovable.app/)
- **Four Core Pages**:
  - **Home**: Landing page and platform overview
  - **Chat**: Conversational interface with real-time AI responses
  - **Report**: Topic selection and report generation
  - **Podcast**: Audio content creation with customization options
- **User Authentication**: Login/signup flow with profile management
- **My Profile Section**: Customizable user preferences and system instructions
- **Input Forms**: Text boxes and options for user prompts and preferences
- **Backend-Ready**: UI designed for seamless FastAPI integration

### FastAPI Backend Integration

- **REST API Architecture**: Clean endpoints for all agent interactions
- **Request/Response Models**: Pydantic validation for type safety
- **User Session Management**: Per-user conversation history and context
- **Production-Ready**: Backend deployed in Render 

### User Profile & Personalization

- **CosmosDB User Storage**: User data persisted in database 
- **Custom System Instructions**: Per-user AI behavior customization
- **Profile Integration**: User preferences automatically injected into all AI agents
- **Display Name Support**: Personalized greetings in conversational responses
- **Cross-Session Persistence**: User settings maintained across logins

### Observability & Monitoring

- **Langfuse Integration**: Observing LLM calls (inputs, returns and function calling)
- **Health Check Endpoints**: Monitor API availability and status

---

## Small & Cool details

- **All features** work whether the user is logged in or not; However we encourage users to create an account to take advantage of the personalization settings! 
- The user has the ability to export both reports and podcasts
- The frontend is ready to display outputs in markdown format
- If the user tries to sign in without singing up first, the platform will not let them sign in and the user will be prompted to create an account
- When the user defines a display name in the "My Profile" page, the conversational agent will address them accordingly

---

## Tech Stack

### Backend Technologies

#### LLM Provider: Google Gemini
- **Model**: gemini-2.5-flash for text generation
- **Embeddings**: gemini-embedding-001 (3072 dimensions)
- **Rationale**: 
  - 3 month Free tier offers more than enough capacity for our needs
  - Team familiarity with the platform
  - Seamless integration of both LLM and embedding models in a unified system

#### Central Framework: LangChain
- **Core Packages**:
  - `langchain-core` - Core LangChain functionality
  - `langchain-azure-ai` - Azure service integrations
  - `langchain-community` - Community-driven components
- **Purpose**: Central tool for LLM workflow development
- **Benefits**:
  - Simplifies interaction with both LLM and database
  - Seamless integration with Azure CosmosDB
  - Streamlines RAG pipeline development

#### Other Python Libraries
- **google-genai** - Direct management of Gemini LLMs and embedding models
- **azure-cosmos** - Straightforward interface for Azure CosmosDB operations
- **pandas** - Dataset management for scraped articles
- **python-dotenv** - Secure API key management 
- **elevenlabs** - Text-to-speech integration for podcast generation
- **beautifulsoup4** & **lxml** - HTML parsing and web content extraction
- **google-api-python-client** & **google-auth-oauthlib** - Gmail API authentication and operations

#### API Framework
- **FastAPI** - Modern, high-performance REST API web framework
- **Uvicorn** - Server for production deployment
- **Pydantic** - Request/response validation and data modeling

#### Observability
- **Langfuse** - LLM performance tracking, token usage monitoring, and tracing

### Database: Azure Cosmos DB

#### Vector Search Configuration
- **Embedding Dimensions**: 3072 (Gemini gemini-embedding-001)
- **Index Type**: Quantized flat vectors for efficient similarity search
- **Distance Function**: Cosine similarity
- **Dual Vector Fields**: Separate embeddings for article titles and content

### Frontend: Lovable

- **Framework**: Lovable (React-based)
- **Hosting**: Free hosting provided by Lovable platform
- **Rationale**:
  - Intuitive and streamlined development experience
  - Quick deployment capabilities
  - User-friendly interface development
  - No hosting costs

### External APIs & Services

- **Gmail API** - Newsletter scraping with OAuth2 authentication
- **Tavily API** - Real-time web search and Portuguese content retrieval
- **ElevenLabs API** - High-quality text-to-speech for podcast generation

### Development Tools

- **Git** - Version control
- **VS Code** - Primary IDE

---

## Detailed Setup

For comprehensive setup instructions including:
- Complete environment configuration
- API keys needed
- Gmail OAuth2 setup
- Azure Cosmos DB configuration

**See [environment_setup.md](environment_setup.md)**

---

## Project Structure

```
deNoise/
├── main.py                                   # FastAPI application entry point
├── app_settings.py                           # Configuration and environment variables
├── update_database.py                        # Database update script
├── requirements.txt                          # Python dependencies
├── README.md                                 # This file
├── environment_setup.md                      # Detailed setup instructions
├── .env                                      # Environment variables (create this)
├── .gitignore                                # Git ignore file
│   
├── database_layer/                           # Data ingestion and processing
│   ├── README.md                             # Database layer documentation
│   ├── gmail_scraping/                       # Email newsletter scraping 
│   │   ├── gmail_auth.py                     # OAuth2 authentication
│   │   ├── scrapers.py                       # Email parsing and extraction
│   │   └── db_building.py                    # Database population
│   │
│   └── tavily_scraping/                      # Web search integration
│       └── tavily_scraping.py                # Tavily API wrapper
│
├── services/                                 # Core business logic
│   ├── README.md                             # Services layer documentation
│   ├── agents_service.py                     # AI agents orchestration
│   ├── cosmos_db_service.py                  # Database operations
│   └── embedding_service.py                  # Vector embeddings generation
│    
├── tools/                                    # AI agent tools
│   ├── README.md                             # Tools layer documentation
│   ├── choosing_rag.py                       # RAG tool for semantic search
│   ├── choosing_tavily.py                    # Real-time web search tool
│   └── text_to_speech.py                     # Audio generation tool
│    
├── prompts/                                  # System prompts for AI agents
│   ├── conversational_agent_system.txt
│   ├── report_generator_system.txt
│   └── podcast_generator_system.txt
│
├── utils/                                    # Utility functions
│   └── prompt_manager.py                     # Prompt loading and formatting
│
└── docs/                                     
    └── ARCHITECTURE.md                       # architecture decisions and technical justifications

```

---

**Built with ❤️ by NOVA IMS Data Science Students Francisco Ferreira, Gonçalo Tacão, João Pedro de Sousa and Tiago da Cruz**