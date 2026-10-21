# Architecture decision register

Decisions that constrain future work, one file each: `docs/adr/NNNN-kebab-title.md`, numbered from 0001, written from `0000-template.md`: Status, Context, Decision, Consequences, Alternatives rejected. The Consequences section names the costs; an ADR that lists no cost has not finished thinking.

Every file has exactly one row here and ids are sequential (`adr-register`). `AGENTS.md` Part A cites no ADR numbers (`adr-refs`), so a clone that renumbers cannot point at the wrong decision. Memory pages cite a decision as `ADR-NNNN` in their Authority line. Superseded decisions keep their file and change their Status.

| ID | Title | Status | Date |
|---|---|---|---|
| 0001 | Adopt the agentic development harness | Accepted | 2026-10-20 |
| 0002 | SQLite and local-only student data | Accepted | 2026-10-05 |
| 0003 | Semantic handouts search with local embeddings | Accepted | 2026-10-20 |
| 0004 | Local Qwen via LM Studio for AI features | Accepted | 2026-10-05 |
| 0005 | Raw agent transcripts stay local | Accepted | 2026-10-21 |
| 0006 | Full-word class tags are the record of completed classes | Accepted | 2026-10-21 |
