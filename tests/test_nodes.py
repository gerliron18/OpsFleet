"""Tests for agent nodes."""
import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
from langchain_core.messages import AIMessage
from agent.state import AgentState, AnalysisType
from agent.nodes import should_retry_query


class TestShouldRetryQuery:
    """Test retry logic for query execution."""
    
    def test_no_error_no_retry(self):
        """Test that successful queries don't trigger retry."""
        state: AgentState = {
            "messages": [],
            "user_query": "test",
            "analysis_type": None,
            "sql_query": None,
            "query_results": pd.DataFrame({"col": [1, 2, 3]}),
            "insights": None,
            "error": None,
            "retry_count": 0,
            "schema_context": None
        }
        assert should_retry_query(state) is False
    
    def test_error_within_retry_limit(self):
        """Test that errors within retry limit trigger retry."""
        state: AgentState = {
            "messages": [],
            "user_query": "test",
            "analysis_type": None,
            "sql_query": None,
            "query_results": None,
            "insights": None,
            "error": "SQL syntax error",
            "retry_count": 0,
            "schema_context": None
        }
        assert should_retry_query(state) is True
    
    def test_max_retries_exceeded(self):
        """Test that max retries prevents further attempts."""
        state: AgentState = {
            "messages": [],
            "user_query": "test",
            "analysis_type": None,
            "sql_query": None,
            "query_results": None,
            "insights": None,
            "error": "SQL syntax error",
            "retry_count": 2,
            "schema_context": None
        }
        assert should_retry_query(state) is False
    
    def test_authentication_error_no_retry(self):
        """Test that authentication errors don't trigger retry."""
        state: AgentState = {
            "messages": [],
            "user_query": "test",
            "analysis_type": None,
            "sql_query": None,
            "query_results": None,
            "insights": None,
            "error": "Authentication failed",
            "retry_count": 0,
            "schema_context": None
        }
        assert should_retry_query(state) is False
    
    def test_permission_error_no_retry(self):
        """Test that permission errors don't trigger retry."""
        state: AgentState = {
            "messages": [],
            "user_query": "test",
            "analysis_type": None,
            "sql_query": None,
            "query_results": None,
            "insights": None,
            "error": "Permission denied",
            "retry_count": 0,
            "schema_context": None
        }
        assert should_retry_query(state) is False
    
    def test_quota_error_no_retry(self):
        """Test that quota errors don't trigger retry."""
        state: AgentState = {
            "messages": [],
            "user_query": "test",
            "analysis_type": None,
            "sql_query": None,
            "query_results": None,
            "insights": None,
            "error": "Quota exceeded",
            "retry_count": 0,
            "schema_context": None
        }
        assert should_retry_query(state) is False
    
    def test_credentials_error_no_retry(self):
        """Test that credential errors don't trigger retry."""
        state: AgentState = {
            "messages": [],
            "user_query": "test",
            "analysis_type": None,
            "sql_query": None,
            "query_results": None,
            "insights": None,
            "error": "Invalid credentials",
            "retry_count": 0,
            "schema_context": None
        }
        assert should_retry_query(state) is False


class TestRespondNode:
    """Test respond node functionality."""
    
    def test_respond_with_success(self):
        """Test respond node with successful insights."""
        from agent.nodes import respond_node
        
        state: AgentState = {
            "messages": [],
            "user_query": "test query",
            "analysis_type": "product_performance",
            "sql_query": "SELECT * FROM products",
            "query_results": pd.DataFrame({"product": ["A", "B"]}),
            "insights": "Product A performs better than B",
            "error": None,
            "retry_count": 0,
            "schema_context": None
        }
        
        result = respond_node(state)
        
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)
        assert "Product A performs better than B" in result["messages"][0].content
    
    def test_respond_with_error(self):
        """Test respond node with error."""
        from agent.nodes import respond_node
        
        state: AgentState = {
            "messages": [],
            "user_query": "test query",
            "analysis_type": None,
            "sql_query": None,
            "query_results": None,
            "insights": None,
            "error": "Query execution failed",
            "retry_count": 2,
            "schema_context": None
        }
        
        result = respond_node(state)
        
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert "error" in result["messages"][0].content.lower()

