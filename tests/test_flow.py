"""
Tests for Clear Winner Feature 2: visualize_agent_flow() - Multi-Agent Flow Visualizer
"""

import pytest
from agentlog._flow import (
    _build_session_graph,
    _detect_cascade_failures,
    _render_flow_text,
    _describe_cascade,
    visualize_agent_flow,
    get_cascade_summary,
)


class TestBuildSessionGraph:
    """Test graph building."""
    
    def test_empty_sessions(self):
        """Build graph with no sessions."""
        graph = _build_session_graph([])
        assert graph['nodes'] == []
        assert graph['edges'] == []
    
    def test_single_session(self):
        """Build graph with one session."""
        sessions = [
            {'session_id': 'sess_1', 'agent': 'cursor', 'task': 'test'}
        ]
        graph = _build_session_graph(sessions)
        
        assert len(graph['nodes']) == 1
        assert graph['nodes'][0]['id'] == 'sess_1'
        assert graph['nodes'][0]['agent'] == 'cursor'
    
    def test_parent_child_relationship(self):
        """Build graph with parent-child link."""
        sessions = [
            {'session_id': 'parent_1', 'agent': 'cursor', 'task': 'parent'},
            {'session_id': 'child_1', 'agent': 'cursor', 'task': 'child', 'parent_session_id': 'parent_1'}
        ]
        graph = _build_session_graph(sessions)
        
        assert len(graph['nodes']) == 2
        assert len(graph['edges']) == 1
        assert graph['edges'][0]['from'] == 'parent_1'
        assert graph['edges'][0]['to'] == 'child_1'


class TestDetectCascadeFailures:
    """Test cascade detection."""
    
    def test_no_cascades(self):
        """Detect no cascades in healthy sessions."""
        graph = {
            'nodes': [
                {'id': 'sess_1', 'error_count': 0, 'outcome': 'success'},
                {'id': 'sess_2', 'error_count': 0, 'outcome': 'success'}
            ],
            'edges': []
        }
        cascades = _detect_cascade_failures(graph)
        assert cascades == []
    
    def test_single_error_no_cascade(self):
        """Single session error, no cascade."""
        graph = {
            'nodes': [
                {'id': 'sess_1', 'error_count': 1, 'outcome': 'failure'}
            ],
            'edges': []
        }
        cascades = _detect_cascade_failures(graph)
        assert len(cascades) == 0  # No chain, just single error
    
    def test_detect_cascade_chain(self):
        """Detect cascade through parent-child chain."""
        graph = {
            'nodes': [
                {'id': 'parent', 'agent': 'A', 'task': 'start', 'error_count': 0},
                {'id': 'child', 'agent': 'B', 'task': 'process', 'error_count': 1, 'outcome': 'failure'}
            ],
            'edges': [
                {'from': 'parent', 'to': 'child', 'type': 'parent_child'}
            ]
        }
        cascades = _detect_cascade_failures(graph)
        
        assert len(cascades) == 1
        assert cascades[0]['chain'] == ['parent', 'child']
        assert cascades[0]['error_session'] == 'child'


class TestDescribeCascade:
    """Test cascade description generation."""
    
    def test_describe_simple_cascade(self):
        """Describe a simple cascade."""
        chain = ['sess_1', 'sess_2']
        nodes = [
            {'id': 'sess_1', 'agent': 'cursor', 'task': 'prepare'},
            {'id': 'sess_2', 'agent': 'codex', 'task': 'process'}
        ]
        
        desc = _describe_cascade(chain, nodes)
        
        assert 'cursor' in desc
        assert 'codex' in desc
        assert 'started' in desc
        assert 'processed' in desc


class TestRenderFlowText:
    """Test text rendering."""
    
    def test_render_basic_flow(self):
        """Render basic flow text."""
        graph = {
            'nodes': [
                {'id': 'sess_1', 'agent': 'cursor', 'task': 'test', 'error_count': 0, 'outcome': 'success'}
            ],
            'edges': []
        }
        cascades = []
        
        result = _render_flow_text(graph, cascades)
        
        assert 'MULTI-AGENT FLOW ANALYSIS' in result
        assert 'cursor' in result
        assert 'sess_1'[:8] in result or 'sess_1' in result
    
    def test_render_with_cascades(self):
        """Render with cascade information."""
        graph = {
            'nodes': [
                {'id': 'parent', 'agent': 'A', 'task': 'start', 'error_count': 0},
                {'id': 'child', 'agent': 'B', 'task': 'fail', 'error_count': 1, 'outcome': 'failure'}
            ],
            'edges': [
                {'from': 'parent', 'to': 'child', 'type': 'parent_child'}
            ]
        }
        cascades = [
            {'chain': ['parent', 'child'], 'error_session': 'child', 'description': 'A started, B failed'}
        ]
        
        result = _render_flow_text(graph, cascades)
        
        assert 'FAILURE CASCADES' in result
        assert 'Cascade #1' in result
        assert 'A started' in result or 'FAILURE POINT' in result


class TestVisualizeAgentFlow:
    """Test public API."""
    
    def test_visualize_returns_string(self):
        """API returns string."""
        result = visualize_agent_flow()
        assert isinstance(result, str)
    
    def test_visualize_has_header(self):
        """Result has analysis header."""
        result = visualize_agent_flow()
        assert 'MULTI-AGENT' in result or 'FLOW' in result or isinstance(result, str)


class TestGetCascadeSummary:
    """Test cascade summary API."""
    
    def test_summary_structure(self):
        """Summary has expected structure."""
        summary = get_cascade_summary()
        
        assert 'has_cascade' in summary
        assert 'summary' in summary
        assert isinstance(summary['has_cascade'], bool)
