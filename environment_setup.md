===============================================================================
                    deNoise - Environment Setup Instructions
===============================================================================


The app is publicly deployed and can be tested at https://denoise.lovable.app/
To replicate the setup locally, follow the instructions below.

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

2.1 Create .env File
--------------------
Create a file named `.env` in the project root directory with the following:

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

2.2 How to Obtain API Keys
---------------------------

GEMINI API KEY:
1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key to your .env file

AZURE COSMOS DB:
1. Create an Azure account: https://azure.microsoft.com/
2. Create a Cosmos DB resource (NoSQL API)
3. Navigate to "Keys" section
4. Copy the URI (for AZURE_URL) and Primary Key (for AZURE_PRIMARY_KEY)
5. Create a database named "deNoise" in your Cosmos DB account

ELEVENLABS API KEY:
1. Visit: https://elevenlabs.io/
2. Sign up for an account
3. Navigate to Profile Settings → API Keys
4. Copy your API key

TAVILY API KEY:
1. Visit: https://tavily.com/
2. Sign up for an account
3. Get your API key from the dashboard
4. Copy to your .env file

LANGFUSE (for LLM monitoring):
1. Visit: https://langfuse.com/
2. Sign up for an account
3. Create a new project
4. Copy the Secret Key, Public Key, and Host URL

===============================================================================
3. GMAIL API SETUP (For Email Newsletter Scraping)
===============================================================================

3.1 Enable Gmail API
---------------------
1. Visit: https://console.cloud.google.com/
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

3.2 Create OAuth 2.0 Credentials
---------------------------------
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Configure the OAuth consent screen if prompted:
   - User Type: External
   - Add your email as a test user
4. Application type: "Desktop app"
5. Download the credentials JSON file
6. Rename it to `credentials.json`
7. Place it in: `database_layer/gmail_scraping/credentials.json`

3.3 First-Time Authentication
------------------------------
When you run the Gmail scraping script for the first time:
1. A browser window will open
2. Sign in with your Google account
3. Grant the requested permissions
4. A `token.json` file will be created automatically

===============================================================================
4. AZURE COSMOS DB SETUP
===============================================================================

4.1 Database Configuration
---------------------------
The application expects:
- Database name: "deNoise"
- Container with vector search capabilities
- The container will be created automatically on first run

4.2 Vector Search Configuration
--------------------------------
The database uses vector embeddings with:
- Embedding dimensions: 3072 (Gemini text-embedding-004)
- Distance function: Cosine similarity
- Two vector fields: titleVector and textVector

===============================================================================
5. RUNNING THE APPLICATION
===============================================================================

5.1 Start the FastAPI Backend
------------------------------
# Make sure your virtual environment is activated
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access the API documentation:
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc

5.2 Update News Database
-------------------------
# Run the database update script to populate with news:
python update_database.py


===============================================================================
8. VERIFICATION CHECKLIST
===============================================================================

Before running the application, verify:
[ ] Python 3.11+ installed
[ ] Virtual environment created and activated
[ ] All packages from requirements.txt installed
[ ] .env file created with all required API keys
[ ] Gmail credentials.json file in correct location (if using email scraping)
[ ] Azure Cosmos DB database "deNoise" created
[ ] Internet connection available for API calls

===============================================================================
9. NEXT STEPS
===============================================================================

After setup:
1. Test the API: uvicorn main:app --reload
2. Visit http://localhost:8000/docs to explore endpoints

===============================================================================
