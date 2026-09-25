from pathlib import Path

from source_code.pdf_processor import extract_text_from_pdf, clean_text
from source_code.text_chunker import chunk_text
from source_code.embedding_service import generate_embeddings
from source_code.database.postgres import get_connection
from source_code.database.mongodb import get_collection


PDF_PATH = "../dataset/samplepdf"

TITLE = "Multilingual Universal Sentence Encoder for Semantic Retrieval"
AUTHORS = "Yinfei Yang et al."
DOMAIN = "NLP"
YEAR = 2020


def ingest_paper():
    # ---------------------------------------------------------
    # 1. Read and process the PDF
    # ---------------------------------------------------------
    extracted_text = extract_text_from_pdf(PDF_PATH)
    cleaned_text = clean_text(extracted_text)

    # ---------------------------------------------------------
    # 2. Split the paper into chunks
    # ---------------------------------------------------------
    chunks = chunk_text(cleaned_text)

    # ---------------------------------------------------------
    # 3. Generate embeddings
    # ---------------------------------------------------------
    embeddings = generate_embeddings(chunks)

    # ---------------------------------------------------------
    # 4. Connect to PostgreSQL
    # ---------------------------------------------------------
    connection = get_connection()
    cursor = connection.cursor()

    # ---------------------------------------------------------
    # 5. Check whether the paper already exists
    # ---------------------------------------------------------
    cursor.execute(
        """
        SELECT id
        FROM papers
        WHERE title = %s;
        """,
        (TITLE,)
    )

    existing_paper = cursor.fetchone()

    if existing_paper:
        print(f"Paper already exists with ID: {existing_paper[0]}")

        cursor.close()
        connection.close()
        return

    try:
        # -----------------------------------------------------
        # 6. Insert paper metadata into PostgreSQL
        # -----------------------------------------------------
        cursor.execute(
            """
            INSERT INTO papers
                (title, authors, abstract, domain, year)
            VALUES
                (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                TITLE,
                AUTHORS,
                chunks[0][:1000],
                DOMAIN,
                YEAR
            )
        )

        paper_id = cursor.fetchone()[0]

        # -----------------------------------------------------
        # 7. Insert chunks and embeddings into PostgreSQL
        # -----------------------------------------------------
        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            cursor.execute(
                """
                INSERT INTO paper_chunks
                    (paper_id, chunk_index, content)
                VALUES
                    (%s, %s, %s)
                RETURNING id;
                """,
                (
                    paper_id,
                    index,
                    chunk
                )
            )

            chunk_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO paper_embeddings
                    (chunk_id, embedding)
                VALUES
                    (%s, %s);
                """,
                (
                    chunk_id,
                    embedding.tolist()
                )
            )

        # -----------------------------------------------------
        # 8. Commit PostgreSQL transaction
        # -----------------------------------------------------
        connection.commit()

        print("PostgreSQL ingestion completed.")
        print(f"Paper ID: {paper_id}")
        print(f"Chunks inserted: {len(chunks)}")
        print(f"Embedding dimension: {embeddings.shape[1]}")

    except Exception:
        connection.rollback()
        cursor.close()
        connection.close()
        raise

    cursor.close()
    connection.close()

    # ---------------------------------------------------------
    # 9. Store the complete paper in MongoDB
    # ---------------------------------------------------------
    client, collection = get_collection()

    mongo_document = {
        "paper_id": paper_id,
        "title": TITLE,
        "authors": AUTHORS,
        "abstract": chunks[0][:1000],
        "domain": DOMAIN,
        "year": YEAR,
        "source_file": Path(PDF_PATH).name,
        "full_text": cleaned_text
    }

    collection.insert_one(mongo_document)

    client.close()

    print("MongoDB document inserted successfully.")
    print(f"MongoDB paper_id: {paper_id}")


if __name__ == "__main__":
    ingest_paper()