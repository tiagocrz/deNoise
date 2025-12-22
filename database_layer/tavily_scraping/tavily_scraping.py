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