import dotenv
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from database import get_db
import schemas
import openai
import ollama

dotenv.load_dotenv()

app = FastAPI(title="Vector Search API")
client = openai.OpenAI()


def get_embedding(text: str) -> List[float]:
    """Generate embedding using OpenAI API"""
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    print(f'get_embedding -> text {len(text)}')
    print(f'get_embedding -> usage {response.usage}')
    return response.data[0].embedding


def get_embedding_ollama(text: str) -> List[float]:
    """Generate embedding using Ollama API."""
    response = ollama.embed(model="nomic-embed-text", input=text)
    print(f'get_embedding_ollama -> text {len(text)}')
    print(f'get_embedding_ollama -> text {response}')
    return response["embeddings"][0]


@app.post("/search/", response_model=List[schemas.ItemResponse])
async def search_items(query: schemas.SearchQuery, db: Session = Depends(get_db)):
    """Search for similar items using vector similarity"""
    try:
        # Generate embedding for search query
        
        query_embedding = get_embedding(query.query)
        print(f'search -> query_embedding: {len(query_embedding)}')

        # Perform vector similarity search
        results = db.execute(
            text(
                """
                SELECT
                    id,
                    name,
                    item_data,
                    embedding <=> cast(:embedding as vector) as similarity
                FROM items
                ORDER BY embedding <=> cast(:embedding as vector)
                LIMIT :limit
                """
            ),
            {"embedding": query_embedding, "limit": query.limit},
        )

        # print(f'search -> query_embedding: {query_embedding} ')
       
        return [
            schemas.ItemResponse(
                id=row.id,
                name=row.name,
                item_data=row.item_data,
                similarity=row.similarity,
            )
            for row in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search_ollama/", response_model=List[schemas.ItemResponse])
async def search_items(query: schemas.SearchQuery, db: Session = Depends(get_db)):
    """Search for similar items using vector similarity"""
    try:
        # Generate embedding for search query
        print(f'search_ollama -> query.query {len(query.query)}')
        query_embedding = get_embedding_ollama(query.query)
        print(f'search_ollama -> query_embedding: {len(query_embedding)} ')
        
        # Perform vector similarity search
        results = db.execute(
            text(
                """
                SELECT
                    id,
                    name,
                    item_data,
                    embedding_ollama <=> cast(:embedding as vector) as similarity
                FROM items
                ORDER BY embedding_ollama <=> cast(:embedding as vector)
                LIMIT :limit
                """
            ),
            {"embedding": query_embedding, "limit": query.limit},
        )

        # print(f'search_ollama -> query_embedding: {query_embedding} ')
        return [
            schemas.ItemResponse(
                id=row.id,
                name=row.name,
                item_data=row.item_data,
                similarity=row.similarity,
            )
            for row in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
