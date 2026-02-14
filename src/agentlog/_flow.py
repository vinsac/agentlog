"""
Multi-agent flow visualizer for agentlog (Clear Winner Feature #2).

The 10X feature: Make multi-agent cascade debugging tractable.
Shows data flow: Agent A → Agent B → Error in Agent C
"""

import json
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict


# ---------------------------------------------------------------------------
# Flow Graph Building
# ---------------------------------------------------------------------------

def _build_session_graph(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a graph of session interactions.
    
    Returns:
        Graph dict with nodes (sessions) and edges (data flow)
    """
    nodes = {}
    edges = []
    
    # Create nodes for each session
    for session in sessions:
        sid = session.get('session_id')
        if not sid:
            continue
        
        nodes[sid] = {
            'id': sid,
            'agent': session.get('agent', 'unknown'),
            'task': session.get('task', 'unknown')[:50],
            'parent': session.get('parent_session_id'),
            'outcome': session.get('outcome'),
            'error_count': session.get('error_count', 0),
            'start_time': session.get('start_ts')
        }
    
    # Create edges from parent relationships
    for sid, node in nodes.items():
        parent_id = node.get('parent')
        if parent_id and parent_id in nodes:
            edges.append({
                'from': parent_id,
                'to': sid,
                'type': 'parent_child'
            })
    
    # Detect data flow edges from events
    session_events = defaultdict(list)
    for session in sessions:
        sid = session.get('session_id')
        if 'events' in session:
            for event in session['events']:
                session_events[sid].append(event)
    
    return {
        'nodes': list(nodes.values()),
        'edges': edges,
        'session_events': dict(session_events)
    }


def _detect_cascade_failures(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Detect failure cascades in the session graph.
    
    Returns:
        List of cascade chains (each chain is list of session IDs)
    """
    cascades = []
    
    # Find sessions with errors
    error_sessions = [
        n['id'] for n in graph['nodes']
        if n.get('error_count', 0) > 0 or n.get('outcome') == 'failure'
    ]
    
    # Trace back from error sessions to find root causes
    for error_sid in error_sessions:
        chain = [error_sid]
        current = error_sid
        
        # Walk backwards through parent relationships
        while True:
            parent = None
            for edge in graph['edges']:
                if edge['to'] == current and edge['type'] == 'parent_child':
                    parent = edge['from']
                    break
            
            if parent and parent not in chain:
                chain.insert(0, parent)
                current = parent
            else:
                break
        
        if len(chain) > 1:
            cascades.append({
                'chain': chain,
                'error_session': error_sid,
                'description': _describe_cascade(chain, graph['nodes'])
            })
    
    return cascades


def _describe_cascade(chain: List[str], nodes: List[Dict]) -> str:
    """Generate human-readable cascade description."""
    node_map = {n['id']: n for n in nodes}
    
    parts = []
    for i, sid in enumerate(chain):
        node = node_map.get(sid, {})
        agent = node.get('agent', 'unknown')
        task = node.get('task', '')
        has_error = node.get('error_count', 0) > 0
        
        if i == 0:
            parts.append(f"{agent} started '{task}'")
        elif i == len(chain) - 1 and has_error:
            parts.append(f"→ {agent} FAILED: '{task}'")
        else:
            parts.append(f"→ {agent} processed '{task}'")
    
    return ' '.join(parts)


# ---------------------------------------------------------------------------
# Text Visualization
# ---------------------------------------------------------------------------

def _render_flow_text(graph: Dict[str, Any], cascades: List[Dict]) -> str:
    """
    Render flow as agent-readable text.
    
    Format optimized for LLM consumption.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("MULTI-AGENT FLOW ANALYSIS")
    lines.append("=" * 60)
    
    # Summary
    nodes = graph['nodes']
    edges = graph['edges']
    
    lines.append(f"\nSessions: {len(nodes)}")
    lines.append(f"Connections: {len(edges)}")
    lines.append(f"Failure Cascades Detected: {len(cascades)}")
    
    # Session list
    lines.append("\n" + "-" * 40)
    lines.append("SESSIONS")
    lines.append("-" * 40)
    
    for node in sorted(nodes, key=lambda x: x.get('start_time', '')):
        sid = node['id'][:8]
        agent = node['agent']
        task = node['task'][:40]
        outcome = node.get('outcome', '?')
        errors = node.get('error_count', 0)
        
        status = "✓" if outcome == 'success' and errors == 0 else "✗" if errors > 0 else "?"
        lines.append(f"  [{status}] {sid} | {agent}: {task}")
        if errors > 0:
            lines.append(f"      └─ {errors} error(s), outcome: {outcome}")
    
    # Cascade details
    if cascades:
        lines.append("\n" + "-" * 40)
        lines.append("FAILURE CASCADES (MOST IMPORTANT)")
        lines.append("-" * 40)
        
        for i, cascade in enumerate(cascades, 1):
            lines.append(f"\nCascade #{i}:")
            lines.append(f"  {cascade['description']}")
            lines.append(f"  Chain: {' → '.join(s[:8] for s in cascade['chain'])}")
            
            # Root cause analysis
            root = cascade['chain'][0]
            error_node = cascade['error_session']
            
            if root != error_node:
                lines.append(f"  \n  ROOT CAUSE: {root[:8]} (data originated here)")
                lines.append(f"  FAILURE POINT: {error_node[:8]} (error manifested here)")
                lines.append(f"  \n  → Data corrupted in early session, caused failure downstream")
    
    # Data flow diagram
    if len(nodes) > 1:
        lines.append("\n" + "-" * 40)
        lines.append("DATA FLOW")
        lines.append("-" * 40)
        
        # Find start nodes (no parents)
        all_children = set(e['to'] for e in edges)
        start_nodes = [n for n in nodes if n['id'] not in all_children]
        
        for start in start_nodes:
            lines.append(f"\n  {start['agent']} ({start['id'][:8]})")
            _render_subtree(start['id'], nodes, edges, lines, depth=1)
    
    lines.append("\n" + "=" * 60)
    
    return '\n'.join(lines)


def _render_subtree(node_id: str, nodes: List[Dict], edges: List[Dict], lines: List[str], depth: int = 0):
    """Recursively render subtree."""
    indent = "    " * depth
    
    # Find children
    children = [e['to'] for e in edges if e['from'] == node_id]
    
    for child_id in children:
        child = next((n for n in nodes if n['id'] == child_id), None)
        if child:
            status = "✓" if child.get('outcome') == 'success' else "✗" if child.get('error_count', 0) > 0 else "?"
            lines.append(f"{indent}└─> [{status}] {child['agent']} ({child_id[:8]}): {child['task'][:30]}")
            _render_subtree(child_id, nodes, edges, lines, depth + 1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def visualize_agent_flow(
    session_id: Optional[str] = None,
    format: str = "agent_readable",
    lookback_sessions: int = 10
) -> str:
    """
    Visualize multi-agent flow.
    
    The 10X feature: Make multi-agent cascade debugging tractable.
    
    Args:
        session_id: Starting session (default: current)
        format: Output format (only "agent_readable" supported)
        lookback_sessions: How many recent sessions to include
        
    Returns:
        Text visualization of agent flow
        
    Example:
        >>> flow = agentlog.visualize_agent_flow()
        >>> print(flow)
        # Shows: Agent A → Agent B → Error in Agent C
    """
    from ._session import get_session_id
    from ._correlation import get_all_patterns
    
    if session_id is None:
        session_id = get_session_id()
    
    # Get all sessions with parent links
    # For now, use patterns data as proxy for sessions
    all_patterns = get_all_patterns()
    
    # Build synthetic sessions from pattern data
    sessions = []
    seen_sids = set()
    
    for pattern_hash, pattern in all_patterns.items():
        for sid in pattern.get('sessions', []):
            if sid not in seen_sids:
                seen_sids.add(sid)
                sessions.append({
                    'session_id': sid,
                    'agent': 'unknown',
                    'task': f'Session with {len(pattern.get("contexts", []))} events',
                    'parent_session_id': None,
                    'outcome': None,
                    'error_count': pattern.get('count', 0),
                    'start_ts': pattern.get('first_seen')
                })
    
    # If we have a specific session, get its related sessions
    if session_id and session_id in seen_sids:
        # Find all sessions linked to this one
        related = [s for s in sessions if s['session_id'] == session_id]
        
        # Add parent if exists
        from ._session import get_parent_session_id
        parent = get_parent_session_id()
        if parent:
            related.append({
                'session_id': parent,
                'agent': 'parent',
                'task': 'Parent session',
                'parent_session_id': None
            })
        
        sessions = related if related else sessions
    
    # Build graph
    graph = _build_session_graph(sessions)
    
    # Detect cascades
    cascades = _detect_cascade_failures(graph)
    
    # Render
    if format == "agent_readable":
        return _render_flow_text(graph, cascades)
    else:
        return json.dumps({'graph': graph, 'cascades': cascades}, indent=2, default=str)


def get_cascade_summary(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a quick summary of any failure cascades.
    
    Args:
        session_id: Session to check (default: current)
        
    Returns:
        Summary dict with cascade information
    """
    flow_text = visualize_agent_flow(session_id)
    
    # Parse for key info
    has_cascade = "FAILURE CASCADES" in flow_text and "Chain:" in flow_text
    
    return {
        'has_cascade': has_cascade,
        'summary': "Multi-agent cascade detected" if has_cascade else "No cascade detected",
        'full_analysis': flow_text if has_cascade else None,
        'recommendation': (
            "Check upstream sessions for data corruption" 
            if has_cascade 
            else "Single session issue - analyze directly"
        )
    }
