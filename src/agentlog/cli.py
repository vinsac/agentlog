"""Command-line handoff tools for agentlog."""

import argparse
import json
import sys
from typing import Optional

from ._store import DEFAULT_STORE_PATH, export_debug_bundle, list_incidents, load_incident_entries


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="agentlog", description="Inspect and export agentlog incidents.")
    parser.add_argument("--store", default=DEFAULT_STORE_PATH, help="Path to agentlog incident JSONL store.")

    subparsers = parser.add_subparsers(dest="command")
    incidents = subparsers.add_parser("incidents", help="Work with stored incidents.")
    incident_commands = incidents.add_subparsers(dest="incident_command")

    list_parser = incident_commands.add_parser("list", help="List stored incidents.")
    list_parser.add_argument("--limit", type=int, default=50)
    list_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")

    inspect_parser = incident_commands.add_parser("inspect", help="Show raw stored entries.")
    inspect_parser.add_argument("incident_id")
    inspect_parser.add_argument("--limit", type=int, default=20)

    export_parser = incident_commands.add_parser("export", help="Export a debug bundle for an agent.")
    export_parser.add_argument("incident_id")
    export_parser.add_argument("--tokens", type=int, default=4000)
    export_parser.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    export_parser.add_argument("--session-id")
    export_parser.add_argument("--no-metadata", action="store_true")
    export_parser.add_argument("--no-explain", action="store_true")
    export_parser.add_argument("--out", help="Write bundle to a file instead of stdout.")

    args = parser.parse_args(argv)

    if args.command == "incidents" and args.incident_command == "list":
        rows = list_incidents(args.store, limit=args.limit)
        if args.json:
            print(json.dumps(rows, indent=2, default=str))
        else:
            _print_incident_table(rows)
        return 0

    if args.command == "incidents" and args.incident_command == "inspect":
        entries = load_incident_entries(args.incident_id, path=args.store, limit=args.limit)
        for entry in entries:
            print(json.dumps(entry, default=str, separators=(",", ":")))
        return 0

    if args.command == "incidents" and args.incident_command == "export":
        bundle = export_debug_bundle(
            incident_id=args.incident_id,
            session_id=args.session_id,
            token_budget=args.tokens,
            path=args.store,
            format=args.format,
            include_metadata=not args.no_metadata,
            explain=not args.no_explain,
        )
        if args.out:
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(bundle)
                if not bundle.endswith("\n"):
                    handle.write("\n")
        else:
            print(bundle)
        return 0

    parser.print_help(sys.stderr)
    return 2


def _print_incident_table(rows):
    if not rows:
        print("No incidents found.")
        return
    print("INCIDENT_ID\tEVENTS\tSESSION_ID\tLAST_ERROR")
    for row in rows:
        print(
            f"{row['incident_id']}\t"
            f"{row['events']}\t"
            f"{row.get('session_id') or ''}\t"
            f"{row.get('last_error') or ''}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
