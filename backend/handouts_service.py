import os
import json
from pathlib import Path
from pypdf import PdfReader
from docx import Document as DocxDocument
import re
import numpy as np
from sentence_transformers import SentenceTransformer

HANDOUTS_FOLDER = "/Users/djw/Documents/Handouts-in-English"
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BACKEND_DIR, "handouts_index.json")

# Load embedding model once (lazy-loaded)
_embedding_model = None

def get_embedding_model():
    """Get or load the embedding model"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model

class HandoutsIndexer:
    def __init__(self):
        self.index = self._load_index()

    def _load_index(self):
        """Load existing index or create new one"""
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, 'r') as f:
                return json.load(f)
        return {"documents": [], "last_updated": None}

    def _save_index(self):
        """Save index to file"""
        with open(INDEX_FILE, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _extract_pdf_text(self, filepath):
        """Extract text from PDF"""
        try:
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF {filepath}: {e}")
            return ""

    def _extract_docx_text(self, filepath):
        """Extract text from DOCX"""
        try:
            doc = DocxDocument(filepath)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            print(f"Error reading DOCX {filepath}: {e}")
            return ""

    def _extract_text(self, filepath):
        """Extract text from PDF or DOCX"""
        if filepath.endswith('.pdf'):
            return self._extract_pdf_text(filepath)
        elif filepath.endswith('.docx') or filepath.endswith('.doc'):
            return self._extract_docx_text(filepath)
        return ""

    def _chunk_text(self, text, chunk_size=500):
        """Split text into chunks for better search"""
        chunks = []
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def index_handouts(self):
        """Index all handouts in the folder"""
        documents = []
        model = get_embedding_model()

        # Walk through all files
        for root, dirs, files in os.walk(HANDOUTS_FOLDER):
            for file in files:
                if file.endswith(('.pdf', '.docx', '.doc')):
                    filepath = os.path.join(root, file)
                    relative_path = os.path.relpath(filepath, HANDOUTS_FOLDER)

                    print(f"Indexing: {relative_path}")

                    # Extract text
                    text = self._extract_text(filepath)

                    if text:
                        # Chunk text
                        chunks = self._chunk_text(text)

                        # Generate embeddings for chunks
                        chunk_embeddings = []
                        for chunk in chunks:
                            try:
                                embedding = model.encode(chunk, convert_to_numpy=True)
                                chunk_embeddings.append(embedding.tolist())
                            except Exception as e:
                                print(f"Error encoding chunk: {e}")
                                chunk_embeddings.append(None)

                        # Create document entry
                        doc = {
                            "filename": file,
                            "relative_path": relative_path,
                            "absolute_path": filepath,
                            "full_text": text[:5000],  # Store first 5000 chars for preview
                            "chunks": chunks,
                            "chunk_embeddings": chunk_embeddings,
                            "word_count": len(text.split())
                        }

                        documents.append(doc)

        self.index["documents"] = documents
        self.index["last_updated"] = str(Path(HANDOUTS_FOLDER).stat().st_mtime)
        self._save_index()

        print(f"\n✓ Indexed {len(documents)} documents with embeddings")
        return len(documents)

    def search(self, query, limit=5):
        """Search for relevant handouts using semantic similarity"""
        model = get_embedding_model()

        # Encode query
        try:
            query_embedding = model.encode(query, convert_to_numpy=True)
        except Exception as e:
            print(f"Error encoding query: {e}")
            return []

        results = []

        for doc in self.index["documents"]:
            best_chunk_score = 0
            best_chunk_text = None

            # Find best matching chunk using semantic similarity
            for i, chunk in enumerate(doc.get("chunks", [])):
                embedding = doc.get("chunk_embeddings", [])[i] if i < len(doc.get("chunk_embeddings", [])) else None

                if embedding is None:
                    continue

                # Calculate cosine similarity
                chunk_embedding = np.array(embedding)
                similarity = float(np.dot(query_embedding, chunk_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)))

                # Scale to 0-100
                score = int((similarity + 1) / 2 * 100)

                if score > best_chunk_score:
                    best_chunk_score = score
                    best_chunk_text = chunk

            # Add keyword matching bonus (for exact matches)
            query_lower = query.lower()
            if query_lower in doc["filename"].lower():
                best_chunk_score += 20
            if query_lower in doc["full_text"].lower():
                best_chunk_score += 10

            if best_chunk_score > 20:  # Threshold for relevance
                results.append({
                    "filename": doc["filename"],
                    "relative_path": doc["relative_path"],
                    "score": best_chunk_score,
                    "word_count": doc["word_count"],
                    "preview": doc["full_text"][:500]
                })

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

if __name__ == "__main__":
    indexer = HandoutsIndexer()
    indexer.index_handouts()

