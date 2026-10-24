# Plan (feature): handouts knowledge base (v2 of Handouts)
Status: story 1 done 2026-10-23; story 2 done 2026-10-23; story 3 done 2026-10-24 (story 4 open).

Departures in story 3, as built (Daniel chose the knowledge map before teacher notes):
- Extraction runs with thinking off and a non-strict JSON schema plus an example of the shape: with the schema enforced strictly, Qwen returned empty lists in 10 tokens; without an example it mostly did too. At most 15 entities and 20 facts per section, `max_tokens` 6000: longer replies were cut off mid-JSON.
- Readings are cached by section text hash (`extraction_cache`), so `ingest --full` never repeats the run; entities and facts are rebuilt from the cache by `apply-knowledge` in seconds.
- Predicates: `done_in_class` (with the how in `detail`) was added for comparisons between classes; `used_for` dropped in favour of `releases`.
- Class names resolve against the flowchart and `HANDOUTS_KB_DIR/handout_classes.yaml` (handout family -> class, drafted by Claude for Daniel to correct); only those are typed as classes.
- Answers that name an entity get its card, up to 4 passages behind its key facts, and a cited "Knowledge map" list. Cards also appear in search mode; the page gained a Browse tab and a Build button. A CLI run writes a heartbeat so the page does not start a second one.
- Full run 2026-10-24: 1,370 sections at 4 at a time, about 3.5 hours; 4 sections still fail (cut-off replies) and are retried by every run. Result 6,331 entries and 13,551 facts.

Departures in story 2, as built (Daniel asked for better answers without the extra wait):
- Measured first: the backend named the model `qwen3.8-27b`, so LM Studio loaded a second copy (other format, 8,192 context); with the identifier `qwen/qwen3.8-27b` the same answer took 17 s instead of 64 s and was correct instead of hedged.
- Helper calls (follow-up rewrite, multi-part split) run with thinking off, only when needed: rewrite only with history, split only for questions of 8+ words with "and", a comma or two question marks. The answer keeps low thinking: with thinking off it again answered "the handouts don't cover this" for LifeEssences and the genetic-modification question.
- 8 sources (10 for multi-part) instead of 12, and a 250-word guide, after measuring 12 sources and unbounded answers at 65 s for a multi-part question; now about 45 s, with passages shown within about 1 s and the answer streamed.
- The prompt names the abbreviations from Daniel's glossary (thinking-off had expanded LF as "Low Frequency") and explains that "<Class> Review" handouts mean that class by "this class".
- The citation check counts paragraphs and bullets of 8+ words, not sentences: Qwen cites per paragraph.
- Fixed during story 2 from Daniel's marks: tab-indented list items are never headings (they had split the MG ending options into fragments).
- `eval --answers` writes a marking sheet to `HANDOUTS_KB_DIR/eval/`; answers are judged by Daniel, not automatically. Set up in a Claude Code session with Daniel; planned for the local agent (Qwen), one story per session and per pull request, in the order below.

Departures in story 1, as built:
- Built by Claude, not Qwen. In Continue, Qwen 3.8 27B ran out of reply tokens while deliberating, wrote files into the wrong workspace, and its `sections.py` crashed on import and ignored the heading rules. Daniel chose to have Claude finish story 1; Qwen remains the in-app answering model.
- Settings are fields on the existing pydantic `Settings` (`backend/app/core/config.py`), not a hand-written `.env` reader: that class rejects unknown `.env` keys, so adding the keys alone broke the backend.
- `/api/handouts/ask` and Ask mode on `/api/handouts/query` already answer through Qwen with `[n]` citations and the grounded prompt, so the page loses no feature; story 2 adds sub-query planning, follow-up rewriting and stricter citation checks. Follow-ups currently prepend the previous question to the search.
- A retired or skipped file keeps a `documents` row without its text (not its old chunks); "what changed between versions" would need the text kept.
- Added during the build: identical-text de-duplication (the Avebury Dragon handout exists under two names), dropping table-of-contents lines, PDF-wrap detection for headings, folding sections under 15 words into the next.
- `/api/handouts/list` and `/api/handouts/reload` were removed with v1; the page uses `/status` and `/rescan`.
- Eval baseline: 21/21 questions found an expected handout in the top 5 (`eval_runs`, 2026-10-23).

