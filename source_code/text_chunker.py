from source_code.pdf_processor import extract_text_from_pdf, clean_text


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> list[str]:
    """Split text into overlapping chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


if __name__ == "__main__":
    pdf_path = "../dataset/samplepdf"

    extracted_text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_text(extracted_text)

    chunks = chunk_text(cleaned_text)

    print(f"Total characters: {len(cleaned_text)}")
    print(f"Number of chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks[:3], start=1):
        print(f"\n--- Chunk {i} ---")
        print(chunk[:500])