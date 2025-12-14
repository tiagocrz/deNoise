from typing import Literal
from datetime import datetime, timedelta
from langfuse import observe
from services.MOCK_cosmos_db_service import MockCosmosDBService

@observe(as_type="tool")
# Ensure the function signature matches the tool you will expose to Gemini
def get_time_range_for_rag(time_scope: Literal["daily", "weekly", "monthly"] = "monthly") -> tuple[str, str]:
    """
    Calculates the precise start and end dates for RAG retrieval based on a time scope.
    
    Args:
        time_scope: A literal indicating the desired time range for RAG retrieval.
        
    Returns:
        A tuple containing the start_date and end_date as ISO format strings 
        (ready for CosmosDB filtering).
    """
    
    # 1. Define the end date (always the current moment)
    now = datetime.now()
    end_date = now.isoformat()
    
    start_date = None

    # 2. Calculate the start date based on the LLM-provided time_scope
    if time_scope == "daily":
        # Start date: 24 hours ago
        start_date = now - timedelta(hours=24)
        
    elif time_scope == "weekly":
        # Start date: 7 days ago
        start_date = now - timedelta(days=7)
        
    elif time_scope == "monthly":
        # Start date: 30 days ago (a standard approximation for a month)
        start_date = now - timedelta(days=30)
        
    else:
        # Fallback (should be 'monthly' if the LLM followed instructions and omitted the argument)
        start_date = now - timedelta(days=30)
        
    # 3. Return the dates as ISO format strings for database consumption
    return start_date.isoformat(), end_date


@observe(as_type="tool")
def rag_trigger(query: str, time_scope: str = "monthly") -> str:
    """
    Searches the internal startup news database (CosmosDB) for relevant articles.
    
    Use this tool when the user asks about:
    - Recent startup news, funding rounds, or acquisitions.
    - Trends in the ecosystem (e.g., "AI talent", "Green tech").
    - Specific companies known to be in the database.
    
    Args:
        query: The search keywords or topic.

        time_scope: The time scope for the search. Options: 'daily', 'weekly', 'monthly'. 
                    Defaults to 'monthly' if not specified.
                    Mapping Hints for the LLM:
                        - Choose 'daily' if the user prompt includes 'yesterday', 'today', '24 hours' or similar.
                        - Choose 'weekly' if the user prompt includes 'last week', 'recently', 'this week', 'since Monday' or similar.
                        - Choose 'monthly' if the user prompt includes 'last month', 'this month', or similar.
    """

    # 1. Instantiate Services
    db_service = MockCosmosDBService()

    # 2. Calculate Date Range (Internal Helper Logic)
    start_date, end_date = get_time_range_for_rag(time_scope)

    # 3. Retrieve Context from DB
    context = db_service.rag_retrieval(query, start_date, end_date)
    
    # 4. Return Result
    if not context:
        return "No relevant documents found in the internal database."
    
    return context