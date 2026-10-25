"""CLI: python -m handouts ingest [--dry-run] [--full] | status | extract-knowledge | apply-knowledge | eval [--answers]"""
import argparse
import asyncio
import json
import time
from datetime import datetime

import yaml

from handouts import kb_dir, store
from handouts.answer import ask_once
from handouts import knowledge
from handouts.ingest import db_path, run
from handouts.retrieve import search


def load_questions() -> list[dict]:
    return yaml.safe_load((kb_dir() / "eval" / "questions.yaml").read_text()) or []


def evaluate() -> None:
    questions = load_questions()
    hits = 0
    for item in questions:
        query = " ".join([*item.get("history", []), item["q"]])
        # Handout passages only: answers add matching teacher notes on top of these, not in their place.
        found = [p["family"] for p in search(query, limit=10) if p["source_kind"] == "handout"][:5]
        expected = {f.lower() for f in item["expect"]}
        hit = bool(expected & set(found))
        hits += hit
        print(f"{'HIT ' if hit else 'MISS'}  {item['q']}\n      found: {', '.join(dict.fromkeys(found))}")
    print(f"\n{hits}/{len(questions)} questions found an expected handout in the top 5")
    conn = store.connect(db_path())
    conn.execute("insert into eval_runs(ran_at, hits, total) values (?,?,?)", (store._now(), hits, len(questions)))
    conn.commit()


def evaluate_answers() -> None:
    """Runs every question through Ask and writes a marking sheet for Daniel into the data folder."""
    answers: dict[str, str] = {}
    lines = [f"# Handouts answers to mark, {datetime.now():%Y-%m-%d %H:%M}", "",
             "For each answer, tick one box and add a note if it is wrong or missing something.", ""]
    for n, item in enumerate(load_questions(), 1):
        history = [{"q": h, "answer": answers.get(h, "")} for h in item.get("history", [])]
        start = time.time()
        result = asyncio.run(ask_once(item["q"], history))
        seconds = time.time() - start
        answers[item["q"]] = result["answer"] or ""
        print(f"{n:2}. {seconds:4.0f}s  {item['q']}")
        sources = "; ".join(f"[{i}] {p['title']} — {p['heading_path'] or 'opening section'}"
                            for i, p in enumerate(result["passages"], 1))
        lines += [f"## {n}. {item['q']}", ""]
        if result["standalone"] != item["q"]:
            lines += [f"*Understood as:* {result['standalone']}", ""]
        if result["searches"]:
            lines += [f"*Searched for:* {' · '.join(result['searches'])}", ""]
        if item.get("answer_should_say"):
            lines += [f"*Should say:* {item['answer_should_say']}", ""]
        body = result["answer_error"] or result["answer"] or "(no answer)"
        if result["fallback"]:
            body = "(hidden on the page: too few citations)\n\n" + body
        lines += [f"*{seconds:.0f} seconds*", "", body, "", f"<sub>Sources: {sources}</sub>", "",
                  "- [ ] Right  - [ ] Partly right  - [ ] Wrong", "", "Note:", "", "---", ""]
    out = kb_dir() / "eval" / f"answers-{datetime.now():%Y%m%d-%H%M}.md"
    out.write_text("\n".join(lines))
    print(f"\nMarking sheet: {out}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m handouts")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="scan the handouts folder and update the index")
    ingest.add_argument("--dry-run", action="store_true", help="print the catalogue only; write nothing")
    ingest.add_argument("--full", action="store_true", help="re-index every file, changed or not")
    sub.add_parser("status", help="print index counts")
    km = sub.add_parser("extract-knowledge", help="build the knowledge map with Qwen (resumable)")
    km.add_argument("--limit", type=int, help="read at most this many sections")
    km.add_argument("--concurrency", type=int, default=4, help="sections read at once (LM Studio parallel slots)")
    sub.add_parser("apply-knowledge", help="rebuild entities and facts from the cached readings")
    ev = sub.add_parser("eval", help="run the questions in eval/questions.yaml")
    ev.add_argument("--answers", action="store_true", help="also ask Qwen and write a marking sheet")
    args = parser.parse_args()

    if args.command == "ingest":
        run(dry_run=args.dry_run, full=args.full)
    elif args.command == "status":
        conn = store.connect(db_path())
        print(json.dumps({**store.counts(conn), "last_scan": store.get_meta(conn, "last_scan")}, indent=2))
    elif args.command == "extract-knowledge":
        knowledge.run(limit=args.limit, concurrency=args.concurrency)
    elif args.command == "apply-knowledge":
        print(knowledge.apply(store.connect(db_path())))
    elif args.command == "eval":
        evaluate_answers() if args.answers else evaluate()


if __name__ == "__main__":
    main()
