"""
Sample script to connect to an Azure Cosmos DB for MongoDB (vCore) account
using the standard MongoDB drivers (pymongo).

Usage:
  - Set the connection string in the environment variable `COSMOS_MONGO_URI`
	(recommended) or paste it when prompted.
  - Install dependencies: `pip install -r requirements.txt`
  - Run: `python Untitled-1.py`

Important:
  - Copy the connection string from the Azure Portal -> your Cosmos account -> Connection String.
  - Make sure your client IP is allowed in the Cosmos account's network settings.
  - Do NOT commit credentials to source control.
"""

import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError


def get_mongo_uri():
	"""Return the connection string from env var or prompt the user."""
	uri = os.getenv("COSMOS_MONGO_URI")
	if uri:
		return uri
	# fallback to interactive prompt (avoid pasting into shared logs)
	print("Enter MongoDB connection string for Azure Cosmos DB for MongoDB:")
	return input().strip()


def main():
	uri = get_mongo_uri()
	if not uri:
		print("No connection string provided. Set COSMOS_MONGO_URI or paste when prompted.")
		return

	# Create client. The URI from the portal typically contains the required options
	# (ssl=true, replicaSet=globaldb, retryWrites=false, etc.). Modern pymongo will honor them.
	try:
		client = MongoClient(uri, serverSelectionTimeoutMS=5000)
		# Trigger server selection / connection check
		print("Connected to server, server info: ")
		try:
			print(client.server_info())
		except Exception:
			# server_info() may fail for some Cosmos accounts; fall back to listing DBs
			pass

		print("Databases:")
		for name in client.list_database_names():
			print(" -", name)

		# Replace 'your_database' with one of the databases listed above or iterate
		# through all databases and collections to sample documents.
		for db_name in client.list_database_names():
			db = client.get_database(db_name)
			try:
				coll_names = db.list_collection_names()
			except Exception:
				coll_names = []
			if not coll_names:
				continue
			print(f"\nDatabase: {db_name}")
			for coll_name in coll_names:
				coll = db.get_collection(coll_name)
				sample = coll.find_one()
				print(f"  Collection: {coll_name}, sample document: {sample}")

	except PyMongoError as e:
		print("Failed to connect or query the Cosmos DB for MongoDB account:", e)


if __name__ == '__main__':
	main()

