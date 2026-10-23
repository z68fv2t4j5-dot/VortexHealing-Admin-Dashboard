"""CLI: python -m handouts ingest [--dry-run] [--full] | status | eval"""
import argparse
import json

import yaml

from handouts import kb_dir, store
from handouts.ingest import db_path, run
from handouts.retrieve import search


def evaluate() -> None:
    questions = yaml.safe_load((kb_dir() / "eval" / "questions.yaml").read_text()) or []
    hits = 0
    for item in questions:
        query = " ".join([*item.get("history", []), item["q"]])
        found = [p["family"] for p in search(query, limit=5)]
        expected = {f.lower() for f in item["expect"]}
        hit = bool(expected & set(found))
        hits += hit
        print(f"{'HIT ' if hit else 'MISS'}  {item['q']}\n      found: {', '.join(dict.fromkeys(found))}")
    print(f"\n{hits}/{len(questions)} questions found an expected handout in the top 5")
    conn = store.connect(db_path())
    conn.execute("insert into eval_runs(ran_at, hits, total) values (?,?,?)", (store._now(), hits, len(questions)))
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m handouts")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="scan the handouts folder and update the index")
    ingest.add_argument("--dry-run", action="store_true", help="print the catalogue only; write nothing")
    ingest.add_argument("--full", action="store_true", help="re-index every file, changed or not")
    sub.add_parser("status", help="print index counts")
    sub.add_parser("eval", help="run the questions in eval/questions.yaml")
    args = parser.parse_args()

    if args.command == "ingest":
        run(dry_run=args.dry_run, full=args.full)
    elif args.command == "status":
        conn = store.connect(db_path())
        print(json.dumps({**store.counts(conn), "last_scan": store.get_meta(conn, "last_scan")}, indent=2))
    elif args.command == "eval":
        evaluate()


if __name__ == "__main__":
    main()
