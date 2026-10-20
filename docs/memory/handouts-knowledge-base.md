---
name: handouts-knowledge-base
description: Semantic search implementation for 100 handout documents using embeddings
type: decision
---

# Handouts Knowledge Base - Semantic Search Implementation

**Completed**: October 20, 2026  
**Status**: Production Ready

## Fact: Semantic Search with Embeddings Implemented

The Handouts Knowledge Base now uses embedding-based semantic search instead of keyword-only matching. This allows users to find documents by concept, not just exact phrases.

**Example**: Query "what class is life essences introduced" now finds MF-Review-24.pdf as #1 result (Multi-Frequency class), whereas keyword-only search would return unrelated results.

## Why: Better Search Quality

Users ask natural language questions that don't match document structure. Semantic search finds conceptually related content even when exact keywords don't match. This is essential for:
- "When is X taught?" → Finding class review documents
- "How do I use Y?" → Finding practice guides  
- "What is Z?" → Finding foundational materials

## How to Apply: Implementation Details

### Architecture
```
100 PDFs/DOCs → Extract text → Chunk (500 chars) → Generate embeddings
                                                          ↓
                                            handouts_index.json (154MB)
                                                          ↓
                                          Semantic search + keyword bonus
```

### Model Choice
- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Why**: 100 docs doesn't need large model; MiniLM is 200MB, fast (~100ms search)
- **Embeddings**: 384-dimensional vectors per chunk

### Scoring Algorithm
```
score = semantic_similarity (0-100) + keyword_bonus
- Semantic similarity: cosine of query vs chunk embedding
- Keyword bonus: +20 if in filename, +10 if in full text
```

### Known Limitation
Currently returns preview (first 5000 chars) to Qwen, not the matching chunk. Qwen can't see why the semantic search selected that document, reducing answer quality.

## Impact: What Changes

| Before | After |
|--------|-------|
| "kundalini" → 5 results, need keyword match | "kundalini" → Kundalini-Review-7.pdf #1 |
| "life essences" → 2 QGate results only | "life essences" → MF-Review-24.pdf #1 |
| "what class is X?" → 0 results | "what class is X?" → 3 conceptual matches |

## Next Work

**Enhancement**: Return matching chunk text (not preview) to Qwen
- Allows Qwen to see actual matched content
- Better citations and answer accuracy
- Estimated effort: 1 file edit (handouts.py)

---

**Related**: docs/ARCHITECTURE.md (Handouts Knowledge Base Architecture section)  
**Files**: backend/handouts_service.py, backend/app/api/handouts.py