## Why

Daniel wants one box on the Handouts page that takes either a search ("Merlin's Jewel structures") or an open question ("where does fear of abandonment come from, and which tools release it?"), and answers comprehensively from the English handouts: tools and their use, the sources of conditioning (physical, emotional, mental, karmic, genetic/ancestral, Core Veil and so on), which class teaches what, and the protocols. The knowledge base must grow on its own when handouts are added or revised, and must take Daniel's own notes and corrections.

## Decisions taken with Daniel (2026-10-21), not to be re-asked

| Question | Answer |
|---|---|
| Audience | Daniel only. Local, inside this dashboard. Nothing leaves the Mac. |
| Answer style | Grounded synthesis. May combine several handouts. Every claim cites handout + section. Anything inferred (not stated) is labelled "Inference". Says plainly when the handouts do not cover something. No general-knowledge filler. |
| Learning | (a) Auto-ingest new and changed files; superseded versions retire. (b) Daniel's notes and corrections are a trusted source layer, cited as "Teacher note", and win over handouts when they conflict. Not wanted now: thumbs-up/down tuning, audio transcription. |
| Versions | Latest version number only. `OLD/` and `old/` folders and `Redline` files are excluded. `-Edit` files do NOT replace the plain file; the highest version number wins regardless of `-Edit` (so `MI-Review-20-Edit` beats `MI-Review-19` and `MI-Review-19-Edit`). |
| Abbreviations | Kept in an editable glossary file (below). MI = Manifesting Intention, MJ = Magical Jewel, LF = LifeForm, DM = Divine Magic. |
| Foundational manual | The 2026 manual (`2026-Foundational-Manual-(Oct 1)-Letter.pdf`) is current; the two 2022 manuals retire. |
| EarthWorks I5 | `EarthWorksI5-Review-2-A` is current over `-2` (Daniel, 2026-10-23); the version rule already orders a letter revision after its number. |

## Observed (2026-10-21)

- Source: `~/Documents/Handouts-in-English`, 193 files: 88 `.doc`, 7 `.docx`, 93 `.pdf`, 3 `.m4a`, 1 `.zip`. Most handouts exist as a `.doc` and a `.pdf` of the same version.
- v1 (`backend/handouts_service.py`) indexed 100 files, all PDFs: `python-docx` cannot read `.doc`, so every `.doc` failed silently. Files that exist only as `.doc` (for example `Flowchart-for-Classes-55`, `Foundational-Responsibility-Agreement-Students-11`, `EarthWorksI5-Review-2`) are missing from search.
- v1 indexes `OLD/` versions and several versions of one handout side by side (`CoreVeil-I-Tree-8` and `-9`, `Class-Descriptions-all-65` and `-66`, `QGate-History-12` and `-13`), so answers can quote retired text.
- v1 keeps only the single best chunk per document, sends 3 chunks to Qwen, splits on every `.` (breaks "approx." and numbered lists), ignores headings, and stores a 154 MB JSON index. The source path is hard-coded (breaks AGENTS.md section 5).
- `textutil -convert txt` (built into macOS) reads every `.doc`/`.docx` here cleanly. Current-version `.doc` text totals about 513,000 words.
- The handouts are well structured: dated titles, headings ("Part II: The Backstory", "Day 1: ..."), tool overviews of the form "Tool name—enables you to ...", numbered conditioning sources (`Foundational-Sources-of-Conditioning-Chart-2`: Core Veil & aspects, Incarnational Personality/karmic, Ancestral History in DNA, Present Life Experiences, Human Energy System & Consciousness, Higher Dimensional Blueprints).
- Abbreviations defined in the text: MF (Multi-Frequency), CV (Core Veil), UAP (Universal Assemblage Point), MG (Merlin's Grace), LCF (Localized Consciousness of the Form). Never defined but heavily used: MI (772 uses), MJ (366, ambiguous: Merlin's Jewel or Magical Jewel), LF (87), DM (110).
- `2026-Foundational-Manual-Extras.zip` holds mantra MP3s, photos and older copies of Foundational PDFs that are already in the folder.
- LM Studio serves `qwen/qwen3.8-27b`, `qwen/qwen3.5-9b` and `text-embedding-nomic-embed-text-v1.5` at `localhost:1234/v1`. The Mac has 64 GB RAM (M5 Max).

