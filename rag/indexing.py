import warnings
warnings.filterwarnings("ignore")
import json 
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

from app_settings import (
    DOCUMENT_DB_URI,
    AZURE_PRIMARY_KEY, AZURE_URL,
    COSMOSDB_INDEXING_POLICY, COSMOSDB_VECTOR_EMBEDDING_POLICY, COSMOSDB_VECTOR_SEARCH_FIELDS,
    GEMINI_API_KEY,
    connect_to_cosmosdb
)

import pandas as pd
from google import genai
from google.genai import types
from langchain_core.documents import Document
from langchain_azure_ai.vectorstores import AzureCosmosDBNoSqlVectorSearch
from azure.cosmos import PartitionKey


def insert_articles(db, container_name, articles: pd.DataFrame):
    """
    Simple bulk insert of objects in either non-vector containers.
    """
    container = db.get_container_client(container_name)
    for article in articles.to_dict(orient='records'):
        container.upsert_item(article)



# Embedding Service Object (adapted implementation from classes)
class EmbeddingService:
    """
    Service for generating text embeddings using Google Gemini's embedding model.

    Uses gemini-embedding-001 with Matryoshka Representation Learning (MRL)
    to generate flexible-dimension embeddings for semantic search.
    """

    def __init__(self, output_dimensionality: int = 3072):
        """
        Initialize the EmbeddingService.

        Args:
            output_dimensionality: Embedding vector dimensions (128-3072).
                                 Recommended: 768, 1536, or 3072.
                                 Default: 3072 for optimal performance.
        """
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-embedding-001"
        self.output_dimensionality = output_dimensionality

    def embed_query(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: Input text to embed (max 2,048 tokens)

        Returns:
            List of floats representing the embedding vector

        Raises:
            ValueError: If text exceeds token limit
            Exception: If API call fails

        Example:
            >>> service = EmbeddingService()
            >>> embedding = service.generate_embedding("Hello world")
            >>> len(embedding)
            768
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.output_dimensionality
                )
            )

            # Extract the embedding values
            embedding = result.embeddings[0].values

            return embedding

        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            raise 

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Note: Due to API rate limits (100 RPM free tier), this processes
        texts sequentially. For production use with many texts, consider
        implementing rate limiting and batching strategies.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors, one per input text

        Example:
            >>> service = EmbeddingService()
            >>> texts = ["First text", "Second text"]
            >>> embeddings = service.generate_embeddings_batch(texts)
            >>> len(embeddings)
            2
        """
        embeddings = []

        for i, text in enumerate(texts):
            try:
                embedding = self.embed_query(text)
                embeddings.append(embedding)

                if (i + 1) % 10 == 0:
                    print(f"✅ Processed {i + 1}/{len(texts)} embeddings")

            except Exception as e:
                print(f"❌ Failed to embed text {i}: {text[:50]}... Error: {e}")
                # Append None for failed embeddings to maintain index alignment
                embeddings.append(None)

        print(f"✅ Completed: {len([e for e in embeddings if e is not None])}/{len(texts)} embeddings generated")
        return embeddings
    


# Instatiate embedding service
embeddings = EmbeddingService()



def index_article(contents:list[str], article_title:str, article_id:int, article_date:str) -> None:
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
                    "date": article_date,
                    "is_title": True if content == article_title else False
                }
            )
            for content in contents
        ]

        cosmosdb_client, cosmos_db = connect_to_cosmosdb()

        partition_key = PartitionKey(path="/id")
        cosmos_container_properties = {"partition_key": partition_key}

        AzureCosmosDBNoSqlVectorSearch.from_documents(
            documents=documents,
            embedding=embeddings,
            cosmos_client=cosmosdb_client,
            database_name='deNoise',
            container_name=container_name,
            full_text_policy=None,
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


