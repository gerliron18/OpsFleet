"""Graph node implementations for the LangGraph data analysis agent."""
import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agent.state import AgentState, AnalysisType
from prompts.system_prompts import (
    INTENT_ANALYSIS_PROMPT,
    SQL_GENERATION_PROMPT,
    INSIGHT_GENERATION_PROMPT,
    ERROR_RECOVERY_PROMPT,
    get_schema_context_string,
    format_dataframe_for_prompt
)
from tools.bigquery_tools import (
    execute_query_direct,
    get_all_table_schemas,
    validate_sql_query
)


def analyze_request_node(state: AgentState, llm) -> Dict[str, Any]:
    """Analyze user request to determine analysis type and intent.
    
    Args:
        state: Current agent state
        llm: Language model instance
        
    Returns:
        Updated state with analysis_type
    """
    logging.info("Node: analyze_request - Determining user intent")
    
    user_query = state["user_query"]
    
    # Create messages for intent classification
    # Gemini requires HumanMessage, not just SystemMessage
    combined_prompt = f"{INTENT_ANALYSIS_PROMPT}\n\nUser Query: {user_query}"
    messages = [
        HumanMessage(content=combined_prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        analysis_type = response.content.strip().lower()
        
        # Validate analysis type
        valid_types = AnalysisType.all_types()
        if analysis_type not in valid_types:
            logging.warning(f"Invalid analysis type '{analysis_type}', defaulting to general_query")
            analysis_type = AnalysisType.GENERAL_QUERY
        
        logging.info(f"Determined analysis type: {analysis_type}")
        
        return {
            "analysis_type": analysis_type,
            "error": None
        }
    
    except Exception as e:
        logging.error(f"Error in analyze_request: {e}")
        return {
            "analysis_type": AnalysisType.GENERAL_QUERY,
            "error": f"Intent analysis error: {str(e)}"
        }


def generate_sql_node(state: AgentState, llm) -> Dict[str, Any]:
    """Generate SQL query based on user request and analysis type.
    
    Args:
        state: Current agent state
        llm: Language model instance
        
    Returns:
        Updated state with sql_query
    """
    logging.info("Node: generate_sql - Creating BigQuery SQL")
    
    user_query = state["user_query"]
    analysis_type = state.get("analysis_type", AnalysisType.GENERAL_QUERY)
    
    # Get schema context if not cached
    schema_context = state.get("schema_context")
    if not schema_context:
        try:
            schema_context = get_all_table_schemas()
            logging.info("Retrieved table schemas")
        except Exception as e:
            logging.error(f"Failed to get schemas: {e}")
            return {
                "error": f"Schema retrieval error: {str(e)}",
                "sql_query": None
            }
    
    # Format schema for prompt
    schema_string = get_schema_context_string(schema_context)
    
    # Check if this is a retry with error recovery
    failed_query = state.get("sql_query") if state.get("error") else None
    error_message = state.get("error") if failed_query else None
    
    if failed_query and error_message:
        logging.info("Attempting SQL error recovery")
        prompt = ERROR_RECOVERY_PROMPT.format(
            error_message=error_message,
            failed_query=failed_query,
            user_query=user_query
        )
        messages = [HumanMessage(content=prompt)]
    else:
        # Normal SQL generation
        prompt = SQL_GENERATION_PROMPT.format(
            schema_context=schema_string,
            user_query=user_query,
            analysis_type=analysis_type
        )
        messages = [HumanMessage(content=prompt)]
    
    try:
        response = llm.invoke(messages)
        sql_query = response.content.strip()
        
        # Clean up any markdown formatting
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        elif sql_query.startswith("```"):
            sql_query = sql_query.replace("```", "").strip()
        
        # Validate query
        is_valid, validation_error = validate_sql_query(sql_query)
        if not is_valid:
            logging.error(f"SQL validation failed: {validation_error}")
            return {
                "error": f"Invalid SQL: {validation_error}",
                "sql_query": sql_query
            }
        
        logging.info(f"Generated SQL query: {sql_query[:100]}...")
        
        return {
            "sql_query": sql_query,
            "schema_context": schema_context,
            "error": None
        }
    
    except Exception as e:
        logging.error(f"Error in generate_sql: {e}")
        return {
            "error": f"SQL generation error: {str(e)}",
            "sql_query": None
        }


def execute_query_node(state: AgentState) -> Dict[str, Any]:
    """Execute the generated SQL query on BigQuery.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with query_results
    """
    logging.info("Node: execute_query - Running BigQuery query")
    
    sql_query = state.get("sql_query")
    
    if not sql_query:
        return {
            "error": "No SQL query to execute",
            "query_results": None
        }
    
    try:
        df = execute_query_direct(sql_query)
        logging.info(f"Query executed successfully: {len(df)} rows returned")
        
        return {
            "query_results": df,
            "error": None,
            "retry_count": 0
        }
    
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Query execution failed: {error_msg}")
        
        retry_count = state.get("retry_count", 0)
        
        return {
            "error": f"Query execution error: {error_msg}",
            "query_results": None,
            "retry_count": retry_count + 1
        }


def analyze_results_node(state: AgentState, llm) -> Dict[str, Any]:
    """Analyze query results and generate business insights.
    
    Args:
        state: Current agent state
        llm: Language model instance
        
    Returns:
        Updated state with insights
    """
    logging.info("Node: analyze_results - Generating insights")
    
    user_query = state["user_query"]
    analysis_type = state.get("analysis_type", "general")
    sql_query = state.get("sql_query", "")
    query_results = state.get("query_results")
    
    if query_results is None or query_results.empty:
        return {
            "insights": "No data was returned from the query. The requested analysis could not be completed.",
            "error": None
        }
    
    # Format results for prompt
    results_string = format_dataframe_for_prompt(query_results)
    
    # Generate insights
    prompt = INSIGHT_GENERATION_PROMPT.format(
        user_query=user_query,
        analysis_type=analysis_type,
        sql_query=sql_query,
        query_results=results_string
    )
    
    messages = [HumanMessage(content=prompt)]
    
    try:
        response = llm.invoke(messages)
        insights = response.content.strip()
        
        logging.info("Insights generated successfully")
        
        return {
            "insights": insights,
            "error": None
        }
    
    except Exception as e:
        logging.error(f"Error in analyze_results: {e}")
        # Provide basic insights as fallback
        fallback_insights = f"Query executed successfully and returned {len(query_results)} rows. "
        fallback_insights += f"Columns: {', '.join(query_results.columns.tolist())}. "
        fallback_insights += "However, detailed analysis could not be generated due to an error."
        
        return {
            "insights": fallback_insights,
            "error": f"Insight generation error: {str(e)}"
        }


def respond_node(state: AgentState) -> Dict[str, Any]:
    """Format and prepare final response to user.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with formatted response message
    """
    logging.info("Node: respond - Formatting final response")
    
    insights = state.get("insights", "")
    error = state.get("error")
    query_results = state.get("query_results")
    
    # Build response message
    if error and not insights:
        # Complete failure
        response_content = f"I apologize, but I encountered an error processing your request:\n\n{error}\n\n"
        response_content += "Please try rephrasing your question or ask something else."
    elif error and insights:
        # Partial success
        response_content = insights
        response_content += f"\n\n(Note: There was a minor issue: {error})"
    else:
        # Full success
        response_content = insights
    
    # Add data summary if results exist
    if query_results is not None and not query_results.empty:
        response_content += f"\n\n---\nData Summary: {len(query_results)} rows analyzed"
    
    response_message = AIMessage(content=response_content)
    
    return {
        "messages": [response_message]
    }


def should_retry_query(state: AgentState) -> bool:
    """Determine if query should be retried after failure.
    
    Args:
        state: Current agent state
        
    Returns:
        True if should retry, False otherwise
    """
    error = state.get("error")
    retry_count = state.get("retry_count", 0)
    max_retries = 2
    
    # Only retry if there's an error and haven't exceeded max retries
    if error and retry_count < max_retries:
        # Check if it's a retryable error (SQL errors, not auth errors)
        error_lower = error.lower()
        non_retryable = ["permission", "authentication", "credentials", "quota"]
        
        for term in non_retryable:
            if term in error_lower:
                logging.info(f"Non-retryable error detected: {term}")
                return False
        
        logging.info(f"Retry attempt {retry_count + 1}/{max_retries}")
        return True
    
    return False

