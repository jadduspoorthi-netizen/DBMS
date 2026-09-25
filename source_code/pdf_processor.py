from pathlib import Path
from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from all pages of a PDF."""

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(path)

    pages_text = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages_text.append(text)

    return "\n".join(pages_text)


def clean_text(text: str) -> str:
    """Perform basic text cleaning."""

    text = text.replace("\x00", " ")
    text = " ".join(text.split())

    return text


if __name__ == "__main__":
    pdf_path = "../dataset/samplepdf"

    extracted_text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_text(extracted_text)

    print(f"Extracted characters: {len(extracted_text)}")
    print(f"Cleaned characters: {len(cleaned_text)}")

    print("\nFirst 1000 characters:\n")
    print(cleaned_text[:1000])