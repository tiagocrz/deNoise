# services/cosmos_db_service_mock.py (MOCK FILE)

class MockCosmosDBService:
    """
    A temporary class to replace the real CosmosDBService for testing.
    It returns hardcoded, made-up data for the RAG pipeline.
    """
    def __init__(self, db_name: str = "denoise_db"):
        # We don't need real clients (Gemini or Cosmos) in the mock
        print("MOCK SERVICE INITIALIZED: Using hardcoded test data.")
        pass

    def rag_retrieval(self, query: str, start_date: str, end_date: str, k: int = 5) -> str:
        """
        Mocks the RAG retrieval step. Returns structured context based on the query.
        """
        # STEP 1 & 2 (MOCKED): No embedding or vector search is performed.
        
        # NOTE: Added two new news items (4 and 5)
        mock_context = f"""
--- RAG CONTEXT ---
The user queried about: {query}. The time filter applied was from {start_date} to {end_date}.

[News Item 1] Title: Unicorn Funding Surge. Body: Startup 'InnovateCo' raised $150M in a Series C round last week, aiming to expand its market share in Europe.
[News Item 2] Title: Acquisition Alert. Body: Major tech company 'GlobalTech' acquired competitor 'QuickFix' in a strategic move to secure talent and intellectual property. The deal valued QuickFix at $50M.
[News Item 3] Title: Policy Update. Body: New Portuguese government policy offers tax incentives for early-stage startups focused on green technology, effective immediately.
[News Item 4] Title: Talent Shortage Report. Body: A new market report indicates a 30% rise in demand for AI engineers in Lisbon over the past quarter, signaling a severe talent shortage.
[News Item 5] Title: New Venture Studio Launch. Body: 'Alpha Studio' launched a new venture studio in Porto dedicated to building B2B SaaS solutions, planning to incubate five startups in the next 12 months.
-------------------------
"""  
        return mock_context

    def retrieve_user_instructions(self, user_id: str) -> str:
        """
        Mocks fetching custom instructions, expanded for different user types.
        """
        user_id = user_id.lower()
        
        if "investor" in user_id:
            # Instructions for Investors
            return "You are a cautious late-stage investor. Emphasize risk analysis, team experience, and market valuation when synthesizing information."
        
        elif "hub_manager" in user_id:
            # Instructions for Hub Managers
            return "You are focused on regional development (Lisbon/Porto) and policy. Highlight talent reports and local investment activity."
        
        elif "enthusiast" in user_id:
            # Instructions for General Enthusiasts
            return "Be positive and focus on aspirational news like new funding and inspiring success stories."
            
        else:
            # Default instructions
            return "You are a general innovation enthusiast. Be informative and neutral."