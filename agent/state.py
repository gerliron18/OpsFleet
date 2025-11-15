"""State definitions for the LangGraph data analysis agent."""
import operator
from typing import Annotated, TypedDict, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage
import pandas as pd


class AgentState(TypedDict):
    """State for the data analysis agent.
    
    Attributes:
        messages: Chat history with user and assistant messages
        user_query: Current user query being processed
        analysis_type: Type of analysis requested (segmentation, product, trends, geographic)
        sql_query: Generated SQL query for BigQuery
        query_results: DataFrame results from BigQuery execution
        insights: Generated insights from data analysis
        error: Error message if any step fails
        retry_count: Number of retries attempted for current operation
        schema_context: Cached table schema information
    """
    messages: Annotated[List[BaseMessage], operator.add]
    user_query: str
    analysis_type: Optional[str]
    sql_query: Optional[str]
    query_results: Optional[pd.DataFrame]
    insights: Optional[str]
    error: Optional[str]
    retry_count: int
    schema_context: Optional[Dict[str, Any]]


class AnalysisType:
    """Constants for different analysis types."""
    CUSTOMER_SEGMENTATION = "customer_segmentation"
    PRODUCT_PERFORMANCE = "product_performance"
    SALES_TRENDS = "sales_trends"
    GEOGRAPHIC_PATTERNS = "geographic_patterns"
    GENERAL_QUERY = "general_query"
    
    @classmethod
    def all_types(cls) -> List[str]:
        """Return all available analysis types."""
        return [
            cls.CUSTOMER_SEGMENTATION,
            cls.PRODUCT_PERFORMANCE,
            cls.SALES_TRENDS,
            cls.GEOGRAPHIC_PATTERNS,
            cls.GENERAL_QUERY
        ]

