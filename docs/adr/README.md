# Architecture Decision Records (ADR)

This directory contains architectural decisions made during development.

## Current Decisions

### ADR-001: SQLite for Local Development
**Decision**: Use SQLite instead of PostgreSQL for local development.
**Reason**: Simplifies setup (no Docker/server required), student data stays local.
**Date**: October 2026

### ADR-002: Semantic Search with Embeddings
**Decision**: Implement embedding-based search using sentence-transformers.
**Reason**: Better conceptual matching than keyword-only search; finds related docs even with different phrasing.
**Date**: October 2026

### ADR-003: Local Qwen via LM Studio
**Decision**: Use Qwen 3.8 running locally on localhost:1234/v1.
**Reason**: Privacy (no cloud), control, no API costs, works offline.
**Date**: October 2026

