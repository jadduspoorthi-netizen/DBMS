from sentence_transformers import SentenceTransformer

from source_code.database.postgres import get_connection


MODEL_NAME = "all-MiniLM-L6-v2"


def search_papers(query: str, top_k: int = 5):
    """Search papers using semantic similarity.

    Each paper appears at most once.
    The result uses the best-matching chunk from each paper.
    """

    model = SentenceTransformer(MODEL_NAME)

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )[0]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            p.id,
            p.title,
            p.domain,
            p.year,
            pc.chunk_index,
            pc.content,
            1 - (pe.embedding <=> %s::vector) AS similarity
        FROM paper_embeddings pe
        JOIN paper_chunks pc
            ON pe.chunk_id = pc.id
        JOIN papers p
            ON pc.paper_id = p.id
        WHERE pe.id = (
            SELECT pe2.id
            FROM paper_embeddings pe2
            JOIN paper_chunks pc2
                ON pe2.chunk_id = pc2.id
            WHERE pc2.paper_id = p.id
            ORDER BY pe2.embedding <=> %s::vector
            LIMIT 1
        )
        ORDER BY similarity DESC
        LIMIT %s;
        """,
        (
            query_embedding.tolist(),
            query_embedding.tolist(),
            top_k
        )
    )

    results = cursor.fetchall()

    cursor.close()
    connection.close()

    return results


if __name__ == "__main__":
    query = "research papers about semantic search and sentence embeddings"

    results = search_papers(query, top_k=5)

    print("\nSemantic Search Results")
    print("=" * 70)

    if not results:
        print("No matching papers found.")
    else:
        for rank, result in enumerate(results, start=1):
            (
                paper_id,
                title,
                domain,
                year,
                chunk_index,
                content,
                similarity
            ) = result

            print(f"\nResult #{rank}")
            print("-" * 70)
            print(f"Paper ID   : {paper_id}")
            print(f"Title      : {title}")
            print(f"Domain     : {domain}")
            print(f"Year       : {year}")
            print(f"Best Chunk : {chunk_index}")
            print(f"Similarity : {similarity:.4f}")
            print(f"Content    : {content[:500]}...")