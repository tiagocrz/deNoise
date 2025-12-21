from app_settings import (
    COSMOSDB_INDEXING_POLICY, COSMOSDB_VECTOR_EMBEDDING_POLICY, COSMOSDB_VECTOR_SEARCH_FIELDS,
    connect_to_cosmosdb
)
import os
import json 
import pandas as pd
from datetime import datetime, timedelta
from langchain_core.documents import Document
from langchain_community.vectorstores.azure_cosmos_db_no_sql import PreFilter, Condition, AzureCosmosDBNoSqlVectorSearch
from azure.cosmos import PartitionKey, exceptions
from langfuse import observe

from services.embedding_service import EmbeddingService
embeddings = EmbeddingService()


class CosmosDBService:
    """
    Handles connections to Azure CosmosDB and manages data operations 
    for VectorDB and UsersDB, including internal embedding generation.
    """
    def __init__(self):
        self.client, self.database = connect_to_cosmosdb()

        self.articles_db = self.database.get_container_client("newsArticles")
        self.vector_db = self.database.get_container_client("newsEmbeddings")
        self.user_db = self.database.get_container_client("userProfiles") 



    def insert_articles(self, container_name, articles: pd.DataFrame):
        """
        Simple bulk insert of objects in either non-vector containers.
        """
        container = self.database.get_container_client(container_name)
        for article in articles.to_dict(orient='records'):
            container.upsert_item(article)



    def index_article(self, contents:list[str], article_title:str, article_id:int, article_date:str) -> None:
        """
        Insert chunks with embeddings into Azure Cosmos DB.
        It can either be a company or opportunity file, based on the company_id or opportunity_id.
        Since the metadata is different, the metadata is added based on the company_id or opportunity_id.
        
        :param chunks: List of chunks to be indexed
        :param file_codename: Codename of the file or Memory id as string
        :param company_id: Company ID
        :param opportunity_id: Opportunity ID

        :return: If it doesn't raise an exception, it was successful
        """

        container_name = "newsEmbeddings"  
        
        try:
            documents = [
                Document(
                    page_content=json.dumps(str(content)),
                    metadata={
                        "title": article_title,
                        "article_id": str(article_id),
                        "date": article_date.split(' ')[0], # Only keep the actual date, not the time
                        "is_title": True if content == article_title else False
                    }
                )
                for content in contents
            ]

            partition_key = PartitionKey(path="/id")
            cosmos_container_properties = {"partition_key": partition_key}

            AzureCosmosDBNoSqlVectorSearch.from_documents(
                documents=documents,
                embedding=embeddings,
                cosmos_client=self.client,
                database_name='deNoise',
                container_name=container_name,
                #full_text_policy=None, # already None by default
                indexing_policy=COSMOSDB_INDEXING_POLICY,
                vector_embedding_policy=COSMOSDB_VECTOR_EMBEDDING_POLICY,
                cosmos_container_properties=cosmos_container_properties,
                vector_search_fields=COSMOSDB_VECTOR_SEARCH_FIELDS,
                cosmos_database_properties={},
                full_text_search_enabled=False
            )

        except Exception as e:
            print(f"Error indexing article: {e}")
            raise
        return     




    def get_time_range(self, start_str: str, end_str: str) -> list[str]:
        """
        Generates a list of date strings between start_str and end_str (inclusive).
        """
        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")
        
        date_list = []
        current_date = start_date

        while current_date <= end_date:
            # Convert back to string and add to list
            date_list.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)
            
        return date_list




    def build_full_context(self, vector_results: list) -> str:
        """
        1. Extracts unique article IDs.
        2. Queries Cosmos DB for all parts (Title + Body).
        3. Robustly finds the text field (checking 'content', 'text', etc.).
        """
        
        # 1. Extract Unique Article IDs
        unique_ids = {doc.metadata['article_id'] for doc in vector_results}
        
        if not unique_ids:
            return "No articles found."

        # 2. Query DB
        ids_formatted = ", ".join([f"'{aid}'" for aid in unique_ids])
        query = f"SELECT * FROM c WHERE c.metadata.article_id IN ({ids_formatted})"
        
        full_docs = list(self.vector_db.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        # 3. Organize Data
        articles_map = {}

        for item in full_docs:
            # Access nested metadata safely
            meta = item.get('metadata', {})
            art_id = meta.get('article_id')
            is_title = meta.get('is_title')
            
            if not art_id: 
                continue

            raw_content = item.get('text')
            # Clean the content if it's a JSON string 
            try:
                if raw_content:
                    clean_content = json.loads(raw_content)
                else:
                    clean_content = "[Content Empty in DB]"
            except (TypeError, json.JSONDecodeError):
                clean_content = str(raw_content)

            # Initialize ID in map
            if art_id not in articles_map:
                articles_map[art_id] = {"title": None, "body": None}

            # Store in correct slot
            if is_title:
                articles_map[art_id]["title"] = clean_content
            else:
                articles_map[art_id]["body"] = clean_content

        # 4. Build Final String
        formatted_context = []
        
        for i, (art_id, parts) in enumerate(articles_map.items(), 1):
            title = parts["title"] if parts["title"] else "Title not found"
            body = parts["body"] if parts["body"] else ""
            
            entry = f"ARTICLE {i}:\n{title}\n{body}\n"
            formatted_context.append(entry)

        return "\n".join(formatted_context)




    @observe(as_type="retriever")
    def rag_retrieval(self, query: str, start_date: str = None, end_date: str = None, k: int = 5) -> str:
        """
        Performs vector similarity search, handling embedding generation internally.

        Args:
            query: The raw text of the user's prompt or topics. (NEW: Raw text)
            start_date: ISO format string for the minimum news publication date.
            end_date: ISO format string for the maximum news publication date.
            k: Number of nearest neighbors (articles) to retrieve.
        """

        time_range = self.get_time_range(start_date, end_date) if start_date and end_date else []

        partition_key = PartitionKey(path="/id")
        cosmos_container_properties = {"partition_key": partition_key}

        # Initialize vector search
        vector_search = AzureCosmosDBNoSqlVectorSearch(
            cosmos_client=self.client,
            embedding=embeddings,
            database_name='deNoise',
            container_name='newsEmbeddings',
            vector_embedding_policy=COSMOSDB_VECTOR_EMBEDDING_POLICY,
            indexing_policy=COSMOSDB_INDEXING_POLICY,
            #vector_search_fields=COSMOSDB_VECTOR_SEARCH_FIELDS,
            cosmos_database_properties={},
            cosmos_container_properties=cosmos_container_properties
        )
        
        # build filters
        filter_conditions = []
        for date in time_range:
            filter_conditions.append(Condition(property="metadata.date", operator="$eq", value=date))

        print(filter_conditions)

        if filter_conditions:
            print("Applying filters.")
            pre_filter = PreFilter(conditions=filter_conditions, logical_operator="$or")
            print(pre_filter)


            results = vector_search.similarity_search(
                query=query,
                k=k,
                pre_filter=pre_filter
            )


        else:
            print("No filters applied.")
            results = vector_search.similarity_search(
                query=query,
                k=k,
            )


        if not results:
            return "No relevant articles found for the given query and date range."

        else:
            context = self.build_full_context(results)

        return context



    def retrieve_user_instructions(self, user_id: str) -> dict:
        """
        Fetches custom instructions AND display name from UserDB. 
        Returns a dictionary with keys 'system_instructions' and 'display_name'.
        """
        try:
            # We assume the document ID is the user_id and partition key is also user_id
            item = self.user_db.read_item(item=user_id, partition_key=user_id)
            
            return {
                "system_instructions": item.get("system_instructions", ""),
                "display_name": item.get("display_name", "")
            }
        
        except exceptions.CosmosResourceNotFoundError:
            # User doesn't exist yet, return default empty strings
            return {"system_instructions": "", "display_name": ""}
            
        except Exception as e:
            print(f"Error retrieving user profile: {e}")
            return {"system_instructions": "", "display_name": ""}
    


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