"""Tests for BigQuery tools."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from tools.bigquery_tools import validate_sql_query


class TestValidateSqlQuery:
    """Test SQL query validation."""
    
    def test_valid_select_query(self):
        """Test that valid SELECT queries pass validation."""
        query = "SELECT * FROM `bigquery-public-data.thelook_ecommerce.orders` LIMIT 10"
        is_valid, error = validate_sql_query(query)
        assert is_valid is True
        assert error is None
    
    def test_select_with_joins(self):
        """Test SELECT with JOIN passes validation."""
        query = """
        SELECT o.order_id, u.name
        FROM `bigquery-public-data.thelook_ecommerce.orders` o
        JOIN `bigquery-public-data.thelook_ecommerce.users` u
        ON o.user_id = u.id
        """
        is_valid, error = validate_sql_query(query)
        assert is_valid is True
        assert error is None
    
    def test_drop_query_rejected(self):
        """Test that DROP queries are rejected."""
        query = "DROP TABLE orders"
        is_valid, error = validate_sql_query(query)
        assert is_valid is False
        assert "dangerous keyword" in error.lower()
    
    def test_delete_query_rejected(self):
        """Test that DELETE queries are rejected."""
        query = "DELETE FROM orders WHERE id = 1"
        is_valid, error = validate_sql_query(query)
        assert is_valid is False
        assert "dangerous keyword" in error.lower()
    
    def test_insert_query_rejected(self):
        """Test that INSERT queries are rejected."""
        query = "INSERT INTO orders VALUES (1, 2, 3)"
        is_valid, error = validate_sql_query(query)
        assert is_valid is False
        assert "dangerous keyword" in error.lower()
    
    def test_update_query_rejected(self):
        """Test that UPDATE queries are rejected."""
        query = "UPDATE orders SET status = 'completed'"
        is_valid, error = validate_sql_query(query)
        assert is_valid is False
        assert "dangerous keyword" in error.lower()
    
    def test_non_select_query_rejected(self):
        """Test that non-SELECT queries are rejected."""
        query = "SHOW TABLES"
        is_valid, error = validate_sql_query(query)
        assert is_valid is False
        assert "must be a select statement" in error.lower()
    
    def test_unbalanced_parentheses_rejected(self):
        """Test that queries with unbalanced parentheses are rejected."""
        query = "SELECT * FROM orders WHERE (id = 1"
        is_valid, error = validate_sql_query(query)
        assert is_valid is False
        assert "unbalanced parentheses" in error.lower()
    
    def test_case_insensitive_validation(self):
        """Test that validation is case-insensitive."""
        query = "select * from orders"
        is_valid, error = validate_sql_query(query)
        assert is_valid is True
        assert error is None


class TestSchemaFormatting:
    """Test schema formatting functions."""
    
    def test_get_schema_context_string(self):
        """Test schema context string formatting."""
        from prompts.system_prompts import get_schema_context_string
        
        schema_dict = {
            "orders": [
                {"name": "order_id", "type": "INTEGER", "description": "Order ID"},
                {"name": "user_id", "type": "INTEGER", "description": "User ID"}
            ],
            "products": [
                {"name": "id", "type": "INTEGER", "description": "Product ID"},
                {"name": "name", "type": "STRING", "description": "Product name"}
            ]
        }
        
        result = get_schema_context_string(schema_dict)
        
        assert "Table: orders" in result
        assert "Table: products" in result
        assert "order_id (INTEGER)" in result
        assert "name (STRING)" in result
        assert "Order ID" in result
        assert "Product name" in result

