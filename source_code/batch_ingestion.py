from pathlib import Path

from source_code.upload_service import process_uploaded_paper
from source_code.database.postgres import get_connection


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_DIR = PROJECT_ROOT / "dataset"

DOMAINS = ["ML", "DBMS", "DS", "OS", "ES"]


def paper_already_exists(title: str) -> bool:
    """Check whether a paper with the same title already exists."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT 1 FROM papers WHERE LOWER(title) = LOWER(%s) LIMIT 1;",
        (title,)
    )

    exists = cursor.fetchone() is not None

    cursor.close()
    connection.close()

    return exists


def get_pdf_title(pdf_path: Path) -> str:
    """
    Temporary title based on filename.

    Example:
        ML1.pdf -> ML1
        DBMS12.pdf -> DBMS12

    Metadata can be improved later using papers.csv.
    """
    return pdf_path.stem


def ingest_domain(domain: str):
    """Ingest all PDFs from one domain folder."""

    domain_dir = DATASET_DIR / domain

    if not domain_dir.exists():
        print(f"\n[WARNING] Folder not found: {domain_dir}")
        return 0, 0

    pdf_files = sorted(domain_dir.glob("*.pdf"))

    print(f"\n{'=' * 70}")
    print(f"DOMAIN: {domain}")
    print(f"PDF files found: {len(pdf_files)}")
    print(f"{'=' * 70}")

    successful = 0
    skipped = 0

    for index, pdf_path in enumerate(pdf_files, start=1):

        title = get_pdf_title(pdf_path)

        print(f"\n[{index}/{len(pdf_files)}] {pdf_path.name}")

        if paper_already_exists(title):
            print(f"  SKIPPED: {title} already exists in database.")
            skipped += 1
            continue

        try:
            result = process_uploaded_paper(
                file_path=pdf_path,
                title=title,
                authors="",
                domain=domain,
                year=None,
            )

            print("  SUCCESS")
            print(f"  Paper ID : {result['paper_id']}")
            print(f"  Chunks   : {result['chunks']}")
            print(f"  MongoDB  : {result['mongodb_document_id']}")

            successful += 1

        except Exception as error:
            print(f"  FAILED: {error}")

    return successful, skipped


def main():
    """Run batch ingestion for all five domains."""

    print("\n" + "=" * 70)
    print("SMARTRESEARCH HUB - BATCH INGESTION")
    print("=" * 70)

    total_successful = 0
    total_skipped = 0

    for domain in DOMAINS:
        successful, skipped = ingest_domain(domain)

        total_successful += successful
        total_skipped += skipped

    print("\n" + "=" * 70)
    print("BATCH INGESTION COMPLETE")
    print("=" * 70)

    print(f"New papers ingested : {total_successful}")
    print(f"Papers skipped      : {total_skipped}")
    print(f"Total processed     : {total_successful + total_skipped}")

    print("\nChecking PostgreSQL...")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM papers;")
    paper_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM paper_chunks;")
    chunk_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM paper_embeddings;")
    embedding_count = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    print(f"Papers       : {paper_count}")
    print(f"Chunks       : {chunk_count}")
    print(f"Embeddings   : {embedding_count}")

    print("\nDone.")


if __name__ == "__main__":
    main()