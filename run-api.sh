#!/bin/bash

# Store the current directory
ORIGINAL_DIR=$(pwd)

# Function to return to original directory on exit
cleanup() {
    echo "Returning to original directory: $ORIGINAL_DIR"
    cd "$ORIGINAL_DIR"
}

# Set trap to ensure cleanup happens on script exit (Ctrl+C, normal exit, etc.)
trap cleanup EXIT

echo "Starting API server..."
echo "Original directory: $ORIGINAL_DIR"

# Change to the API project directory
cd /home/maduro/repo-ai/RAG/pgvector-vector-search-api/api

echo "Changed to API directory: $(pwd)"

# Run uvicorn server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload