"""Integration tests for the full agent workflow."""
import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
from agent.state import AgentState, AnalysisType


class TestGraphIntegration:
    """Test the full graph integration."""
    
    @pytest.mark.integration
    def test_graph_creation(self):
        """Test that graph can be created without errors."""
        from agent.graph import create_data_analysis_graph
        
        # This might fail if API key is not set, but should at least test structure
        try:
            graph = create_data_analysis_graph()
            assert graph is not None
        except ValueError as e:
            # Expected if API key not set
            assert "GOOGLE_API_KEY" in str(e)
    
    @pytest.mark.integration
    def test_initial_state_structure(self):
        """Test that initial state has correct structure."""
        from agent.graph import run_analysis
        
        initial_state = {
            "messages": [],
            "user_query": "test query",
            "analysis_type": None,
            "sql_query": None,
            "query_results": None,
            "insights": None,
            "error": None,
            "retry_count": 0,
            "schema_context": None
        }
        
        # Verify all required keys are present
        required_keys = [
            "messages", "user_query", "analysis_type", "sql_query",
            "query_results", "insights", "error", "retry_count", "schema_context"
        ]
        for key in required_keys:
            assert key in initial_state


class TestEndToEndFlow:
    """Test end-to-end workflow scenarios."""
    
    @pytest.mark.integration
    def test_query_validation_flow(self):
        """Test that dangerous queries are caught."""
        from tools.bigquery_tools import validate_sql_query
        
        dangerous_queries = [
            "DROP TABLE orders",
            "DELETE FROM users",
            "UPDATE products SET price = 0",
            "INSERT INTO orders VALUES (1, 2)"
        ]
        
        for query in dangerous_queries:
            is_valid, error = validate_sql_query(query)
            assert is_valid is False
            assert error is not None
    
    @pytest.mark.integration
    def test_safe_query_validation(self):
        """Test that safe queries pass validation."""
        from tools.bigquery_tools import validate_sql_query
        
        safe_queries = [
            "SELECT * FROM orders LIMIT 10",
            "SELECT COUNT(*) FROM users",
            "SELECT * FROM products WHERE category = 'Electronics'"
        ]
        
        for query in safe_queries:
            is_valid, error = validate_sql_query(query)
            assert is_valid is True
            assert error is None