## Assumed (check during story 1)

- Every current handout's newest version is a `.doc`/`.docx` or a `.pdf`; where both exist at the same version their text is the same, so the `.doc` (cleaner text) is used.
- A heading is a short line (under ~80 characters) with no full stop at the end, or a numbered/lettered/`Day N:`/`Part N:` line. Story 1 measures this on 5 handouts before relying on it.

## Hard rules for whoever implements this

1. **The repository is public. Handout text is confidential teaching material.** No handout text, extracted fact, glossary definition, eval question or index file is ever committed. Tests use invented fixture text. Everything derived from the handouts lives in the knowledge-base data folder outside the repository.
2. Paths come from settings, never literals: `HANDOUTS_DIR` (source, required) and `HANDOUTS_KB_DIR` (data folder, default `~/Documents/Handouts-KB`). They are fields on the existing pydantic `Settings` in `backend/app/core/config.py` (already added), which reads `backend/.env`; that class forbids unknown keys, so every new `.env` key needs a field there first. Read them via `from app.core.config import settings`. Add both to `backend/.env.example` with placeholders.
3. Every page and endpoint works with LM Studio down. Search falls back to keyword search; Ask says clearly that the model is not running.
4. Load Qwen in LM Studio at 16384+ context (AGENTS.md trap 4).

## Acceptance criteria (whole feature)

1. `python -m handouts ingest --dry-run` prints a catalogue: every source file marked KEEP, RETIRED (with the file that supersedes it) or SKIPPED (with the reason). Daniel reviews it once; `catalog_overrides.yaml` in the data folder can force KEEP/SKIP for any file.
2. Every KEEP handout has its text indexed, including `.doc`-only files. `GET /api/handouts/status` reports counts of documents, sections, chunks, entities and notes, plus the last scan time.
3. A plain search returns passages ranked by keyword + meaning, each showing handout title, section heading and version, with abbreviations expanded (searching "MF" finds "Multi-Frequency").
4. An open question returns an answer in which every sentence carrying a claim has a citation `[n]`, each `[n]` resolves to a passage shown under the answer, inferences are marked "Inference:", and an uncovered topic gets "The handouts don't cover this" rather than invented content.
5. Asking about a named tool, class or conditioning source also shows its knowledge card: what it is, which class introduces it, what it is used for or released by, related items, all with citations.
6. Copying a revised handout (higher version number) into the source folder and pressing Rescan (or restarting the backend) re-indexes only the changed files, retires the old version, and the next answer cites the new one.
7. Daniel can add a note or correct an answer from the page; the note is saved as a Markdown file in the data folder, is cited as "Teacher note (date)", and overrides a conflicting handout statement in later answers.
8. The local eval (`python -m handouts eval`) answers Daniel's question list and reports, per question, whether the expected handout appears in the top 5 passages. Baseline target: at least 18 of 20.

## Design

### Data folder (`HANDOUTS_KB_DIR`, outside the repo)

