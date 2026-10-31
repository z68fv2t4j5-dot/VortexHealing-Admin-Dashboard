"""CLI: python -m handouts ingest [--dry-run] [--full] | status | extract-knowledge | apply-knowledge | eval [--answers]"""
import argparse
import json

from handouts import improve, knowledge, store
from handouts.ingest import db_path, run


def evaluate() -> None:
    result = improve.search_check()
    for r in result["questions"]:
        print(f"{'HIT ' if r['hit'] else 'MISS'}  {r['q']}\n      found: {', '.join(r['found'])}")
    print(f"\n{result['hits']}/{result['total']} questions found an expected handout in the top 5")
    conn = store.connect(db_path())
    conn.execute("insert into eval_runs(ran_at, hits, total) values (?,?,?)", (store._now(), result["hits"], result["total"]))
    conn.commit()


def evaluate_answers() -> None:
    """Asks every test question; the run is marked in the Improve tab on the Handouts page."""
    run = improve.answer_all(improve.new_run())
    s = improve.summary(run)
    print(f"\nRun {run['id']}: {s['answered']} answers, about {s['average_seconds']} s each. Mark it in the Improve tab.")


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
    ev.add_argument("--answers", action="store_true", help="ask Qwen every question; mark the run in the Improve tab")
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
