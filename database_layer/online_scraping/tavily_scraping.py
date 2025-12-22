import os
import hashlib
import uuid
from datetime import datetime, timedelta
from tavily import TavilyClient
from htmldate import find_date
import re
from app_settings import TAVILY_API_KEY

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

domains_to_check = [
    "empreendedor.com",
    "portugalstartupnews.com",
    "portugalstartups.com",
    "startupportugal.com",
    "portugalventures.pt",
    "observador.pt",
    "eco.sapo.pt",
    "essential-business.pt",
    "portugalbusinessesnews.com"
]


def extract_date(url, text_content=None):
    """
    Tries to find the publication date using htmldate, using one of the following:
    1. Checks the URL patterns (fastest).
    2. Fetches metadata from the URL (most accurate).
    3. Returns today's date if all else fails.

    Args:
        url: The URL of the article.
        text_content (optional): The raw HTML content of the article. Default == None.
    
    Returns:
        str: The extracted date in 'YYYY-MM-DD' format or today's date as fallback.
    """
    try:
        found_date = find_date(url, outputformat='%Y-%m-%d')
        if found_date:
            return found_date
        
    except Exception as e:
        print(f"Date extraction failed for {url}: {e}")

    return datetime.now().strftime("%Y-%m-%d")


# Aggressive text cleaning function (NOT USED)
def aggressive_clean(text):
    lines = text.split('\n')
    cleaned_lines = []
    seen_lines = set()

    # 1. AGGRESSIVE PATTERNS TO REMOVE
    # If a line contains ANY of these, it is deleted instantly.
    # We target GDPR, Cookies, Login, UI elements, and specific platform noise.
    garbage_triggers = [
        "login", "register", "sign in", "sign up", "subscribe", "subscrição",
        "cookie", "consent", "parceiros", "armazenamento", "device", "browser",
        "privacy policy", "terms of use", "termos e condições", "política de privacidade",
        "all rights reserved", "copyright", "powered by", "mybusiness.com",
        "share on", "compartilhar", "tweet", "follow us", "siga-nos",
        "no information for this section", "our apologies",
        "skip to content", "saltar os links", "outdated browser",
        "funcional", "estatísticas", "marketing", "preferências", # Cookie banner categories
        "ver mais", "saiba mais", "ler mais", "read more",
        "edit with live css", "write css",
        "image", "video", "shutterstock", "freepik", # Image captions often leak
        "whatsapp://", "facebook.com", "twitter.com", "linkedin.com"
    ]

    # 2. PATTERNS TO KEEP (Whitelist)
    # If a line matches these headers, we force keep it (unless it's garbage)
    header_indicators = ["===", "---"]

    for line in lines:
        original_line = line
        line = line.strip()

        # --- FILTER 1: Empty & Structure ---
        if not line:
            continue
        
        # Keep Markdown Headers (=== or ---)
        if any(x in line for x in header_indicators):
            cleaned_lines.append(line)
            continue

        # --- FILTER 2: Remove Markdown Images & Icons ---
        # Remove ![Alt](URL) completely
        line = re.sub(r'!\[.*?\]\(.*?\)', '', line)
        # Remove standalone image links often found in these scrapes
        if line.startswith("[![Image"):
            continue

        # --- FILTER 3: The "Garbage Word" Check ---
        line_lower = line.lower()
        if any(trigger in line_lower for trigger in garbage_triggers):
            continue

        # --- FILTER 4: The "Link" Analysis ---
        # We need to distinguish between a Navigation Link (Bad) and a Resource/Article Link (Good).
        
        # Check if line is PURELY a markdown link: [Text](URL)
        link_match = re.match(r'^\[(.*?)\]\(.*?\)$', line)
        
        if link_match:
            link_text = link_match.group(1)
            # LOGIC: 
            # If the link text is short (< 25 chars) and doesn't look like a book/resource title, kill it.
            # Navigation links are usually "Home", "News", "Economia" (Short).
            # Content links are "The Lean Startup", "Sonae investe seis milhões..." (Longer).
            if len(link_text) < 25:
                continue 
            
            # Additional check: If it looks like a date or author inside a link, kill it.
            if re.match(r'^\d', link_text) or "author" in original_line:
                continue

        # --- FILTER 5: Short Line Noise ---
        # If a line is very short, not a list item (*), and has no punctuation, it's likely UI noise.
        # e.g. "Lisboa", "Domingo", "10.5 C"
        if len(line) < 20 and not line.startswith("*") and not line.endswith(('.', ':', '?', '!')):
            continue

        # --- FILTER 6: Deduplication ---
        # Scrapes often repeat the Title 3 times.
        if line in seen_lines:
            continue
        
        seen_lines.add(line)
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def get_news_with_dates():
    """
    Fetches the latest entrepreneurship and startup funding news articles from Tavily,
    extracts their publication dates, and prepares them for database insertion.

    Returns:
        all_articles: A list of dictionaries, where each dictionary contains the
        'id', 'title', 'text', and 'date' of an article.
    """
    all_articles = []

    today = datetime.now()
    seven_days_ago = today - timedelta(days=7)

    today_dt = today.strftime("%Y-%m-%d")
    seven_days_ago_dt = seven_days_ago.strftime("%Y-%m-%d")
    
    for url in domains_to_check:
        print(f"Checking {url}...")
        
        try:
            response = tavily_client.search(
                query="latest entrepreneurship startup funding investment news",
                topic="general",
                start_date=seven_days_ago_dt,
                end_date=today_dt,
                max_results=5,
                include_raw_content=False,
                include_domains=[url],
                search_depth="advanced"
            )

            results = response.get("results", []) 
            
            for result in results:
                title = result["title"]
                result_url = result.get("url")       
            
                content = result["content"]
            
                published_date = extract_date(result_url, content)

                article_id = hashlib.md5(result_url.encode()).hexdigest()

                article_record = {
                    "id": article_id,
                    "title": title,
                    "text": content,
                    "date": published_date
                }

                all_articles.append(article_record)

        except Exception as e:
            print(f"Failed to fetch from {url}: {e}")

    return all_articles



