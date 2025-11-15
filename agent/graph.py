"""LangGraph state graph construction for the data analysis agent."""
import logging
from typing import Literal
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    analyze_request_node,
    generate_sql_node,
    execute_query_node,
    analyze_results_node,
    respond_node,
    should_retry_query
)
from llm.gemini_client import get_gemini_model


def create_data_analysis_graph(model_name: str = "gemini-2.5-flash"):
    """Create and compile the LangGraph state graph for data analysis.
    
    The graph flow:
    1. analyze_request: Determine user intent and analysis type
    2. generate_sql: Create SQL query based on intent
    3. execute_query: Run query on BigQuery
    4. Conditional routing:
       - If error and can retry: loop back to generate_sql
       - If success: proceed to analyze_results
       - If max retries exceeded: proceed to respond with error
    5. analyze_results: Generate business insights from data
    6. respond: Format final response to user
    
    Args:
        model_name: Gemini model to use for LLM operations
        
    Returns:
        Compiled StateGraph ready for execution
    """
    logging.info(f"Creating LangGraph with model: {model_name}")
    
    # Initialize LLM
    llm = get_gemini_model(model_name=model_name, temperature=0.1)
    
    # Create state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes with LLM binding where needed
    workflow.add_node("analyze_request", lambda state: analyze_request_node(state, llm))
    workflow.add_node("generate_sql", lambda state: generate_sql_node(state, llm))
    workflow.add_node("execute_query", execute_query_node)
    workflow.add_node("analyze_results", lambda state: analyze_results_node(state, llm))
    workflow.add_node("respond", respond_node)
    
    # Define the routing logic after query execution
    def route_after_execution(state: AgentState) -> Literal["generate_sql", "analyze_results", "respond"]:
        """Route after query execution based on success/failure.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node to execute
        """
        error = state.get("error")
        query_results = state.get("query_results")
        
        # Check if we should retry
        if error and should_retry_query(state):
            logging.info("Routing to generate_sql for retry")
            return "generate_sql"
        
        # If we have results, analyze them
        if query_results is not None:
            logging.info("Routing to analyze_results")
            return "analyze_results"
        
        # If error and can't retry, go to respond
        if error:
            logging.info("Routing to respond with error")
            return "respond"
        
        # Default: analyze results
        logging.info("Routing to analyze_results (default)")
        return "analyze_results"
    
    # Set entry point
    workflow.set_entry_point("analyze_request")
    
    # Add edges
    workflow.add_edge("analyze_request", "generate_sql")
    workflow.add_edge("generate_sql", "execute_query")
    
    # Conditional edge after query execution
    workflow.add_conditional_edges(
        "execute_query",
        route_after_execution,
        {
            "generate_sql": "generate_sql",  # Retry SQL generation
            "analyze_results": "analyze_results",  # Success path
            "respond": "respond"  # Error path
        }
    )
    
    workflow.add_edge("analyze_results", "respond")
    workflow.add_edge("respond", END)
    
    # Compile the graph
    app = workflow.compile()
    
    logging.info("LangGraph compiled successfully")
    return app


def run_analysis(
    user_query: str,
    graph,
    verbose: bool = False
) -> dict:
    """Run the data analysis agent on a user query.
    
    Args:
        user_query: The user's question or request
        graph: Compiled LangGraph instance
        verbose: Whether to log detailed progress
        
    Returns:
        Final state dictionary with results
    """
    if verbose:
        logging.info(f"Processing query: {user_query}")
    
    # Initialize state
    initial_state = {
        "messages": [],
        "user_query": user_query,
        "analysis_type": None,
        "sql_query": None,
        "query_results": None,
        "insights": None,
        "error": None,
        "retry_count": 0,
        "schema_context": None
    }
    
    try:
        # Run the graph
        final_state = graph.invoke(initial_state)
        
        if verbose:
            logging.info("Query processing completed")
        
        return final_state
    
    except Exception as e:
        logging.error(f"Error running analysis: {e}")
        return {
            **initial_state,
            "error": f"Agent execution error: {str(e)}",
            "messages": []
        }


def get_response_from_state(state: dict) -> str:
    """Extract the response message from final state.
    
    Args:
        state: Final state dictionary from graph execution
        
    Returns:
        Response text for the user
    """
    messages = state.get("messages", [])
    if messages:
        # Get the last AI message
        for msg in reversed(messages):
            if hasattr(msg, 'content'):
                return msg.content
    
    # Fallback if no messages
    error = state.get("error")
    if error:
        return f"An error occurred: {error}"
    
    return "I couldn't process your request. Please try again."

