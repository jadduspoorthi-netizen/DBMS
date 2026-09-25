from source_code.semantic_search import search_papers


def retrieve_context(query: str, top_k: int = 5) -> dict:
    """
    Retrieve the most relevant paper chunks for a user question.
    """

    results = search_papers(query, top_k=top_k)

    sources = []
    context_parts = []

    for rank, result in enumerate(results, start=1):
        (
            paper_id,
            title,
            domain,
            year,
            chunk_index,
            content,
            similarity,
        ) = result

        sources.append(
            {
                "rank": rank,
                "paper_id": paper_id,
                "title": title,
                "domain": domain,
                "year": year,
                "chunk_index": chunk_index,
                "similarity": round(float(similarity), 4),
            }
        )

        context_parts.append(
            f"""
Source {rank}
Title: {title}
Domain: {domain}
Year: {year}
Similarity: {float(similarity):.4f}

Content:
{content}
"""
        )

    context = "\n".join(context_parts)

    return {
        "query": query,
        "context": context,
        "sources": sources,
    }