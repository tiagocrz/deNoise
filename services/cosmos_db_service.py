# Methods that interact with CosmosDB

import os
from azure.cosmos import CosmosClient
from google import genai
#from langfuse import observe

class CosmosDBService:
    """
    Handles connections to Azure CosmosDB and manages data operations 
    for VectorDB, and UsersDB (in the future), including internal embedding generation.
    """
    def __init__(self, db_name: str = "METER AQUI NOME DA DB"):
        # Initialize Gemini client for embedding generation
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) 

        self.client = CosmosClient(
            url=os.getenv("COSMOS_ENDPOINT"), 
            credential=os.getenv("COSMOS_KEY")
        )
        self.database = self.client.get_database_client(db_name)
        
        self.vector_db = self.database.get_container_client("VectorDB(METER NOME REAL)")
        #self.user_db = self.database.get_container_client("UserDB") FOR THE FUTURE
        
    #@observe(as_type="retrieval")
    def rag_retrieval(self, query: str, start_date: str, end_date: str, k: int = 5) -> str:
        """
        Performs vector similarity search, handling embedding generation internally.

        Args:
            query: The raw text of the user's prompt or topics. (NEW: Raw text)
            start_date: ISO format string for the minimum news publication date.
            end_date: ISO format string for the maximum news publication date.
            k: Number of nearest neighbors (articles) to retrieve.
        """
        # STEP 1: Generate Embedding
        query_embedding = self.gemini_client.embeddings.embed_content(
            model='text-embedding-004', # Best practice to specify model
            content=query
        )
        
        # STEP 2: Execute Vector Search (using query_embedding, start_date, end_date)
        # ... (CosmosDB Vector Search query logic) ...
        
        retrieved_items = [
            f"Title: Article 1. Body: Some relevant news text. Date: {start_date}",
            f"Title: Article 2. Body: More relevant news text. Date: {end_date}",
        ] 
        
        context = "\n---\n".join(retrieved_items)
        return context


    # FOR CUSTOM USER INSTRUCTIONS
    def retrieve_user_instructions(self, user_id: str) -> str:
        """Fetches custom instructions from UserDB based on user_id."""
        # Implementation involves querying UserDB based on user_id [cite: 99]
        # Placeholder for implementation:
        if user_id == "investor_123":
            return "You are a skeptical investment analyst. Focus on risks and long-term viability."
        return ""
    
    def sync_user_profile(self, user_data: dict):
        """Writes/updates user profile data to the UserDB container[cite: 273, 297]."""
        # Implementation involves updating the document in UserDB
        print(f"Syncing user profile for {user_data.get('user_id')}")