```
Handouts-KB/
  kb.sqlite               # everything derived; rebuildable from source + notes
  glossary.yaml           # abbreviations and synonyms; Daniel edits it
  catalog_overrides.yaml  # optional KEEP/SKIP by filename
  notes/                  # teacher notes, one Markdown file each
  eval/questions.yaml     # Daniel's test questions + expected handout
```

`glossary.yaml` seed (all confirmed by Daniel, 2026-10-21):

```yaml
MF: [Multi-Frequency]
CV: [Core Veil]
UAP: [Universal Assemblage Point]
MG: [Merlin's Grace]
LCF: [Localized Consciousness of the Form]
MI: [Manifesting Intention]
MJ: [Magical Jewel]       # NOT Merlin's Jewel, which is a separate tool (MF class); never alias the two
LF: [LifeForm]
DM: [Divine Magic]
```

The ingest also harvests `Long Name (ABBR)` and `ABBR (Long Name)` patterns from the text into a `glossary_auto` table; `glossary.yaml` wins on conflict.

### Code layout

Replace `backend/handouts_service.py` with a small package `backend/handouts/`. One module per job, each justified:

| Module | Job |
|---|---|
| `catalog.py` | Walk `HANDOUTS_DIR`, group files into families, choose the latest version, apply overrides. Pure function over a list of paths: easy to unit-test. |
| `extract.py` | `.doc`/`.docx` via `textutil -convert txt -stdout` (subprocess, exit code asserted); `.pdf` via `pypdf` (already a dependency). Returns text. |
| `sections.py` | Text -> title, date (first date-like line), sections (heading path), chunks of ~250-400 words that never cross a section boundary and overlap by one sentence. Sentence split must not break on "e.g.", "approx.", "~", or numbered items. |
| `store.py` | SQLite (stdlib `sqlite3`) schema, FTS5 keyword index, embedding blobs (float32 via `numpy`), CRUD. |
| `embed.py` | Calls LM Studio `POST /v1/embeddings` with `text-embedding-nomic-embed-text-v1.5`. Nomic needs prefixes: `search_document: ` for chunks, `search_query: ` for queries. Batch 32. |
| `ingest.py` | Orchestrates a scan: catalogue -> extract -> sections -> store -> embed; dry run, incremental by sha256, retiring superseded versions. Kept apart from `__main__.py` so the API's Rescan and startup scan call the same function as the CLI. |
| `retrieve.py` | Hybrid retrieval: glossary expansion -> FTS5 BM25 top 40 + vector top 40 -> reciprocal rank fusion (k=60) -> teacher-note boost -> at most 3 chunks per document in the final top N. |
| `knowledge.py` | Story 3: the per-section Qwen extraction of entities and facts, merging, cards. |
| `answer.py` | Story 2: sub-query planning, context assembly, the grounded prompt, citation validation. |
| `notes.py` | Story 4: read/write `notes/*.md`, ingest them as a source. |
| `__main__.py` | CLI: `ingest [--dry-run] [--full]`, `extract-knowledge [--limit N]`, `eval`, `status`. |

Dependencies: none added. `sentence-transformers` (and the torch it pulls) and `python-docx` come out of `requirements.txt`, because embeddings move to LM Studio and `.doc`/`.docx` move to `textutil`. If LM Studio is down at ingest time, chunks are stored without embeddings and `ingest` fills them in on the next run; search uses FTS5 alone until then.

### Catalogue rules (`catalog.py`)

