import os
import json
import dotenv
import requests
import psycopg
import openai
import ollama
from time import sleep

dotenv.load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI()


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


def get_embedding_openai_small(text: str):
    """Generate embedding using OpenAI API."""
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding

def get_embedding_openai_large(text: str):
    """Generate embedding using OpenAI API."""
    response = client.embeddings.create(model="text-embedding-3-large", input=text)
    return response.data[0].embedding

def get_embedding_ollama(text: str):
    """Generate embedding using Ollama API."""
    response = ollama.embed(model="nomic-embed-text", input=text)
    return response["embeddings"][0]


def fetch_books():
    """Fetch books across various subjects from Open Library."""
    categories = [
        # "programming",
        "web_development",
        # "artificial_intelligence",
        # "computer_science",
        # "software_engineering",
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

        # print(f"Successfully processed {len(books)} books for {category}")

    if not all_books:
        print("No books were fetched from any category.")

    all_books_formatted = []
    for book_data in all_books:
        description = (
            f"This is a book about {book_data['subject']}. "
            f"First Published in {book_data['first_publish_year']}. "            
            f"Book titled '{book_data['title']}' by {', '.join(book_data['authors'])}. "
        )
        all_books_formatted.append(description)

    print(f"all_books_formatted: {all_books_formatted}")

    return all_books

def delete_all_books():
    """Delete all entries from the items table."""
    try:
        conn = psycopg.connect("postgresql://postgres:password@localhost:5432/example_db")
    
        cur = conn.cursor()
        cur.execute("DELETE FROM items")
        conn.commit()
        cur.close()
        print("Successfully cleared the items table.")
    except Exception as e:
        print(f"Error clearing items table: {e}")
        conn.rollback()

def load_books_to_db():
    """Load books with embeddings into PostgreSQL."""

    # Wait for the database to be ready
    sleep(5)

    # Pull a embedding model from Ollama
    if not setup_model():
        exit(1)

    # Connect to the database
    conn = psycopg.connect("postgresql://postgres:password@localhost:5432/example_db")
    cur = conn.cursor()

    # Fetch data from the Open Library
    books = fetch_books()

    for book in books:
        # Check if the book already exists in the database
        cur.execute("SELECT 1 FROM items WHERE name = %s", (book["title"],))
        if cur.fetchone():
            print(f"Book '{book['title']}' already exists in the database. Skipping.")
            continue

        description = (
            # f"This is a book about {book['subject']}."
            f"First Published in {book['first_publish_year']}. "            
            # f"Book titled '{book['title']}' by {', '.join(book['authors'])}. "
        )

        print(f"description: {description}")

        # Generate embedding
        embedding_openai_small = get_embedding_openai_small(description)                # OpenAI
        print(f"openai embedding small: {len(embedding_openai_small)}")

        embedding_openai_large = get_embedding_openai_large(description)                # OpenAI
        print(f"openai embedding large: {len(embedding_openai_large)}")
        
        embedding_ollama = get_embedding_ollama(description)  # Ollama
        print(f"ollama embedding: {len(embedding_ollama)}")

        cur.execute(
            """
            INSERT INTO items (name, item_data, embedding_openai_small, embedding_openai_large, embedding_ollama)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (book["title"], json.dumps(book), embedding_openai_small, embedding_openai_large, embedding_ollama),
        )

    # Commit and close
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    try:

        fetch_books()

        # delete_all_books()
        # load_books_to_db()
        print("Successfully loaded sample books!")
    except Exception as e:
        print(f"Error loading books: {e}")
