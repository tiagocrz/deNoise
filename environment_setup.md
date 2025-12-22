===============================================================================
                    deNoise - Environment Setup Instructions
===============================================================================


The app is publicly deployed and can be tested at https://denoise.lovable.app/
To develop the setup locally, we employed the following:

PREREQUISITES
-------------
- Python 3.11
- API keys for required services (see API Keys section below)

===============================================================================
1. PYTHON ENVIRONMENT SETUP
===============================================================================

1.1 Create Virtual Environment
-------------------------------
# Windows (PowerShell):
py -3.11 -m venv venv
.\venv\Scripts\activate

# Linux/macOS:
python3.11 -m venv venv
source venv/bin/activate


1.2 Install Dependencies
-------------------------
pip install --upgrade pip
pip install -r requirements.txt



===============================================================================
2. API KEYS & ENVIRONMENT VARIABLES
===============================================================================

2.1 Created .env File
--------------------
Created a file named `.env` in the project root directory with the following:

# Google Gemini AI API
GEMINI_API_KEY=your_gemini_api_key_here

# Azure Cosmos DB Configuration
AZURE_PRIMARY_KEY=your_azure_cosmos_primary_key_here
AZURE_URL=your_azure_cosmos_url_here

# ElevenLabs API (Text-to-Speech)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Tavily API (Web Search)
TAVILY_API_KEY=your_tavily_api_key_here

# Langfuse (LLM Observability - Optional)
LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
LANGFUSE_HOST=https://cloud.langfuse.com


===============================================================================
3. GMAIL API SETUP (For Email Newsletter Scraping)
===============================================================================

3.1 Enabled the Gmail API for the account of one of the team members (who was already subscribed to the target newsletters)
---------------------------------

3.2 Create OAuth 2.0 Credentials to allow the API to access the "Newsletters" folder inside the inbox
---------------------------------

3.3 Note: The scraper only works if the target account has the exact same configuration as follows:
   - "Newsletter" folder in the labels
   - A subscription to the following newsletters: MorningBrew, TLDR, StartupPortugal
   - OAuth 2.0 Credentials file (JSON) in the path database_layer/gmail_scraping/credentials.json
---------------------------------

===============================================================================
4. AZURE COSMOS DB SETUP
===============================================================================

4.1 Database Configuration
---------------------------
The application expects:
- Database name: "deNoise"
- Container with vector search capabilities named "newsEmbeddings"
- Container for news articles "newsArticles"
- Container for user profiles "userProfiles"


===============================================================================
5. BACKEND DEPLOYMENT
===============================================================================

During development, whenever we needed to test a specific function/method, we used a notebook to check the outputs. Afterwards, whenever we finished a new feature, the backend was always deployed directly to the production environment on Render which is connected to the frontend. This ensured that we were testing the application in a real and consistent environment, through the lens of the final user.