from pathlib import Path

from source_code.pdf_processor import extract_text_from_pdf, clean_text
from source_code.text_chunker import chunk_text
from source_code.embedding_service import generate_embeddings
from source_code.database.postgres import get_connection
from source_code.database.mongodb import get_collection


# Project root → dataset/uploads
PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = PROJECT_ROOT / "dataset" / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def process_uploaded_paper(
    file_path: str,
    title: str,
    authors: str,
    domain: str,
    year: int
):
    """
    Process an uploaded research paper.

    Pipeline:
    PDF → Text → Chunks → Embeddings
        → PostgreSQL + pgvector
        → MongoDB
    """

    # -------------------------------------------------
    # 1. Check whether the paper already exists
    # -------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM papers
        WHERE title = %s;
        """,
        (title,)
    )

    existing_paper = cursor.fetchone()

    if existing_paper:
        cursor.close()
        connection.close()

        raise ValueError(
            f"A paper with this title already exists. "
            f"Paper ID: {existing_paper[0]}"
        )

    cursor.close()
    connection.close()

    # -------------------------------------------------
    # 2. Extract PDF text
    # -------------------------------------------------

    extracted_text = extract_text_from_pdf(file_path)
    cleaned_text = clean_text(extracted_text)

    if not cleaned_text:
        raise ValueError(
            "No readable text was found in the PDF."
        )

    # -------------------------------------------------
    # 3. Create text chunks
    # -------------------------------------------------

    chunks = chunk_text(cleaned_text)

    if not chunks:
        raise ValueError(
            "Could not create text chunks from the PDF."
        )

    # -------------------------------------------------
    # 4. Generate embeddings
    # -------------------------------------------------

    embeddings = generate_embeddings(chunks)

    # -------------------------------------------------
    # 5. Insert paper into PostgreSQL
    # -------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO papers
                (title, authors, abstract, domain, year)
            VALUES
                (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                title,
                authors,
                chunks[0][:1000],
                domain,
                year
            )
        )

        paper_id = cursor.fetchone()[0]

        # -------------------------------------------------
        # 6. Store chunks and embeddings
        # -------------------------------------------------

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

        connection.commit()

    except Exception:

        connection.rollback()
        cursor.close()
        connection.close()

        raise

    cursor.close()
    connection.close()

    # -------------------------------------------------
    # 7. Store complete document in MongoDB
    # -------------------------------------------------

    client, collection = get_collection()

    try:

        mongo_document = {
            "paper_id": paper_id,
            "title": title,
            "authors": authors,
            "abstract": chunks[0][:1000],
            "domain": domain,
            "year": year,
            "source_file": Path(file_path).name,
            "full_text": cleaned_text,
            "chunk_count": len(chunks)
        }

        collection.insert_one(mongo_document)

    finally:
        client.close()

    # -------------------------------------------------
    # 8. Return processing information
    # -------------------------------------------------

    return {
        "paper_id": paper_id,
        "title": title,
        "authors": authors,
        "domain": domain,
        "year": year,
        "chunks_created": len(chunks),
        "embedding_dimension": embeddings.shape[1]
    }