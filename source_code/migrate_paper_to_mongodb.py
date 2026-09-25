from source_code.database.postgres import get_connection
from source_code.database.mongodb import get_collection


def migrate_paper():
    # Get the existing paper and its chunks from PostgreSQL
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, authors, abstract, domain, year
        FROM papers
        WHERE id = 1;
        """
    )

    paper = cursor.fetchone()

    if not paper:
        print("Paper ID 1 was not found in PostgreSQL.")
        cursor.close()
        connection.close()
        return

    paper_id, title, authors, abstract, domain, year = paper

    cursor.execute(
        """
        SELECT chunk_index, content
        FROM paper_chunks
        WHERE paper_id = %s
        ORDER BY chunk_index;
        """,
        (paper_id,)
    )

    chunks = cursor.fetchall()

    cursor.close()
    connection.close()

    # Connect to MongoDB
    client, collection = get_collection()

    # Prevent duplicate MongoDB documents
    existing = collection.find_one({"paper_id": paper_id})

    if existing:
        print(
            f"Paper already exists in MongoDB with paper_id: {paper_id}"
        )
        client.close()
        return

    # Reconstruct the complete paper text
    full_text = "\n\n".join(
        chunk[1] for chunk in chunks
    )

    document = {
        "paper_id": paper_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "domain": domain,
        "year": year,
        "source_file": "samplepdf",
        "full_text": full_text,
        "chunk_count": len(chunks)
    }

    result = collection.insert_one(document)

    client.close()

    print("Paper migrated to MongoDB successfully.")
    print(f"MongoDB document ID: {result.inserted_id}")
    print(f"Paper ID: {paper_id}")
    print(f"Chunks stored in document: {len(chunks)}")


if __name__ == "__main__":
    migrate_paper()