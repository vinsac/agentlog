"""
Deterministic debug-context assembly.

This module owns the capture -> compress -> handoff boundary. Storage provides
events; this module selects, budgets, and formats them for a coding agent.
"""

import json
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ._priority import get_entry_priority
from ._redaction import redaction_summary
from ._tokens import estimate_tokens, estimate_tokens_dict


HIGH_PRIORITY_TAGS = {"error", "session", "decision", "tool", "llm", "operation"}


def assemble_debug_context(
    entries: Iterable[Dict[str, Any]],
    *,
    max_tokens: int = 4000,
    session_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    scope: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False,
    explain: bool = False,
) -> str:
    """
    Build a stable, token-budgeted debug bundle.

    Args:
        entries: Captured event dictionaries.
        max_tokens: Approximate output budget.
        session_id: Optional session filter.
        incident_id: Optional incident filter.
        scope: Optional exact-match filters such as {"request_id": "req_1"}.
        include_metadata: Include redaction/budget metadata in the header.
        explain: Include selection and drop reasons in the header.
    """
    return assemble_debug_context_with_metadata(
        entries,
        max_tokens=max_tokens,
        session_id=session_id,
        incident_id=incident_id,
        scope=scope,
        include_metadata=include_metadata,
        explain=explain,
    )["context"]


def assemble_debug_context_with_metadata(
    entries: Iterable[Dict[str, Any]],
    *,
    max_tokens: int = 4000,
    session_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    scope: Optional[Dict[str, Any]] = None,
    include_metadata: bool = False,
    explain: bool = False,
) -> Dict[str, Any]:
    """Build a stable debug bundle plus machine-readable selection metadata."""
    input_entries = list(entries)
    filtered, filter_notes = filter_entries(
        input_entries,
        session_id=session_id,
        incident_id=incident_id,
        scope=scope,
    )

    header = _build_header(
        filtered,
        session_id=session_id,
        incident_id=incident_id,
        include_metadata=include_metadata,
        explain=explain,
        filter_notes=filter_notes,
    )

    selected, selection = select_entries(filtered, max_tokens=max_tokens, header=header)

    if include_metadata or explain:
        header = _build_header(
            filtered,
            session_id=session_id,
            incident_id=incident_id,
            include_metadata=include_metadata,
            explain=explain,
            filter_notes=filter_notes,
            selection=selection,
        )

    parts = [header]
    if selected:
        parts.append("\n".join(_to_json_line(entry) for entry in selected))
    return {
        "context": "\n".join(parts),
        "input_count": len(input_entries),
        "filtered_count": len(filtered),
        "selected_count": len(selected),
        "dropped_count": len(selection["dropped"]),
        "filters": filter_notes,
        "selection": selection,
    }


