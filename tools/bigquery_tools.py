"""LangGraph tool wrappers for BigQuery operations."""
import logging
from typing import Optional, Dict, Any, List
import pandas as pd
from langchain_core.tools import tool
from bq_client import BigQueryRunner


# Global BigQuery client instance
_bq_client: Optional[BigQueryRunner] = None


def initialize_bigquery_client(
    project_id: Optional[str] = None,
    dataset_id: str = "bigquery-public-data.thelook_ecommerce"
) -> BigQueryRunner:
    """Initialize or get the global BigQuery client.
    
    Args:
        project_id: GCP project ID (uses default credentials if None)
        dataset_id: BigQuery dataset ID
        
    Returns:
        BigQueryRunner instance
    """
    global _bq_client
    if _bq_client is None:
        _bq_client = BigQueryRunner(project_id=project_id, dataset_id=dataset_id)
        logging.info("BigQuery client initialized")
    return _bq_client


def get_bigquery_client() -> BigQueryRunner:
    """Get the initialized BigQuery client.
    
    Returns:
        BigQueryRunner instance
        
    Raises:
        RuntimeError: If client not initialized
    """
    if _bq_client is None:
        raise RuntimeError(
            "BigQuery client not initialized. Call initialize_bigquery_client() first."
        )
    return _bq_client


@tool
def execute_bigquery_query(sql_query: str) -> str:
    """Execute a SQL query on BigQuery and return results.
    
    This tool executes SQL queries against the BigQuery thelook_ecommerce dataset
    and returns the results as a formatted string representation.
    
    Args:
        sql_query: The SQL query to execute
        
    Returns:
        String representation of query results or error message
    """
    try:
        client = get_bigquery_client()
        df = client.execute_query(sql_query)
        
        if df.empty:
            return "Query executed successfully but returned no results."
        
        # Return formatted dataframe info
        result = f"Query returned {len(df)} rows and {len(df.columns)} columns.\n\n"
        result += f"Columns: {', '.join(df.columns.tolist())}\n\n"
        result += "Sample data (first 10 rows):\n"
        result += df.head(10).to_string(index=False)
        
        return result
    except Exception as e:
        error_msg = f"BigQuery execution error: {str(e)}"
        logging.error(error_msg)
        return error_msg


@tool
def get_table_schema_info(table_name: str) -> str:
    """Get schema information for a BigQuery table.
    
    Retrieves column names, types, and descriptions for the specified table
    in the thelook_ecommerce dataset.
    
    Args:
        table_name: Name of the table (orders, order_items, products, users)
        
    Returns:
        Formatted string with schema information or error message
    """
    try:
        client = get_bigquery_client()
        schema = client.get_table_schema(table_name)
        
        result = f"Schema for table '{table_name}':\n\n"
        for field in schema:
            result += f"- {field['name']} ({field['type']}, {field['mode']})"
            if field['description']:
                result += f": {field['description']}"
            result += "\n"
        
        return result
    except Exception as e:
        error_msg = f"Error retrieving schema for table '{table_name}': {str(e)}"
        logging.error(error_msg)
        return error_msg


def execute_query_direct(sql_query: str) -> pd.DataFrame:
    """Execute a query and return DataFrame directly (not as a tool).
    
    This is used internally by the agent nodes for data processing.
    
    Args:
        sql_query: The SQL query to execute
        
    Returns:
        DataFrame with query results
        
    Raises:
        Exception: If query execution fails
    """
    client = get_bigquery_client()
    return client.execute_query(sql_query)


def get_all_table_schemas() -> Dict[str, List[Dict[str, Any]]]:
    """Get schemas for all main tables in the dataset.
    
    Returns:
        Dictionary mapping table names to their schema information
    """
    client = get_bigquery_client()
    tables = ["orders", "order_items", "products", "users"]
    schemas = {}
    
    for table in tables:
        try:
            schemas[table] = client.get_table_schema(table)
            logging.info(f"Retrieved schema for table: {table}")
        except Exception as e:
            logging.error(f"Failed to get schema for {table}: {e}")
            schemas[table] = []
    
    return schemas


def validate_sql_query(sql_query: str) -> tuple[bool, Optional[str]]:
    """Basic validation of SQL query before execution.
    
    Args:
        sql_query: SQL query to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    sql_lower = sql_query.lower().strip()
    
    # Check for dangerous operations
    dangerous_keywords = ["drop", "delete", "truncate", "insert", "update", "alter", "create"]
    for keyword in dangerous_keywords:
        if keyword in sql_lower.split():
            return False, f"Query contains dangerous keyword: {keyword}. Only SELECT queries are allowed."
    
    # Must start with SELECT
    if not sql_lower.startswith("select"):
        return False, "Query must be a SELECT statement."
    
    # Basic syntax check
    if sql_lower.count("(") != sql_lower.count(")"):
        return False, "Unbalanced parentheses in query."
    
    return True, None


# Create list of tools for LangGraph
bigquery_tools = [execute_bigquery_query, get_table_schema_info]

