# Script to run both scrapers (Gmail and Tavily)  and update the database 

from app_settings import (COSMOSDB_INDEXING_POLICY, 
                          COSMOSDB_VECTOR_EMBEDDING_POLICY, 
                          connect_to_cosmosdb)

from database_layer.gmail_scraping.db_building import scrape_gmail
from database_layer.online_scraping.tavily_scraping import get_news_with_dates
from services.cosmos_db_service import CosmosDBService
from azure.cosmos import PartitionKey


def recreate_container(container_name: str):
    """
    Delete and recreate any container.
    This is the fastest way to clear all data.
    """
    
    cosmosdb_client, cosmos_db = connect_to_cosmosdb()
    
    # Delete the container
    try:
        cosmos_db.delete_container(container_name)
        print(f"Deleted {container_name} container")
    except Exception as e:
        print(f"Container might not exist: {e}")
    

    # Recreate the container
    partition_key = PartitionKey(path="/id")

    if container_name == "newsEmbeddings":
        cosmos_db.create_container_if_not_exists(
            id=container_name,
            partition_key=partition_key,
            indexing_policy=COSMOSDB_INDEXING_POLICY,
            vector_embedding_policy=COSMOSDB_VECTOR_EMBEDDING_POLICY
        )
    else:
        cosmos_db.create_container_if_not_exists(
            id=container_name,
            partition_key=partition_key
        )
    
    print(f"✅ Recreated {container_name} container")





if __name__ == "__main__":
    cosmosdb_service = CosmosDBService()

    # Recreate containers
    recreate_container("newsArticles")
    recreate_container("newsEmbeddings")

    
    # Fetch Gmail news
    gmail_news = scrape_gmail()
    print(f"Fetched {len(gmail_news)} news articles from Gmail newsletters.")

    
    # Fetch Tavily news 
    tavily_news = get_news_with_dates()
    print(f"Fetched {len(tavily_news)} news articles from Tavily.")


    # Insert news articles into CosmosDB
    cosmosdb_service.insert_articles("newsArticles", gmail_news)
    cosmosdb_service.insert_articles("newsArticles", tavily_news)


    # Create embeddings and index them 
    for article in list(cosmosdb_service.articles_db.read_all_items()):
        try:
            cosmosdb_service.index_article(
                contents=[article['title'], article['text']],
                article_title=article['title'],
                article_id=article['id'],
                article_date=article['date']
            )
            print(f"✅ Indexed successfully: {article['title']}")

        except Exception as e:
            print(f"❌ Failed to index article {article['title']}: {e}")


    print(f"✅ All {len(list(cosmosdb_service.articles_db.read_all_items()))} articles indexed.")