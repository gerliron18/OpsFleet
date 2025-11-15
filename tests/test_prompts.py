"""Tests for system prompts."""
import pytest
import pandas as pd
from prompts.system_prompts import (
    INTENT_ANALYSIS_PROMPT,
    SQL_GENERATION_PROMPT,
    INSIGHT_GENERATION_PROMPT,
    ERROR_RECOVERY_PROMPT,
    get_schema_context_string,
    format_dataframe_for_prompt
)


class TestPromptConstants:
    """Test that prompt constants are defined."""
    
    def test_intent_analysis_prompt_exists(self):
        """Test INTENT_ANALYSIS_PROMPT is defined and non-empty."""
        assert INTENT_ANALYSIS_PROMPT
        assert len(INTENT_ANALYSIS_PROMPT) > 100
        assert "customer_segmentation" in INTENT_ANALYSIS_PROMPT
        assert "product_performance" in INTENT_ANALYSIS_PROMPT
    
    def test_sql_generation_prompt_exists(self):
        """Test SQL_GENERATION_PROMPT is defined and non-empty."""
        assert SQL_GENERATION_PROMPT
        assert len(SQL_GENERATION_PROMPT) > 100
        assert "{schema_context}" in SQL_GENERATION_PROMPT
        assert "{user_query}" in SQL_GENERATION_PROMPT
    
    def test_insight_generation_prompt_exists(self):
        """Test INSIGHT_GENERATION_PROMPT is defined and non-empty."""
        assert INSIGHT_GENERATION_PROMPT
        assert len(INSIGHT_GENERATION_PROMPT) > 100
        assert "{query_results}" in INSIGHT_GENERATION_PROMPT
        assert "{user_query}" in INSIGHT_GENERATION_PROMPT
    
    def test_error_recovery_prompt_exists(self):
        """Test ERROR_RECOVERY_PROMPT is defined and non-empty."""
        assert ERROR_RECOVERY_PROMPT
        assert len(ERROR_RECOVERY_PROMPT) > 50
        assert "{error_message}" in ERROR_RECOVERY_PROMPT
        assert "{failed_query}" in ERROR_RECOVERY_PROMPT


class TestFormatDataframeForPrompt:
    """Test DataFrame formatting for prompts."""
    
    def test_format_empty_dataframe(self):
        """Test formatting an empty DataFrame."""
        df = pd.DataFrame()
        result = format_dataframe_for_prompt(df)
        assert "No data returned" in result
    
    def test_format_none_dataframe(self):
        """Test formatting None as DataFrame."""
        result = format_dataframe_for_prompt(None)
        assert "No data returned" in result
    
    def test_format_small_dataframe(self):
        """Test formatting a small DataFrame."""
        df = pd.DataFrame({
            'product': ['A', 'B', 'C'],
            'sales': [100, 200, 300]
        })
        result = format_dataframe_for_prompt(df)
        
        assert "3 rows" in result
        assert "2 columns" in result
        assert "product" in result
        assert "sales" in result
    
    def test_format_large_dataframe(self):
        """Test formatting a large DataFrame with truncation."""
        df = pd.DataFrame({
            'id': range(100),
            'value': range(100, 200)
        })
        result = format_dataframe_for_prompt(df, max_rows=10)
        
        assert "100 rows" in result
        assert "Showing first 10 rows" in result
        assert "90 more rows" in result
    
    def test_format_dataframe_with_columns(self):
        """Test that column names are included."""
        df = pd.DataFrame({
            'order_id': [1, 2, 3],
            'user_id': [10, 20, 30],
            'amount': [50.0, 75.5, 100.0]
        })
        result = format_dataframe_for_prompt(df)
        
        assert "order_id" in result
        assert "user_id" in result
        assert "amount" in result


class TestGetSchemaContextString:
    """Test schema context string generation."""
    
    def test_empty_schema(self):
        """Test formatting an empty schema."""
        schema_dict = {}
        result = get_schema_context_string(schema_dict)
        assert result == ""
    
    def test_single_table_schema(self):
        """Test formatting a single table schema."""
        schema_dict = {
            "orders": [
                {"name": "id", "type": "INTEGER", "description": "Order ID"},
                {"name": "total", "type": "FLOAT", "description": "Order total"}
            ]
        }
        result = get_schema_context_string(schema_dict)
        
        assert "Table: orders" in result
        assert "id (INTEGER)" in result
        assert "total (FLOAT)" in result
        assert "Order ID" in result
        assert "Order total" in result
    
    def test_multiple_tables_schema(self):
        """Test formatting multiple tables."""
        schema_dict = {
            "orders": [
                {"name": "id", "type": "INTEGER", "description": ""}
            ],
            "products": [
                {"name": "name", "type": "STRING", "description": "Product name"}
            ]
        }
        result = get_schema_context_string(schema_dict)
        
        assert "Table: orders" in result
        assert "Table: products" in result
        assert "id (INTEGER)" in result
        assert "name (STRING)" in result
    
    def test_field_without_description(self):
        """Test formatting fields without descriptions."""
        schema_dict = {
            "test": [
                {"name": "field1", "type": "STRING", "description": None},
                {"name": "field2", "type": "INTEGER", "description": ""}
            ]
        }
        result = get_schema_context_string(schema_dict)
        
        assert "field1 (STRING)" in result
        assert "field2 (INTEGER)" in result

