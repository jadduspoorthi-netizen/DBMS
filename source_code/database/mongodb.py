from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "smartresearchhub"
COLLECTION_NAME = "papers"


def get_collection():
    """Connect to MongoDB and return the papers collection."""

    client = MongoClient(MONGO_URI)

    database = client[DATABASE_NAME]
    collection = database[COLLECTION_NAME]

    return client, collection


if __name__ == "__main__":
    client, collection = get_collection()

    print("MongoDB connection successful.")
    print(f"Database   : {DATABASE_NAME}")
    print(f"Collection : {COLLECTION_NAME}")

    client.close()