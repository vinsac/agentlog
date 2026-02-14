"""
Visual diff rendering for agentlog (Phase 5).

Renders code changes in human-readable format for non-technical review.
"""

import re
from typing import List, Dict, Any, Optional, Tuple


# ---------------------------------------------------------------------------
# Diff Parsing
# ---------------------------------------------------------------------------

def parse_diff(diff_text: str) -> List[Dict[str, Any]]:
    """
    Parse git diff output into structured chunks.
    
    Args:
        diff_text: Raw git diff output
        
    Returns:
        List of diff chunks
    """
    chunks = []
    current_file = None
    current_chunk = []
    
    for line in diff_text.split('\n'):
        # File header
        if line.startswith('diff --git'):
            if current_file and current_chunk:
                chunks.append({
                    "file": current_file,
                    "lines": current_chunk
                })
            current_chunk = []
            
        elif line.startswith('--- a/'):
            current_file = line[6:]
            
        elif line.startswith('+++ b/'):
            new_file = line[6:]
            if current_file == "/dev/null":
                current_file = new_file
                
        # Hunk header
        elif line.startswith('@@'):
            match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
            if match:
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1
                
                current_chunk.append({
                    "type": "hunk",
                    "old_start": old_start,
                    "old_count": old_count,
                    "new_start": new_start,
                    "new_count": new_count
                })
        
        # Added line
        elif line.startswith('+'):
            current_chunk.append({
                "type": "add",
                "content": line[1:]
            })
        
        # Removed line
        elif line.startswith('-'):
            current_chunk.append({
                "type": "remove",
                "content": line[1:]
            })
        
        # Context line
        elif line.startswith(' '):
            current_chunk.append({
                "type": "context",
                "content": line[1:]
            })
    
    if current_file and current_chunk:
        chunks.append({
            "file": current_file,
            "lines": current_chunk
        })
    
    return chunks


# ---------------------------------------------------------------------------
# Markdown Rendering
# ---------------------------------------------------------------------------

def render_diff_markdown(diff_text: str, max_lines: int = 100) -> str:
    """
    Render diff as markdown for review.
    
    Args:
        diff_text: Raw git diff
        max_lines: Maximum lines to render
        
    Returns:
        Markdown formatted diff
    """
    chunks = parse_diff(diff_text)
    
    lines = ["## Code Changes"]
    total_lines = 0
    
    for chunk in chunks:
        if total_lines >= max_lines:
            lines.append("\n*... (truncated) ...*")
            break
        
        file = chunk["file"]
        lines.append(f"\n### `{file}`")
        lines.append("\n```diff")
        
        for line in chunk["lines"]:
            if total_lines >= max_lines:
                break
                
            line_type = line.get("type")
            content = line.get("content", "")
            
            if line_type == "hunk":
                lines.append(f"@@ -{line['old_start']},{line['old_count']} +{line['new_start']},{line['new_count']} @@")
            elif line_type == "add":
                lines.append(f"+{content}")
            elif line_type == "remove":
                lines.append(f"-{content}")
            elif line_type == "context":
                lines.append(f" {content}")
            
            total_lines += 1
        
        lines.append("```")
    
    return '\n'.join(lines)


def render_diff_html(diff_text: str, max_lines: int = 100) -> str:
    """
    Render diff as HTML for review.
    
    Args:
        diff_text: Raw git diff
        max_lines: Maximum lines to render
        
    Returns:
        HTML formatted diff
    """
    chunks = parse_diff(diff_text)
    
    lines = [
        '<div class="diff-review">',
        '<h2>Code Changes</h2>'
    ]
    total_lines = 0
    
    for chunk in chunks:
        if total_lines >= max_lines:
            lines.append('<p><em>... (truncated) ...</em></p>')
            break
        
        file = chunk["file"]
        lines.append(f'<h3>{file}</h3>')
        lines.append('<pre class="diff">')
        
        for line in chunk["lines"]:
            if total_lines >= max_lines:
                break
                
            line_type = line.get("type")
            content = line.get("content", "")
            escaped = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            if line_type == "hunk":
                lines.append(f'<span class="hunk">@@ -{line["old_start"]},{line["old_count"]} +{line["new_start"]},{line["new_count"]} @@</span>')
            elif line_type == "add":
                lines.append(f'<span class="add">+{escaped}</span>')
            elif line_type == "remove":
                lines.append(f'<span class="remove">-{escaped}</span>')
            elif line_type == "context":
                lines.append(f'<span class="context"> {escaped}</span>')
            
            total_lines += 1
        
        lines.append('</pre>')
    
    lines.append('</div>')
    lines.append('<style>')
    lines.append('.diff-review { font-family: monospace; }')
    lines.append('.diff { background: #f5f5f5; padding: 10px; overflow-x: auto; }')
    lines.append('.hunk { color: #666; font-weight: bold; }')
    lines.append('.add { background: #dfd; color: #080; }')
    lines.append('.remove { background: #fdd; color: #800; }')
    lines.append('.context { color: #333; }')
    lines.append('</style>')
    
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Summary Generation
# ---------------------------------------------------------------------------

