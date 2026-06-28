"""Command-line handoff tools for agentlog."""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

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
    inspect_parser.add_argument("incident_id", nargs="?")
    inspect_parser.add_argument("--limit", type=int, default=20)
    inspect_parser.add_argument("--latest", action="store_true", help="Inspect the most recent incident.")
    inspect_parser.add_argument("--session-id", help="Inspect entries for a session without an incident id.")

    export_parser = incident_commands.add_parser("export", help="Export a debug bundle for an agent.")
    export_parser.add_argument("incident_id", nargs="?")
    export_parser.add_argument("--latest", action="store_true", help="Export the most recent incident.")
    export_parser.add_argument("--tokens", type=int, default=4000)
    export_parser.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    export_parser.add_argument("--session-id")
    export_parser.add_argument(
        "--scope",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Filter exported context by an exact-match scope field. Can be repeated.",
    )
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
        incident_id = _resolve_incident_id(args.store, args.incident_id, args.latest)
        if not incident_id and not args.session_id:
            print("error: provide an incident id, --latest, or --session-id", file=sys.stderr)
            return 2
        entries = load_incident_entries(
            incident_id,
            session_id=args.session_id,
            path=args.store,
            limit=args.limit,
        )
        if not entries:
            _print_not_found(incident_id, args.session_id)
            return 1
        for entry in entries:
            print(json.dumps(entry, default=str, separators=(",", ":")))
        return 0

    if args.command == "incidents" and args.incident_command == "export":
        incident_id = _resolve_incident_id(args.store, args.incident_id, args.latest)
        if not incident_id and not args.session_id:
            print("error: provide an incident id, --latest, or --session-id", file=sys.stderr)
            return 2
        if not load_incident_entries(incident_id, session_id=args.session_id, path=args.store, limit=1):
            _print_not_found(incident_id, args.session_id)
            return 1
        bundle = export_debug_bundle(
            incident_id=incident_id,
            session_id=args.session_id,
            scope=_parse_scope(args.scope),
            token_budget=args.tokens,
            path=args.store,
            format=args.format,
            include_metadata=not args.no_metadata,
            explain=not args.no_explain,
        )
        if args.out:
            dirpath = os.path.dirname(args.out)
            if dirpath:
                os.makedirs(dirpath, exist_ok=True)
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


def _resolve_incident_id(path: str, incident_id: Optional[str], latest: bool) -> Optional[str]:
    if latest:
        incidents = list_incidents(path, limit=1)
        if not incidents:
            return None
        return incidents[0]["incident_id"]
    return incident_id


def _parse_scope(scope_items: List[str]) -> Dict[str, str]:
    scope: Dict[str, str] = {}
    for item in scope_items:
        if "=" not in item:
            raise SystemExit(f"invalid --scope value {item!r}; expected KEY=VALUE")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"invalid --scope value {item!r}; key cannot be empty")
        scope[key] = value
    return scope


def _print_not_found(incident_id: Optional[str], session_id: Optional[str]) -> None:
    target = []
    if incident_id:
        target.append(f"incident_id={incident_id}")
    if session_id:
        target.append(f"session_id={session_id}")
    print(f"error: no stored entries found for {' '.join(target) or 'requested scope'}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
