import numpy as np
from sentence_transformers import SentenceTransformer

from source_code.text_chunker import chunk_text
from source_code.pdf_processor import extract_text_from_pdf, clean_text


MODEL_NAME = "all-MiniLM-L6-v2"


def generate_embeddings(chunks: list[str]):
    """Generate embeddings for a list of text chunks."""

    model = SentenceTransformer(MODEL_NAME)

    embeddings = model.encode(
        chunks,
        normalize_embeddings=True
    )

    return embeddings


if __name__ == "__main__":
    pdf_path = "../dataset/samplepdf"

    extracted_text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_text(extracted_text)

    chunks = chunk_text(cleaned_text)

    embeddings = generate_embeddings(chunks)

    print(f"Model: {MODEL_NAME}")
    print(f"Number of chunks: {len(chunks)}")
    print(f"Embedding shape: {embeddings.shape}")
    print(f"Embedding dimension: {embeddings.shape[1]}")

    print("\nFirst embedding:")
    print(embeddings[0][:10])

    np.save(
        "../results/sample_embeddings.npy",
        embeddings
    )

    print("\nEmbeddings saved successfully.")