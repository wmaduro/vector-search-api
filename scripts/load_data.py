import os
import json
import requests
import psycopg
# import openai
import ollama
from time import sleep

# Initialize OpenAI client
# client = openai.OpenAI()


def setup_model(model_name: str = "nomic-embed-text"):
    """Pull the embedding model via Ollama."""
    try:
        # Check if the model exists
        ollama.embed(model=model_name, input="test")
        print(f"Model {model_name} is already available.")
        return True
    except ollama.ResponseError as e:
        if e.status_code == 404:
            # Model doesn't exist, attempt to pull it
            print(f"Pulling model {model_name}...")
            ollama.pull(model_name)
            return True
        else:
            print(f"Unexpected error: {e.error}")
            return False


# def get_embedding(text: str):
#     """Generate embedding using OpenAI API."""
#     response = client.embeddings.create(model="text-embedding-3-small", input=text)
#     return response.data[0].embedding


def get_embedding_ollama(text: str):
    """Generate embedding using Ollama API."""
    response = ollama.embed(model="nomic-embed-text", input=text)
    return response["embeddings"][0]


def fetch_books():
    """Fetch books across various subjects from Open Library."""
    categories = [
        "programming",
        "web_development",
        "artificial_intelligence",
        "computer_science",
        "software_engineering",
    ]
    all_books = []

    for category in categories:
        url = f"https://openlibrary.org/subjects/{category}.json?limit=10"
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for a bad response

        data = response.json()
        books = data.get("works", [])

        # Format each book
        for book in books:
            book_data = {
                "title": book.get("title", "Untitled"),
                "authors": [
                    author.get("name", "Unknown Author")
                    for author in book.get("authors", [])
                ],
                "first_publish_year": book.get("first_publish_year", "Unknown"),
                "subject": category,
            }
            all_books.append(book_data)

        print(f"Successfully processed {len(books)} books for {category}")

    if not all_books:
        print("No books were fetched from any category.")

    return all_books


def load_books_to_db():
    """Load books with embeddings into PostgreSQL."""

    # Wait for the database to be ready
    sleep(5)

    # Pull a embedding model from Ollama
    if not setup_model():
        exit(1)

    # Connect to the database
    conn = psycopg.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # Fetch data from the Open Library
    books = fetch_books()

    for book in books:
        description = (
            f"Book titled '{book['title']}' by {', '.join(book['authors'])}. "
            f"Published in {book['first_publish_year']}. "
            f"This is a book about {book['subject']}."
        )

        # Generate embedding
        # embedding = "[" + ",".join(["0"] * 1536) + "]"        # Placeholder embedding
        # embedding = get_embedding(description)                # OpenAI
        embedding_ollama = get_embedding_ollama(description)  # Ollama

        cur.execute(
            """
            INSERT INTO items (name, item_data, embedding_ollama)
            VALUES (%s, %s, %s)
            """,
            (book["title"], json.dumps(book),  embedding_ollama),
        )

    # Commit and close
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    try:
        load_books_to_db()
        print("Successfully loaded sample books!")
    except Exception as e:
        print(f"Error loading books: {e}")
