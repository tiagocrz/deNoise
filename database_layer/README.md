# Database Layer

Data ingestion pipelines for scraping news and populating Azure Cosmos DB with embeddings for RAG.

## Components

### Gmail Scraping (`gmail_scraping/`)

Extracts articles from email newsletters using Gmail API with OAuth2 authentication.

**Supported Newsletters:**
- TLDR (dan@tldrnewsletter.com)
- Morning Brew (crew@morningbrew.com)
- Startup Portugal (contact@startupportugal.com)


### Tavily Scraping (`tavily_scraping/`)

Scrapes entrepreneurship news from Portuguese websites using Tavily API.

**Key Functions:**
- `get_news_with_dates()` - Fetches latest news from 9 Portuguese domains

**Domains:** empreendedor.com, portugalstartupnews.com, portugalstartups.com, startupportugal.com, portugalventures.pt, observador.pt, eco.sapo.pt, essential-business.pt, portugalbusinessesnews.com

**Configuration:** Last 7 days, 5 articles per domain, advanced search depth


Both scrapers can be called on-demand to refresh the database with latest news.