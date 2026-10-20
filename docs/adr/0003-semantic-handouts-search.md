# ADR-0003: Semantic handouts search with local embeddings

**Status:** Accepted. **Date:** 2026-10-20. **Trigger:** keyword search missed natural questions such as "what class is life essences introduced".

## Context

About 100 handout PDFs and DOCs. Questions rarely use the documents' exact words. Keyword search returned nothing or unrelated documents for concept questions.

## Decision

Chunk handout text (~500 characters), embed each chunk with `sentence-transformers/all-MiniLM-L6-v2`, and rank by cosine similarity plus a small keyword bonus. Send the best-matching chunks, not a document preview, to Qwen for answers.

## Consequences

- A 154 MB index file (`backend/handouts_index.json`) that cannot go in git; it is rebuilt locally.
- The model downloads (~200 MB) on first run, and the index loads at startup.
- `requirements.txt` carries the ML stack; tests use `requirements-test.txt` to avoid it.

## Alternatives rejected

- Keyword search only: failed the questions people actually ask.
- A larger embedding model: unnecessary for 100 documents and slower.
- A hosted embedding API: handout content would leave the machine.