- Skip: any path with a directory named `OLD` or `old`; names containing `Redline`; names starting `~$`; `.DS_Store`; `.zip`; audio (`.m4a`, `.mp3`) for now.
- Family key: filename stem, lower-cased. First strip these format/edit suffixes from the end, repeatedly: `-edit`, `-letter`, `-for-pdf`. Then split off the trailing version (`-24` or `24` -> `(24,)`; `-1K` -> `(1,'k')`; `-2-A` -> `(2,'a')`). What remains is the family. `-short`, `-condensed`, `-complete`, `-one-page` and `-big` are part of the name: they mark different documents, not versions.
- Latest: highest version tuple wins. On a tie, prefer the file without `-letter`/`-for-pdf`, then `.doc`/`.docx` over `.pdf`. PDF-only handouts (the Foundational manuals, `MI-Jin-Shin-Nodes`) are kept as PDFs.
- Foundational manuals: keep `2026-Foundational-Manual-(Oct 1)-Letter.pdf`; `Foundational-Manual-2022-Feb-26.pdf` and `Foundational-Training-Manual-2022-Nov.pdf` are RETIRED (Daniel, 2026-10-21). Write these into the seed `catalog_overrides.yaml`. Any other dated family the dry run cannot order goes under "NEEDS DECISION" for Daniel; do not guess.
- The same handout in two folders (`Foundational-Angel-Symbol-and-Info-1` in `AngelicHeart/` and `Foundational/`) is one family; keep one, retire the other.

### Storage schema (`store.py`)

```
documents(id, family, path, title, doc_date, version, sha256, mtime, status KEEP|RETIRED, superseded_by, source_kind handout|note, indexed_at)
sections(id, document_id, heading_path, ord, sha256)
chunks(id, section_id, ord, text, embedding BLOB NULL)
chunks_fts  -- FTS5 over chunks.text + sections.heading_path + documents.title, tokenize 'porter unicode61'
glossary_auto(abbr, expansion, document_id)
entities(id, name, type, definition, aliases_json)          -- story 3
facts(id, subject_id, predicate, object_id NULL, object_text NULL, chunk_id, extracted_with)  -- story 3
section_extraction(section_id, sha256, model, done_at)      -- story 3 resume marker
eval_runs(id, ran_at, hits, total)                          -- story 1
```

Identical text under two names (observed: the Avebury Dragon handout in `EarthWorks/` and `Foundational/`): after extraction, a KEEP file whose normalised text hash equals an already-indexed document's is recorded as SKIPPED "identical text to <path>" and not indexed twice.

Incremental ingest: compare each KEEP file's sha256 with `documents.sha256`. Unchanged: skip. Changed or new: delete its sections, chunks and facts, then re-insert. Newly superseded: mark RETIRED and exclude from retrieval (rows kept for "what changed" later). Knowledge extraction re-runs only for sections whose sha256 changed.

### Knowledge layer (story 3)

For each section (current, not yet extracted at this sha256), call Qwen (`qwen/qwen3.8-27b`, temperature 0, JSON-schema response format via LM Studio `response_format`) with the section text plus its document title and heading path, asking for:

```json
{"entities":[{"name":"","type":"tool|transmission|class|conditioning|structure|protocol|being|place|concept","aliases":[],"definition":"<= 2 sentences, from this text only"}],
 "facts":[{"subject":"","predicate":"introduced_in|used_for|releases|is_source_of|is_part_of|requires|prerequisite_of|located_in|related_to","object":"","conditioning_level":"physical|emotional|mental|karmic|genetic_ancestral|core_veil|energetic|blueprint|present_life|null"}]}
```

- Seed the conditioning taxonomy from `Foundational-Sources-of-Conditioning-Chart-2` plus Daniel's levels (physical, emotional, mental, karmic, genetic). Store the seed in `glossary.yaml` under `conditioning_levels:` so Daniel can extend it.
- Merge entities on a normalised name (lower case, no punctuation, glossary aliases folded). Keep every definition with its chunk; the card shows the one from the class that introduces the entity.
- Every fact keeps its `chunk_id`; a fact without evidence is dropped.
- `introduced_in` is cross-checked against the document's class: a fact from `MF-Review-24` saying a tool is received "in this class" resolves to MF.
- Runs as `python -m handouts extract-knowledge`, resumable, prints progress and an ETA. Expect hours on the first full run (overnight); afterwards only changed sections. `--limit 20` for testing.