def summarize_diff(diff_text: str) -> Dict[str, Any]:
    """
    Generate a summary of changes.
    
    Args:
        diff_text: Raw git diff
        
    Returns:
        Summary dict with statistics
    """
    chunks = parse_diff(diff_text)
    
    files_changed = len(chunks)
    lines_added = 0
    lines_removed = 0
    file_changes = []
    
    for chunk in chunks:
        file = chunk["file"]
        added = 0
        removed = 0
        
        for line in chunk["lines"]:
            line_type = line.get("type")
            if line_type == "add":
                added += 1
            elif line_type == "remove":
                removed += 1
        
        lines_added += added
        lines_removed += removed
        
        file_changes.append({
            "file": file,
            "added": added,
            "removed": removed,
            "net_change": added - removed
        })
    
    # Detect change types
    new_files = [f for f in file_changes if f["added"] > 0 and f["removed"] == 0]
    deleted_files = [f for f in file_changes if f["added"] == 0 and f["removed"] > 0]
    modified_files = [f for f in file_changes if f["added"] > 0 and f["removed"] > 0]
    
    return {
        "files_changed": files_changed,
        "lines_added": lines_added,
        "lines_removed": lines_removed,
        "net_change": lines_added - lines_removed,
        "new_files": len(new_files),
        "deleted_files": len(deleted_files),
        "modified_files": len(modified_files),
        "file_changes": file_changes,
        "change_summary": _describe_changes(new_files, deleted_files, modified_files)
    }


def _describe_changes(new: List[Dict], deleted: List[Dict], modified: List[Dict]) -> str:
    """Generate human-readable change description."""
    parts = []
    
    if new:
        parts.append(f"{len(new)} new file{'s' if len(new) > 1 else ''}")
    if deleted:
        parts.append(f"{len(deleted)} deleted file{'s' if len(deleted) > 1 else ''}")
    if modified:
        parts.append(f"{len(modified)} modified file{'s' if len(modified) > 1 else ''}")
    
    if not parts:
        return "No changes"
    
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_git_diff(
    format: str = "markdown",
    max_lines: int = 100,
    cwd: Optional[str] = None
) -> str:
    """
    Render current git diff in specified format.
    
    Args:
        format: "markdown", "html", "raw"
        max_lines: Maximum lines to include
        cwd: Working directory
        
    Returns:
        Formatted diff
        
    Example:
        >>> md = render_git_diff("markdown")
        >>> html = render_git_diff("html", max_lines=50)
    """
    from ._git import get_git_info
    
    git_info = get_git_info(cwd)
    diff_text = git_info.get("diff", "")
    
    if not diff_text:
        return "No changes"
    
    if format == "html":
        return render_diff_html(diff_text, max_lines)
    elif format == "markdown":
        return render_diff_markdown(diff_text, max_lines)
    else:
        return diff_text[:max_lines * 100]


def render_session_diff(
    session_id: Optional[str] = None,
    format: str = "markdown"
) -> str:
    """
    Render diff for a session.
    
    Args:
        session_id: Session to render (default: current)
        format: Output format
        
    Returns:
        Formatted diff
    """
    from ._session import get_session_id
    from ._workspace import load_snapshot
    
    if session_id is None:
        session_id = get_session_id()
    
    if not session_id:
        return "No active session"
    
    # Try to load session snapshot
    snapshot = load_snapshot(f"session_{session_id}")
    if snapshot and "git" in snapshot:
        diff_text = snapshot["git"].get("diff", "")
        if diff_text:
            if format == "html":
                return render_diff_html(diff_text)
            elif format == "markdown":
                return render_diff_markdown(diff_text)
    
    # Fall back to current git diff
    return render_git_diff(format)


def get_diff_summary(cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a quick summary of current changes.
    
    Args:
        cwd: Working directory
        
    Returns:
        Summary dict
    """
    from ._git import get_git_info
    
    git_info = get_git_info(cwd)
    diff_text = git_info.get("diff", "")
    
    if not diff_text:
        return {
            "has_changes": False,
            "summary": "No uncommitted changes"
        }
    
    summary = summarize_diff(diff_text)
    summary["has_changes"] = True
    summary["commit"] = git_info.get("commit", "")[:7]
    summary["branch"] = git_info.get("branch")
    
    return summary


def export_diff_for_review(
    output_file: Optional[str] = None,
    format: str = "markdown"
) -> str:
    """
    Export diff for review to file or string.
    
    Args:
        output_file: Optional file to write (default: return string)
        format: Output format
        
    Returns:
        Diff content or file path
    """
    content = render_git_diff(format)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(content)
        return output_file
    
    return content
