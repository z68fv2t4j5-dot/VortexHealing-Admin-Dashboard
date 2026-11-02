"""CLI: python -m transcript_import zoom [--dry-run]"""
import argparse

from transcript_import import zoom


def main(argv: "list[str] | None" = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m transcript_import")
    sub = parser.add_subparsers(dest="command", required=True)
    z = sub.add_parser("zoom", help="download new Zoom transcripts (last six months) and file them")
    z.add_argument("--dry-run", action="store_true", help="print what would be downloaded; write nothing")
    args = parser.parse_args(argv)
    if args.command == "zoom":
        c = zoom.sync(dry_run=args.dry_run)
        verb = "would download" if args.dry_run else "downloaded"
        print(f"\nmeeting instances listed: {c['listed']}; {verb}: {c['new']}; "
              f"already had: {c['already_had']}; unavailable: {c['unavailable']}")


if __name__ == "__main__":
    main()
