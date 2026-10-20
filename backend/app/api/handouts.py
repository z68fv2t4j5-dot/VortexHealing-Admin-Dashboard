from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from pydantic import BaseModel
from handouts_service import HandoutsIndexer
import httpx
import sys
import os

router = APIRouter()

# Initialize indexer eagerly at module load
try:
    _indexer = HandoutsIndexer()
except Exception as e:
    _indexer = None

def get_indexer():
    global _indexer
    if _indexer is None:
        _indexer = HandoutsIndexer()
    return _indexer

class HandoutsQuery(BaseModel):
    question: str

class SearchResult(BaseModel):
    filename: str
    preview: str
    score: int

@router.get("/handouts/search")
async def search_handouts(q: str):
    """Search handouts by keyword"""
    indexer = get_indexer()
    results = indexer.search(q, limit=5)
    return {"results": results, "query": q}

@router.post("/handouts/ask")
async def ask_handouts(query: HandoutsQuery):
    """Ask a question and get answer from Qwen with handout references"""

    indexer = get_indexer()

    # First, search for relevant handouts
    search_results = indexer.search(query.question, limit=3)

    # Build context from top results
    context = "Relevant handout excerpts:\n\n"
    if search_results:
        for result in search_results:
            context += f"From '{result['filename']}':\n{result['preview']}\n\n"
    else:
        context += "No handout excerpts found for your question.\n"

    # Send to Qwen with context
    prompt = f"""Based on these handout excerpts, answer the user's question:

{context}

User Question: {query.question}

Answer the question clearly, citing which handout each piece of information came from. If no excerpts were provided, say you can't find information on this topic in the handouts."""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:1234/v1/chat/completions",
                json={
                    "model": "qwen",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=60.0
            )

            if response.status_code != 200:
                raise Exception(f"Qwen error: {response.text}")

            result = response.json()
            answer = result['choices'][0]['message']['content']

    except Exception as e:
        answer = f"Error getting response from Qwen: {str(e)}"

    return {
        "question": query.question,
        "answer": answer,
        "sources": [
            {
                "filename": r["filename"],
                "path": r["relative_path"],
                "relevance": r["score"]
            } for r in search_results
        ]
    }

@router.get("/handouts/reload")
async def reload_handouts():
    """Force reload the handouts index"""
    global _indexer
    _indexer = None  # Clear the cache
    indexer = get_indexer()  # Reinitialize
    return {
        "status": "reloaded",
        "document_count": len(indexer.index.get("documents", []))
    }


@router.get("/handouts/list")
async def list_handouts():
    """List all indexed handouts"""
    indexer = get_indexer()
    docs = indexer.index.get("documents", [])
    return {
        "count": len(docs),
        "documents": [
            {
                "filename": d["filename"],
                "relative_path": d["relative_path"],
                "word_count": d["word_count"]
            } for d in docs
        ]
    }

