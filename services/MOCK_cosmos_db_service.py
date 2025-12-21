# services/cosmos_db_service_mock.py (MOCK FILE)
import os
from azure.cosmos import CosmosClient, exceptions
from google import genai

class MockCosmosDBService:
    """
    A temporary class to replace the real CosmosDBService for testing.
    It returns hardcoded, made-up data for the RAG pipeline.
    """
    def __init__(self, db_name: str = "deNoise"): # Ensure this matches your Azure DB name
        # Initialize Gemini
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) 

        # Initialize Cosmos
        self.client = CosmosClient(
            url=os.getenv("COSMOS_ENDPOINT"), 
            credential=os.getenv("COSMOS_KEY")
        )
        self.database = self.client.get_database_client(db_name)
        
        # Connect to Containers
        self.vector_db = self.database.get_container_client("newsEmbeddings")
        # Ensure you create a container named 'UserDB' in Azure with partition key '/user_id'
        self.user_db = self.database.get_container_client("userProfiles")

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
        Fetches custom instructions from UserDB. 
        Returns empty string if user not found.
        """
        try:
            # We assume the document ID is the user_id and partition key is also user_id
            item = self.user_db.read_item(item=user_id, partition_key=user_id)
            return item.get("system_instructions", "")
        
        except exceptions.CosmosResourceNotFoundError:
            # User doesn't exist yet, return default empty instructions
            return ""
        except Exception as e:
            print(f"Error retrieving user profile: {e}")
            return ""
    
    def sync_user_profile(self, user_data: dict):
        """
        Upserts (Create or Update) user profile data to the UserDB.
        """
        try:
            # Ensure the item has the required 'id' field for CosmosDB
            user_data["id"] = user_data["user_id"]
            
            self.user_db.upsert_item(user_data)
            return True
            
        except Exception as e:
            print(f"Error syncing user profile: {e}")
            raise e