"""Tests for agent state management."""
import pytest
from agent.state import AgentState, AnalysisType


class TestAnalysisType:
    """Test AnalysisType constants and methods."""
    
    def test_all_types_returns_list(self):
        """Test that all_types returns a list of analysis types."""
        types = AnalysisType.all_types()
        assert isinstance(types, list)
        assert len(types) == 5
    
    def test_all_types_contains_expected_values(self):
        """Test that all expected analysis types are present."""
        types = AnalysisType.all_types()
        assert AnalysisType.CUSTOMER_SEGMENTATION in types
        assert AnalysisType.PRODUCT_PERFORMANCE in types
        assert AnalysisType.SALES_TRENDS in types
        assert AnalysisType.GEOGRAPHIC_PATTERNS in types
        assert AnalysisType.GENERAL_QUERY in types
    
    def test_analysis_type_constants(self):
        """Test that analysis type constants have correct values."""
        assert AnalysisType.CUSTOMER_SEGMENTATION == "customer_segmentation"
        assert AnalysisType.PRODUCT_PERFORMANCE == "product_performance"
        assert AnalysisType.SALES_TRENDS == "sales_trends"
        assert AnalysisType.GEOGRAPHIC_PATTERNS == "geographic_patterns"
        assert AnalysisType.GENERAL_QUERY == "general_query"


class TestAgentState:
    """Test AgentState TypedDict."""
    
    def test_state_structure(self):
        """Test that AgentState has all required fields."""
        # Create a minimal valid state
        state: AgentState = {
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
        
        # Verify all fields are present
        assert "messages" in state
        assert "user_query" in state
        assert "analysis_type" in state
        assert "sql_query" in state
        assert "query_results" in state
        assert "insights" in state
        assert "error" in state
        assert "retry_count" in state
        assert "schema_context" in state

