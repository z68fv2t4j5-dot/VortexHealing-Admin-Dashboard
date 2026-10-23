---
name: handouts-knowledge-base
description: Handouts search is a catalogue plus hybrid FTS5/embedding index kept outside the repo; design in ADR-0008
metadata:
  type: project
---

**Fact:** `backend/handouts/` keeps one current file per handout, indexes it into `kb.sqlite` in `HANDOUTS_KB_DIR` (outside the repo), and searches by keywords plus nomic embeddings. Stories 2-4 (answers, knowledge map, teacher notes) follow the plan.

**Why:** v1 read no `.doc` files and mixed retired versions with current ones.

**Authority:** ADR-0008
