import os
from pathlib import Path
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, PartitionKey


PROJECT_ROOT = Path(__file__).resolve().parent
env_path = PROJECT_ROOT / '.env'
print("Project root path:", PROJECT_ROOT)
load_dotenv(env_path, override=True)


## Check if the loading was successful
#if not os.getenv("GEMINI_API_KEY"):
#    raise ValueError("Failed to load environment variables from .env file")
#else:
#    print(os.getenv("GEMINI_API_KEY")[:5] + "..." )  # Print first 5 characters of the key for verification
#    print("Environment variables loaded successfully")


# Load the environment variables
DOCUMENT_DB_URI = os.getenv("DOCUMENT_DB_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AZURE_PRIMARY_KEY = os.getenv("AZURE_PRIMARY_KEY")
AZURE_URL = os.getenv("AZURE_URL")

COSMOSDB_INDEXING_POLICY = {
    "indexingMode": "consistent",
    "automatic": True,
    "includedPaths": [{"path": "/*"}],
    "excludedPaths": [
        {
            "path": "/\"_etag\"/?"
        },
        {
            "path": "/titleVector/*"
        },
        {
            "path": "/textVector/*"
        }
    ],
    "vectorIndexes":[
        {
            "path": "/titleVector",
            "type": "quantizedFlat"
        },
        {
            "path": "/textVector",
            "type": "quantizedFlat"
        }
    ]
}

COSMOSDB_VECTOR_EMBEDDING_POLICY = {
    "vectorEmbeddings":[
        {
            "path": "/titleVector",
            "dataType": "float32",
            "distanceFunction": "cosine",
            "dimensions": 3072
        },
        {
            "path": "/textVector",
            "dataType": "float32",
            "distanceFunction": "cosine",
            "dimensions": 3072
        }
    ]
}


COSMOSDB_VECTOR_SEARCH_FIELDS = {
        "text_field": 'content',   
        "embedding_field": 'embedding'           
    }


def connect_to_cosmosdb():
    client = CosmosClient(url=AZURE_URL, credential=AZURE_PRIMARY_KEY)
    db = client.get_database_client('deNoise')
    return client, db