Entity cards: `GET /api/handouts/entity/{id}` returns name, type, definitions, class introduced, facts grouped by predicate, each with its citation. Cards appear beside search and ask results when the query names an entity (alias match on the expanded query).

### Ask flow (story 2, extended in 3 and 4)

0. Follow-ups: the page sends the last 3 question/answer pairs with the request (held in page state only, not stored). When there is history, one Qwen call (temperature 0) rewrites the question into a standalone one ("how does that differ from external karma?" after "what is a karma knot" -> "how does a karma knot differ from external karma?"). The rewritten question is shown above the answer so Daniel can see what was searched. Retrieval always uses the rewritten question.
1. Expand the question with the glossary.
2. Plan: one Qwen call (temperature 0) returns up to 3 sub-queries as JSON (for "where does X come from and what releases it": "source of X", "conditioning level of X", "tools that release X"). Skip planning for questions under 6 words.
3. Retrieve for the question and each sub-query; fuse; take the top 12 chunks within a 9,000-token budget. Add matching entity facts (story 3) and relevant teacher notes (story 4) to the context, numbered like the passages.
4. Answer: one Qwen call (temperature 0.2). System prompt, verbatim intent: answer only from the numbered sources; cite `[n]` after each claim; when you combine sources into a conclusion they do not state, start that sentence with "Inference:"; teacher notes override handouts when they conflict; if the sources do not answer, say "The handouts don't cover this" and list the closest passages; give the answer in plain prose with short headings when it has parts (what it is / where it comes from / which tools / which class).
5. Validate: strip any `[n]` that is not a provided source; if fewer than half the claim sentences keep a citation, return the passages with a note instead of the answer.

One endpoint: `POST /api/handouts/query {q, mode: "auto"|"search"|"ask", history?: [{q, answer}]}`. `auto`: if `q` ends with `?` or starts with a question word, or has 6+ words, run ask; otherwise search. The response always includes `passages` and `cards`, and includes `answer` when it asked. Keep `GET /api/handouts/search` and `POST /api/handouts/ask` as thin wrappers until the page no longer calls them, then remove them in story 4.

### Teacher notes (story 4)

- File `notes/<yyyy-mm-dd>-<slug>.md`, front matter `topic`, `entities` (optional names), `corrects` (optional handout family + section). Body is Daniel's text. The first note already exists (`notes/2026-10-21-external-karma.md`, a term Daniel uses that no handout does); story 4 must ingest it unchanged, and eval question 3 depends on it.
- Ingested as `source_kind=note`, always eligible for retrieval, boosted in fusion, cited "Teacher note (date)".
- The page gets "Add note" on every answer and every card, prefilled with the question and the cited sources; saving writes the file and re-ingests that note only.
- `GET /api/handouts/notes` lists notes; editing a note file by hand is picked up by the next scan.

### Auto-ingest

- Backend startup runs an incremental scan in a background thread; the page shows "Scanning..." from `status`.
- A Rescan button calls `POST /api/handouts/rescan`. No file-watcher dependency: startup + button is enough for one user.
- The scan never runs knowledge extraction itself (too slow); `status` shows "N sections waiting for knowledge extraction" and the page offers a button that starts it in the background.

### Page (`frontend/src/pages/Handouts.tsx`)

One input with a Search/Ask/Auto toggle (default Auto). Results: answer (with clickable `[n]` jumping to the passage), cards, passages (title, section, version, highlight). Each passage opens the source file through `GET /api/handouts/file/{document_id}` (serves the PDF if one exists at that version, otherwise the `.doc`). A side panel shows status and Rescan. Story 3 adds a Browse tab: Tools, Classes, Conditioning, each a filterable list opening cards.

## Stories (one session and one pull request each, in order)

