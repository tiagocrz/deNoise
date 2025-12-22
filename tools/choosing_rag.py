from typing import Literal
from datetime import datetime, timedelta
from langfuse import observe
from services.cosmos_db_service import CosmosDBService

@observe(as_type="tool")
def get_time_range_for_rag(time_scope: Literal["daily", "weekly", "monthly"] = "monthly") -> tuple[str, str]:
    """
    Calculates the precise start and end dates for RAG retrieval based on a time scope.
    """
    
    # Define the end date (fixing the day of project submission, 22nd December 2025, otherwise we would need to re-run the scraping periodically)
    now = datetime(2025, 12, 22, 15, 8, 58, 151763)
    end_date = now.isoformat()
    
    start_date = None

    # Calculate the start date based on the LLM chosen time_scope
    if time_scope == "daily":
        start_date = now - timedelta(hours=24)
        
    elif time_scope == "weekly":
        start_date = now - timedelta(days=7)
        
    elif time_scope == "monthly":
        start_date = now - timedelta(days=30)
        
    else:
        start_date = now - timedelta(days=30)
        
    # Return the dates as ISO format strings without the time component for database compatibility
    return start_date.isoformat().split('T')[0], end_date.split('T')[0]


@observe(as_type="tool")
def rag_trigger(query: str, time_scope: str = "monthly") -> str:
    """
    Searches the internal startup news database (CosmosDB) for relevant articles.
    
    Use this tool when the user asks about:
    - Recent startup news, funding rounds, or other news that you would find in TLDR or MorningBrew newsletters.
    - Market trends (e.g., "AI in Lisbon", "Green Tech investment").
    - Specific companies (e.g., "What is InnovateCo doing?").
    - Stock markets (e.g, "Updates on Nasdaq this week?").
    - General fact-checking or brainstorming requests.
    
    Args:
        query (str): The search keywords or topic.

        time_scope (str): The time scope for the search. Options: 'daily', 'weekly', 'monthly'. 
                    Defaults to 'monthly' if not specified.
                    Mapping Hints for the LLM:
                        - Choose 'daily' if the user prompt includes 'yesterday', 'today', '24 hours' or similar.
                        - Choose 'weekly' if the user prompt includes 'last week', 'recently', 'this week', 'since Monday' or similar.
                        - Choose 'monthly' if the user prompt includes 'last month', 'this month', or similar.

    Returns:
        str: Concatenated relevant articles or a message indicating no results found.
    """

    # 1. Instantiate Services
    db_service = CosmosDBService()

    # 2. Calculate Date Range (Internal Helper Logic)
    start_date, end_date = get_time_range_for_rag(time_scope)

    # 3. Retrieve Context from DB
    context = db_service.rag_retrieval(query, start_date, end_date)
    
    # 4. Return Result
    if not context:
        return "No relevant documents found in the internal database."
    
    return context