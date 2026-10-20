# ADR-0004: Local Qwen via LM Studio for AI features

**Status:** Accepted. **Date:** 2026-10-05. **Trigger:** adding chat, task generation and handout Q&A without sending student or class data to a cloud service.

## Context

The AI features see student names, class content and admin notes. The machine has 64 GB of RAM, enough to run a mid-size model locally.

## Decision

Call Qwen through LM Studio's OpenAI-compatible server at `localhost:1234/v1`. Every page that uses it handles LM Studio being down.

## Consequences

- Answer quality is capped by what runs locally; complex coding work goes to a hosted coding agent, not the in-app model.
- LM Studio must be running, with a model loaded at a large enough context length.
- No per-call cost and it works offline.

## Alternatives rejected

- A hosted model API for in-app features: student data would leave the machine.
