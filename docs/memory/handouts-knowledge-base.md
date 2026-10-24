---
name: handouts-knowledge-base
description: Handouts search is a catalogue plus hybrid FTS5/embedding index outside the repo, with streamed, cited Qwen answers; design in ADR-0008
metadata:
  type: project
---

**Fact:** `backend/handouts/` indexes one current file per handout into `kb.sqlite` in `HANDOUTS_KB_DIR` (outside the repo) and searches by keywords plus nomic embeddings; `answer.py` streams cited Qwen answers (helpers with thinking off, the answer with low). Stories 3-4 (knowledge map, teacher notes) follow the plan.

**Why:** v1 read no `.doc` files, and answers took a minute.

**Authority:** ADR-0008
