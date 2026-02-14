"""
Tests for remote sync module (Phase 4).
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from agentlog._remote import (
    _get_d1_config,
    is_d1_enabled,
    D1Client,
    init_d1_schema,
    list_d1_sessions,
    delete_d1_session,
    share_session,
    import_shared_session,
)


class TestD1Config:
    """Test D1 configuration."""
    
    def test_get_d1_config_all_set(self):
        """Get config when all env vars set."""
        with patch.dict(os.environ, {
            "CLOUDFLARE_ACCOUNT_ID": "acct_123",
            "CLOUDFLARE_D1_DATABASE_ID": "db_456",
            "CLOUDFLARE_API_TOKEN": "token_789"
        }):
            config = _get_d1_config()
            assert config is not None
            assert config["account_id"] == "acct_123"
            assert config["database_id"] == "db_456"
            assert config["api_token"] == "token_789"
    
    def test_get_d1_config_missing_vars(self):
        """Get config when env vars missing."""
        with patch.dict(os.environ, {}, clear=True):
            config = _get_d1_config()
            assert config is None
    
    def test_is_d1_enabled_true(self):
        """D1 enabled when config present."""
        with patch.dict(os.environ, {
            "CLOUDFLARE_ACCOUNT_ID": "acct_123",
            "CLOUDFLARE_D1_DATABASE_ID": "db_456",
            "CLOUDFLARE_API_TOKEN": "token_789"
        }):
            assert is_d1_enabled() is True
    
    def test_is_d1_enabled_false(self):
        """D1 disabled when config missing."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_d1_enabled() is False


class TestD1Client:
    """Test D1 API client."""
    
    def test_client_initialization(self):
        """Create D1 client."""
        client = D1Client("acct_123", "db_456", "token_789")
        
        assert client.account_id == "acct_123"
        assert client.database_id == "db_456"
        assert client.api_token == "token_789"
        assert "api.cloudflare.com" in client.base_url
    
    def test_client_query_error_handling(self):
        """Client handles query errors."""
        client = D1Client("acct_123", "db_456", "token_789")
        
        # Mock urllib to return error
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = b'{"error": "test error"}'
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            result = client.query("SELECT 1")
            # Should return parsed JSON
            assert result is not None


class TestD1Operations:
    """Test D1 operations without real API calls."""
    
    def test_init_schema_no_config(self):
        """Schema init fails without config."""
        with patch.dict(os.environ, {}, clear=True):
            result = init_d1_schema()
            assert result is False
    
    def test_list_sessions_no_config(self):
        """List sessions returns empty without config."""
        with patch.dict(os.environ, {}, clear=True):
            sessions = list_d1_sessions()
            assert sessions == []
    
    def test_delete_session_no_config(self):
        """Delete session fails without config."""
        with patch.dict(os.environ, {}, clear=True):
            result = delete_d1_session("sess_123")
            assert result is False
    
    def test_share_session_no_config(self):
        """Share session returns None without config."""
        with patch.dict(os.environ, {}, clear=True):
            result = share_session("sess_123")
            assert result is None
    
    def test_import_shared_session_no_config(self):
        """Import session returns None without config."""
        with patch.dict(os.environ, {}, clear=True):
            result = import_shared_session("sess_123")
            assert result is None


class TestD1Schema:
    """Test D1 schema SQL."""
    
    def test_schema_contains_required_tables(self):
        """Schema creates required tables."""
        from agentlog._remote import D1_SCHEMA
        
        assert "agentlog_sessions" in D1_SCHEMA
        assert "agentlog_events" in D1_SCHEMA
        assert "agentlog_outcomes" in D1_SCHEMA
    
    def test_schema_contains_indexes(self):
        """Schema creates indexes."""
        from agentlog._remote import D1_SCHEMA
        
        assert "idx_events_session" in D1_SCHEMA
        assert "idx_events_tag" in D1_SCHEMA
