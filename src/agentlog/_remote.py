"""
Remote sync for agentlog (Phase 4) - Optional Cloudflare D1 integration.

Provides team sharing of debugging context via Cloudflare D1 database.
This is optional - core functionality remains local-first.
"""

import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _get_d1_config() -> Optional[Dict[str, str]]:
    """
    Get D1 configuration from environment.
    
    Returns:
        Config dict or None if not configured
    """
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    database_id = os.getenv("CLOUDFLARE_D1_DATABASE_ID")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    
    if not all([account_id, database_id, api_token]):
        return None
    
    return {
        "account_id": account_id,
        "database_id": database_id,
        "api_token": api_token
    }


def is_d1_enabled() -> bool:
    """Check if D1 sync is enabled."""
    return _get_d1_config() is not None


# ---------------------------------------------------------------------------
# D1 API Client
# ---------------------------------------------------------------------------

class D1Client:
    """Minimal D1 API client using stdlib only."""
    
    def __init__(self, account_id: str, database_id: str, api_token: str):
        self.account_id = account_id
        self.database_id = database_id
        self.api_token = api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}"
    
    def _request(self, method: str, path: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request to D1."""
        import urllib.request
        import urllib.error
        
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        try:
            if data:
                body = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(url, data=body, headers=headers, method=method)
            else:
                req = urllib.request.Request(url, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"error": str(e)}
    
    def query(self, sql: str, params: Optional[List[Any]] = None) -> Optional[Dict]:
        """Execute SQL query."""
        return self._request("POST", "/query", {
            "sql": sql,
            "params": params or []
        })


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

D1_SCHEMA = """
CREATE TABLE IF NOT EXISTS agentlog_sessions (
    id TEXT PRIMARY KEY,
    agent_name TEXT,
    task TEXT,
    start_ts REAL,
    end_ts REAL,
    parent_session_id TEXT,
    git_commit TEXT,
    git_branch TEXT,
    outcome TEXT,
    error_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS agentlog_events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    ts REAL NOT NULL,
    tag TEXT NOT NULL,
    payload TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES agentlog_sessions(id)
);

CREATE TABLE IF NOT EXISTS agentlog_outcomes (
    session_id TEXT PRIMARY KEY,
    outcome TEXT,
    reason TEXT,
    timestamp TEXT,
    tags TEXT,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES agentlog_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_events_session ON agentlog_events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_tag ON agentlog_events(tag);
"""


def init_d1_schema() -> bool:
    """
    Initialize D1 database schema.
    
    Returns:
        True if successful
    """
    config = _get_d1_config()
    if not config:
        return False
    
    client = D1Client(**config)
    
    for statement in D1_SCHEMA.split(';'):
        stmt = statement.strip()
        if stmt:
            result = client.query(stmt)
            if result and result.get("error"):
                return False
    
    return True


# ---------------------------------------------------------------------------
# Sync Operations
# ---------------------------------------------------------------------------

def sync_session_to_d1(session_id: Optional[str] = None) -> bool:
    """
    Sync a session to D1.
    
    Args:
        session_id: Session to sync (default: current)
        
    Returns:
        True if successful
    """
    from ._session import get_session_id, get_agent_info
    from ._buffer import get_context, token_summary
    from ._correlation import get_all_patterns
    from ._outcome import get_outcome
    
    config = _get_d1_config()
    if not config:
        return False
    
    if session_id is None:
        session_id = get_session_id()
    
    if not session_id:
        return False
    
    client = D1Client(**config)
    
    # Get session info
    agent_info = get_agent_info()
    tokens = token_summary()
    outcome = get_outcome(session_id)
    
    # Count errors for this session
    patterns = get_all_patterns()
    error_count = sum(
        1 for p in patterns.values()
        if session_id in p.get("sessions", [])
    )
    
    # Upsert session
    result = client.query(
        """
        INSERT OR REPLACE INTO agentlog_sessions 
        (id, agent_name, task, start_ts, error_count, token_count, outcome)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            session_id,
            agent_info.get("agent_name", "unknown"),
            agent_info.get("task", "unknown"),
            datetime.now().timestamp(),
            error_count,
            tokens.get("total", 0),
            outcome.get("outcome") if outcome else None
        ]
    )
    
    if result and result.get("error"):
        return False
    
    # Get events for this session
    context = get_context(tags=None)
    events = []
    for line in context.strip().split('\n'):
        if line and not line.startswith('#'):
            try:
                entry = json.loads(line)
                if entry.get("session_id") == session_id:
                    events.append(entry)
            except json.JSONDecodeError:
                pass
    
    # Sync events
    for event in events:
        event_id = event.get("seq", event.get("id", hash(str(event))))
        event_ts = event.get("ts", datetime.now().timestamp())
        event_tag = event.get("tag", "unknown")
        
        client.query(
            """
            INSERT OR IGNORE INTO agentlog_events
            (id, session_id, ts, tag, payload)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                f"{session_id}_{event_id}",
                session_id,
                event_ts,
                event_tag,
                json.dumps(event, default=str)
            ]
        )
    
    return True


def load_session_from_d1(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a session from D1.
    
    Args:
        session_id: Session to load
        
    Returns:
        Session data or None
    """
    config = _get_d1_config()
    if not config:
        return None
    
    client = D1Client(**config)
    
    # Get session
    result = client.query(
        "SELECT * FROM agentlog_sessions WHERE id = ?",
        [session_id]
    )
    
    if not result or result.get("error"):
        return None
    
    results = result.get("result", [])
    if not results:
        return None
    
    # Get events
    events_result = client.query(
        "SELECT * FROM agentlog_events WHERE session_id = ? ORDER BY ts",
        [session_id]
    )
    
    events = []
    if events_result and not events_result.get("error"):
        for row in events_result.get("result", []):
            try:
                events.append(json.loads(row.get("payload", "{}")))
            except json.JSONDecodeError:
                pass
    
    session_row = results[0]
    return {
        "id": session_row.get("id"),
        "agent_name": session_row.get("agent_name"),
        "task": session_row.get("task"),
        "outcome": session_row.get("outcome"),
        "error_count": session_row.get("error_count"),
        "token_count": session_row.get("token_count"),
        "events": events
    }


def list_d1_sessions(limit: int = 100) -> List[Dict[str, Any]]:
    """
    List sessions stored in D1.
    
    Args:
        limit: Maximum sessions to return
        
    Returns:
        List of session summaries
    """
    config = _get_d1_config()
    if not config:
        return []
    
    client = D1Client(**config)
    
    result = client.query(
        """
        SELECT id, agent_name, task, outcome, error_count, token_count
        FROM agentlog_sessions
        ORDER BY start_ts DESC
        LIMIT ?
        """,
        [limit]
    )
    
    if not result or result.get("error"):
        return []
    
    return [
        {
            "id": row.get("id"),
            "agent_name": row.get("agent_name"),
            "task": row.get("task"),
            "outcome": row.get("outcome"),
            "error_count": row.get("error_count"),
            "token_count": row.get("token_count")
        }
        for row in result.get("result", [])
    ]


def delete_d1_session(session_id: str) -> bool:
    """
    Delete a session from D1.
    
    Args:
        session_id: Session to delete
        
    Returns:
        True if deleted
    """
    config = _get_d1_config()
    if not config:
        return False
    
    client = D1Client(**config)
    
    # Delete events first (FK constraint)
    client.query(
        "DELETE FROM agentlog_events WHERE session_id = ?",
        [session_id]
    )
    
    # Delete session
    result = client.query(
        "DELETE FROM agentlog_sessions WHERE id = ?",
        [session_id]
    )
    
    if result and result.get("error"):
        return False
    
    return True


# ---------------------------------------------------------------------------
# Team Sharing Helpers
# ---------------------------------------------------------------------------

def share_session(session_id: Optional[str] = None) -> Optional[str]:
    """
    Share current session to D1 and return shareable ID.
    
    Args:
        session_id: Session to share (default: current)
        
    Returns:
        Session ID if shared successfully
    """
    from ._session import get_session_id
    
    if session_id is None:
        session_id = get_session_id()
    
    if not session_id:
        return None
    
    if sync_session_to_d1(session_id):
        return session_id
    
    return None


def import_shared_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Import a shared session from D1.
    
    Args:
        session_id: Session to import
        
    Returns:
        Session data or None
    """
    return load_session_from_d1(session_id)
