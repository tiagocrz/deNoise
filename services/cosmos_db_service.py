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
    '''
    Handles all connections to Azure CosmosDB:
    - Inserting/updating/fetching user data
    - Inserting articles, their embeddings and indexing
    - RAG retrieval with date filtering
    '''
    def __init__(self):
        self.client, self.database = connect_to_cosmosdb()
        self.articles_db = self.database.get_container_client("newsArticles")
        self.vector_db = self.database.get_container_client("newsEmbeddings")
        self.user_db = self.database.get_container_client("userProfiles") 


    def insert_articles(self, container_name, articles: list[dict]) -> None:
        '''
        Insert all scraped articles in the container.
        '''
        container = self.database.get_container_client(container_name)
        for article in articles:
            clean_article = {}
            for k, v in article.items():
                if isinstance(v, pd.Timestamp):
                    clean_article[k] = v.isoformat().split('T')[0]
                else:
                    clean_article[k] = v

            container.upsert_item(clean_article)



    def index_article(self, contents:list[str], article_title:str, article_id:int, article_date:str) -> None:
        '''
        Embedds and indexes each article and its respective title separately into the CosmosDB vector store.
        '''

        container_name = "newsEmbeddings"  
        
        try:
            documents = [
                Document(
                    page_content=json.dumps(str(content)),
                    metadata={
                        "title": article_title,
                        "article_id": str(article_id),
                        "date": article_date,
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
        '''
        Generates a list of date strings (all days) between start_str and end_str (inclusive).
        This is to enable the filtering in CosmosDB.
        '''
        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")
        
        date_list = []
        current_date = start_date

        while current_date <= end_date:
            date_list.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)
            
        return date_list




    def build_full_context(self, vector_results: list) -> str:
        '''
        Builds full context joining the title and respective text body for each article, for more coherent and complete RAG output.
        '''
        unique_ids = {doc.metadata['article_id'] for doc in vector_results}
        if not unique_ids:
            return "No articles found."

        # Query DB
        ids_formatted = ", ".join([f"'{aid}'" for aid in unique_ids])
        query = f"SELECT * FROM c WHERE c.metadata.article_id IN ({ids_formatted})"
        
        full_docs = list(self.vector_db.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        articles_map = {}

        for item in full_docs:
            meta = item.get('metadata', {})
            art_id = meta.get('article_id')
            is_title = meta.get('is_title')
            date = meta.get('date')

            if not art_id: 
                continue

            raw_content = item.get('text')
            try:
                if raw_content:
                    clean_content = json.loads(raw_content)
                else:
                    clean_content = "[Content Empty in DB]"
            except (TypeError, json.JSONDecodeError):
                clean_content = str(raw_content)

            if art_id not in articles_map:
                articles_map[art_id] = {"title": None, "body": None}

            if is_title:
                articles_map[art_id]["title"] = clean_content
            else:
                articles_map[art_id]["body"] = clean_content
            
            articles_map[art_id]["date"] = date

        # Build final string
        formatted_context = []
        
        for i, (art_id, parts) in enumerate(articles_map.items(), 1):
            title = parts["title"] if parts["title"] else "Title not found"
            body = parts["body"] if parts["body"] else ""
            date = parts["date"] if parts["date"] else "Date not found"
            
            entry = f"ARTICLE {i} ({date}):\n{title}\n{body}\n"
            formatted_context.append(entry)

        return "\n".join(formatted_context)




    @observe(as_type="retriever")
    def rag_retrieval(self, query: str, start_date: str = None, end_date: str = None, k: int = 5) -> str:
        """
        Filters articles by date range and then performs similarity search between the embedded query and the embedded articles.
        Retrieves the top k relevant articles' contents as context for RAG.
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
        
        # Build filters
        filter_conditions = []
        for date in time_range:
            filter_conditions.append(Condition(property="metadata.date", operator="$eq", value=date))


        if filter_conditions:
            pre_filter = PreFilter(conditions=filter_conditions, logical_operator="$or")

            results = vector_search.similarity_search(
                query=query,
                k=k,
                pre_filter=pre_filter
            )


        else:
            results = vector_search.similarity_search(
                query=query,
                k=k,
            )


        if not results:
            return "No relevant articles found for the given query and date range."

        else:
            context = self.build_full_context(results)
            print(context)
        return context



    def retrieve_user_instructions(self, user_id: str) -> dict:
        """
        Fetches custom instructions and display name from UserDB. 
        It's also used to check if user exists for Login/Signup purposes.
        """
        try:
            item = self.user_db.read_item(item=user_id, partition_key=user_id)
            
            return {
                "system_instructions": item.get("system_instructions", ""),
                "display_name": item.get("display_name", "")
            }
        
        except exceptions.CosmosResourceNotFoundError:
            # User doesn't exist (yet)
            return None
            
        except Exception as e:
            print(f"Error retrieving user profile: {e}")
            return None
    


    def sync_user_profile(self, user_data: dict):
        """
        Upserts (create or update) user profile data to the UserDB.
        """
        try:
            # Ensure the item has the required 'id' field for CosmosDB
            user_data["id"] = user_data["user_id"]
            
            self.user_db.upsert_item(user_data)
            return True
            
        except Exception as e:
            print(f"Error syncing user profile: {e}")
            raise e