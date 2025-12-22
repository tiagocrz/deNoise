import os
from tavily import TavilyClient
from langfuse import observe
from app_settings import TAVILY_API_KEY

@observe(as_type="tool")
def scrape_url_realtime(url: str, prompt: str) -> str:
    """
    Scrapes and summarizes content from a specific, external URL in real-time using Tavily.

    CRITICAL INSTRUCTION:
    - Use this function ONLY when the user explicitly provides a URL.
    - Example: "Please summarize the key news from this webpage: eco.sapo.pt?"
    - The URL can be in different formats but must always be passed as the 'url' argument. Key formats: "http", "https", "www", ".com", ".pt", ".org" or similar.
    - Do NOT use this for general knowledge questions.

    Args:
        url: The complete external URL to be scraped.
        prompt: The full, unmodified user question/prompt to guide the summarization.
    """
    
    tavily = TavilyClient(api_key=TAVILY_API_KEY)

    result = tavily.search(
        query=prompt,
        auto_parameters=True,
        topic="news",
        max_results=10,
        include_answer="advanced",
        include_domains=[url])

    return result['answer']