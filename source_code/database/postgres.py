import os

import psycopg2


DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "smartresearchhub"
DB_USER = "jadduspoorthi"
DB_PASSWORD = os.getenv("SMARTRESEARCH_DB_PASSWORD")


def get_connection():
    """Create and return a PostgreSQL database connection."""

    if not DB_PASSWORD:
        raise RuntimeError(
            "SMARTRESEARCH_DB_PASSWORD environment variable is not set."
        )

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


if __name__ == "__main__":
    connection = get_connection()

    print("PostgreSQL connection successful.")

    connection.close()