def filter_entries(
    entries: List[Dict[str, Any]],
    *,
    session_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    scope: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Filter events by handoff scope."""
    notes: List[str] = []
    filtered = entries

    if session_id:
        before = len(filtered)
        filtered = [entry for entry in filtered if entry.get("session_id") == session_id]
        notes.append(f"session_id={session_id} kept {len(filtered)}/{before}")

    if incident_id:
        before = len(filtered)
        filtered = [entry for entry in filtered if _entry_has_value(entry, "incident_id", incident_id)]
        notes.append(f"incident_id={incident_id} kept {len(filtered)}/{before}")

    if scope:
        for key, value in scope.items():
            before = len(filtered)
            filtered = [entry for entry in filtered if _entry_has_value(entry, key, value)]
            notes.append(f"scope.{key} kept {len(filtered)}/{before}")

    return filtered, notes


def select_entries(
    entries: List[Dict[str, Any]],
    *,
    max_tokens: int,
    header: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Select entries by priority, recency, and token budget.

    Selection is deterministic: priority desc, sequence desc for picking, then
    chronological order for output.
    """
    header_tokens = estimate_tokens(header)
    remaining = max(0, max_tokens - header_tokens - 8)

    candidates = sorted(
        entries,
        key=lambda entry: (
            -_selection_priority(entry),
            -int(entry.get("seq", 0)),
            _to_json_line(entry),
        ),
    )

    selected: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []
    spent = 0

    for entry in candidates:
        tokens = estimate_tokens_dict(entry)
        if tokens <= remaining - spent:
            selected.append(entry)
            spent += tokens
        else:
            dropped.append(
                {
                    "seq": entry.get("seq"),
                    "tag": entry.get("tag", "info"),
                    "reason": "token_budget",
                    "tokens": tokens,
                }
            )

    selected.sort(key=lambda entry: int(entry.get("seq", 0)))
    return selected, {
        "budget_tokens": max_tokens,
        "header_tokens": header_tokens,
        "entry_tokens": spent,
        "selected": len(selected),
        "dropped": dropped,
    }


def _selection_priority(entry: Dict[str, Any]) -> int:
    priority = get_entry_priority(entry)
    if entry.get("tag") in HIGH_PRIORITY_TAGS:
        priority += 3
    if entry.get("tag") == "error":
        priority += 5
    return priority


def _build_header(
    entries: List[Dict[str, Any]],
    *,
    session_id: Optional[str],
    incident_id: Optional[str],
    include_metadata: bool,
    explain: bool,
    filter_notes: List[str],
    selection: Optional[Dict[str, Any]] = None,
) -> str:
    title = "# agentlog debug context"
    if session_id:
        title += f" (session: {session_id})"
    if incident_id:
        title += f" (incident: {incident_id})"

    lines = [title]

    git = _latest_git(entries)
    if git and git.get("commit"):
        branch = git.get("branch", "?")
        commit_short = str(git["commit"])[:7]
        dirty = " dirty" if git.get("dirty") else ""
        lines.append(f"# git: {branch}@{commit_short}{dirty}")

    token_totals = _token_summary(entries)
    if token_totals["total"] > 0:
        models = ", ".join(
            f"{model}: {data['in']}in/{data['out']}out"
            for model, data in token_totals["by_model"].items()
        )
        lines.append(f"# tokens: {token_totals['total']} total ({models})")

    if include_metadata:
        policy = redaction_summary()
        lines.append(
            "# redaction: "
            f"deny_fields={policy['deny_fields']} "
            f"pii_fields={policy['pii_fields']} "
            f"patterns={policy['patterns']} "
            f"allowlist={policy['allowlist_enabled']}"
        )

    if explain:
        for note in filter_notes:
            lines.append(f"# filter: {note}")
        if selection:
            lines.append(
                "# budget: "
                f"{selection['entry_tokens']} entry tokens + "
                f"{selection['header_tokens']} header tokens / "
                f"{selection['budget_tokens']}"
            )
            lines.append(
                "# selection: "
                f"{selection['selected']} selected, {len(selection['dropped'])} dropped"
            )
            for dropped in selection["dropped"][:10]:
                lines.append(
                    "# dropped: "
                    f"seq={dropped['seq']} tag={dropped['tag']} "
                    f"reason={dropped['reason']} tokens={dropped['tokens']}"
                )

    return "\n".join(lines)


def _latest_git(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    for entry in reversed(entries):
        git = entry.get("git")
        if isinstance(git, dict):
            return git
    return {}


def _token_summary(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_in = 0
    total_out = 0
    by_model: Dict[str, Dict[str, int]] = {}
    for entry in entries:
        if entry.get("tag") != "llm":
            continue
        model = str(entry.get("model", "unknown"))
        tokens_in = int(entry.get("tokens_in", 0) or 0)
        tokens_out = int(entry.get("tokens_out", 0) or 0)
        total_in += tokens_in
        total_out += tokens_out
        by_model.setdefault(model, {"in": 0, "out": 0})
        by_model[model]["in"] += tokens_in
        by_model[model]["out"] += tokens_out
    return {"total_in": total_in, "total_out": total_out, "total": total_in + total_out, "by_model": by_model}


def _entry_has_value(entry: Dict[str, Any], key: str, value: Any) -> bool:
    if entry.get(key) == value:
        return True
    ctx = entry.get("ctx")
    if isinstance(ctx, dict):
        descriptor = ctx.get(key)
        if descriptor == value:
            return True
        if isinstance(descriptor, dict) and descriptor.get("v") == value:
            return True
    return False


def _to_json_line(entry: Dict[str, Any]) -> str:
    return json.dumps(entry, default=str, separators=(",", ":"))
