---
name: handouts-knowledge-base
description: Handouts search is semantic (local embeddings, chunk-level); design and limits live in ADR-0003 and the architecture map
metadata:
  type: project
---

**Fact:** Handouts search ranks ~500-character chunks by embedding similarity plus a keyword bonus, and passes matching chunks to Qwen. The 154 MB index is local only.

**Why:** Keyword search missed concept questions like "what class is life essences introduced".

**Authority:** ADR-0003
