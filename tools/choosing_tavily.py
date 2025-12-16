import os
from tavily import TavilyClient
from langfuse import observe

@observe(as_type="tool")
def scrape_url_realtime(url: str, prompt: str) -> str:
    """
    Scrapes and summarizes content from a specific, external URL in real-time using Tavily.

    CRITICAL INSTRUCTION:
    - Use this function ONLY when the user explicitly provides a URL.
    - Example: "What does this link say: [URL]?"
    - Do NOT use this for general knowledge questions.

    Args:
        url: The complete external URL (http:// or https://) to be scraped.
        prompt: The full, unmodified user question/prompt to guide the summarization.
    """
    
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    result = tavily.search(
        query=prompt,
        auto_parameters=True,
        topic="news",
        max_results=10,
        include_answer="advanced",
        include_domains=url)

    return result