| # | Story | Surface | Done when |
|---|---|---|---|
| 1 | Catalogue, extraction, sections, SQLite + FTS5 + embeddings, hybrid search, status, rescan, file serving, eval CLI; page search mode | `backend/handouts/{__init__,__main__,catalog,extract,sections,store,embed,ingest,retrieve}.py`, `backend/app/api/handouts.py`, `backend/app/core/config.py` (the two `HANDOUTS_*` settings), `backend/main.py` (startup scan only), `backend/requirements.txt`, `backend/requirements-test.txt`, `backend/tests/test_handouts_api.py`, `backend/tests/test_handouts_{catalog,sections,retrieve,ingest}.py`, `frontend/src/pages/Handouts.tsx`, `.env.example`, `.gitignore`, `docs/ARCHITECTURE.md`, `docs/adr/0008-handouts-knowledge-base.md`, `docs/adr/0003-semantic-handouts-search.md` (status only), `docs/adr/README.md`, `docs/memory/handouts-knowledge-base.md`; delete `backend/handouts_service.py` | Criteria 1, 2, 3, 6; Daniel approved the dry-run catalogue; eval baseline recorded (counts only) |
| 2 | Ask: planning, context, grounded prompt, citation validation; page answer view | `backend/handouts/answer.py`, `backend/app/api/handouts.py`, `backend/tests/test_handouts_answer.py`, `frontend/src/pages/Handouts.tsx`, `docs/ARCHITECTURE.md` | Criterion 4; LM-Studio-down path tested |
| 3 | Knowledge extraction, entities, facts, cards, Browse tab | `backend/handouts/knowledge.py`, `backend/handouts/store.py`, `backend/handouts/answer.py`, `backend/app/api/handouts.py`, `backend/tests/test_handouts_knowledge.py`, `frontend/src/pages/Handouts.tsx`, `docs/ARCHITECTURE.md` | Criterion 5 on Daniel's eval questions about tools and conditioning |
| 4 | Teacher notes and corrections; remove old endpoints | `backend/handouts/notes.py`, `backend/handouts/retrieve.py`, `backend/handouts/answer.py`, `backend/app/api/handouts.py`, `backend/tests/test_handouts_notes.py`, `frontend/src/pages/Handouts.tsx`, `docs/ARCHITECTURE.md` | Criterion 7; criterion 8 re-run and not lower than the story-1 baseline |

Each story still runs `harness-plan` for its own slice (it can copy from here), `harness-close` at the end, and needs the `Surface:`, `Tests:` and `Review:` trailers.

## Test plan

- Unit, with invented fixture filenames and text only (hard rule 1):
  - `catalog`: OLD/old skipped; Redline skipped; `MI-Review-19`, `MI-Review-19-Edit`, `MI-Review-20-Edit` -> 20-Edit kept, the others RETIRED with `superseded_by`; `.doc` preferred over same-version `.pdf`; `EarthWorksI5-Review-1J`/`-1K`/`-2-A`/`-2` ordering; `-condensed` and `-Complete` stay separate families; dated manuals land in NEEDS DECISION; overrides win.
  - `sections`: headings detected (short no-period line, `Day 1:`, `Part II:`, numbered); a chunk never crosses a section; "approx." and "e.g." do not split sentences.
  - `retrieve`: RRF ordering on a hand-made ranking; at most 3 chunks per document; glossary expansion (`MF` -> `Multi-Frequency`); RETIRED documents never returned; with embeddings missing, FTS5 alone still returns results.
  - `ingest`: unchanged file skipped by sha256; changed file replaces its chunks; new higher version retires the old one.
  - `answer` (story 2): follow-up with history is rewritten before retrieval and the rewrite is returned; no history -> no rewrite call; invalid `[n]` stripped; under-cited answer falls back to passages; LM Studio down -> clear message, passages still returned. Mock the HTTP call.
  - `knowledge` (story 3): merge on normalised names and aliases; facts without evidence dropped; schema-invalid model output skipped and logged, not crashed.
  - `notes` (story 4): note file round-trip; note outranks a handout chunk with equal scores.
  - Each new behaviour gets a witnessed red (mutate, see it fail) per AGENTS.md section 5.
