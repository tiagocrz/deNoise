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
    print(f"[Tool] Calling Tavily Online to scrape: {url}")
    
    try:
        # Implementation using Tavily's API (Mocked for now)
        # In production: Use self.tavily_client.search(...)
        
        response_text = (
            f"Tavily Summary for {url}\n"
            f"Tailored to prompt: '{prompt}'\n"
            f"Content: [Real-time scraped content would appear here...]"
        )
        return response_text

    except Exception as e:
        return f"Error: Could not retrieve content from URL. {str(e)}"