- e2e: n/a as automated (needs the confidential corpus and LM Studio). Manual check per story against acceptance criteria, recorded in the session log with counts only.
- Local eval: `eval/questions.yaml` in the data folder already exists (started 2026-10-21 with Daniel's questions). Each entry is `{q, expect: [families], history?, answer_should_say?}`; a hit is any expected family among the top 5 passages. Entries may carry a `history` list for follow-up questions. `answer_should_say` is the fact the answer must contain (mostly the class name for "which class" questions); `eval --answers` runs the full ask flow and prints each answer beside it for Daniel to mark, since judging it automatically would need a second model and is not worth it yet. Daniel adds to it over time. `python -m handouts eval` prints hits/total and stores the counts in `eval_runs`.

## Architecture map delta

Yes. Replace data flow 3 in `docs/ARCHITECTURE.md` with the new flow (catalogue -> extract -> sections/chunks -> SQLite FTS5 + LM Studio embeddings -> hybrid retrieval -> ask/cards/notes), add `backend/handouts/` to the layout table with a `verify: exists` line, and add the invariant "no handout-derived content inside the repository".

## ADR

Yes: `0008-handouts-knowledge-base.md`, written in story 1, superseding ADR-0003 (set 0003's Status to "Superseded by ADR-0008"). Context: v1 gaps observed above. Decision: catalogue with latest-version rule; textutil + pypdf; SQLite FTS5 + nomic embeddings via LM Studio, fused; Qwen-extracted entity/fact layer with per-fact evidence; teacher notes as a trusted source; data outside the public repo. Alternatives rejected: keep sentence-transformers (heavy torch dependency, weaker model, nothing gained now that LM Studio serves an embedder); a vector database (one user, ~10k chunks: SQLite is enough); a file watcher (startup + button covers one user); a hosted model (handouts would leave the machine).

## Cross-repo impact

None. The data folder `~/Documents/Handouts-KB` is created by the first ingest.

## Open questions (each with a recommended answer)

1. (Answered 2026-10-21: glossary filled above; the 2026 manual is current.)
2. (Answered 2026-10-21: Daniel's 20 eval questions are written; `eval/questions.yaml` holds 21 entries. Daniel may add more at any time.)
3. Extraction model: 27B (better) or 9B (about 3x faster)? Recommended: 27B overnight for the first run, configurable via `HANDOUTS_EXTRACT_MODEL`.
4. Should the zip's mantra audio and Mehindra photos ever be searchable? Recommended: no, for now; revisit with audio transcription.

## BACKLOG

- Audio transcription (`.m4a`, the mantra `.mp3`s) for a later round; Daniel did not choose it now.
- Answer feedback (thumbs) to grow the eval set automatically; not chosen now.
- "What changed between versions" questions using RETIRED rows.
- Students with class-gated access: out of scope; the `facts.introduced_in` data would be the basis for gating later.
- (found in story 1) `frontend/tsconfig.json`: `resolveJsonModule` with classic module resolution makes `tsc --noEmit` fail on main as well (TS5070); `vite build` is unaffected.
- (found in story 1) `npx eslint` cannot run: the project has a legacy `.eslintrc` and ESLint 9 needs `eslint.config.js`.
- (found in story 1) CI measures `--cov=app` only; add `--cov=handouts` so the ratchet covers the handouts package (tooling change, separate PR).
- (found in story 1) A file skipped as "identical text" stays skipped if its twin is later deleted, until `python -m handouts ingest --full`.
- (found in story 1) Port 8000 on Daniel's Mac is held by a static file server started in `~/Documents/Finance`, so the dashboard frontend (proxy to 8000) cannot reach this backend until that is stopped.
