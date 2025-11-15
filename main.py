#!/usr/bin/env python3
"""Main CLI application for the Data Analysis LangGraph Agent."""
import os
import sys
import logging
from typing import Optional
from dotenv import load_dotenv
from agent.graph import create_data_analysis_graph, run_analysis, get_response_from_state
from tools.bigquery_tools import initialize_bigquery_client


# ASCII art banner
BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   📊 E-Commerce Data Analysis Agent 📊                        ║
║                                                               ║
║   Powered by LangGraph + Google Gemini + BigQuery            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""


def setup_logging(log_level: str = "INFO"):
    """Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_environment():
    """Load environment variables from .env file."""
    load_dotenv()
    
    # Validate required environment variables
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("\n❌ ERROR: GOOGLE_API_KEY not found in environment variables.")
        print("\nPlease create a .env file with your Google AI Studio API key:")
        print("  GOOGLE_API_KEY=your_api_key_here")
        print("\nGet your free API key from: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    logging.info("Environment variables loaded successfully")


def print_banner():
    """Print the application banner."""
    print(BANNER)
    print("Welcome! I can help you analyze e-commerce data from BigQuery.\n")
    print("Available analysis types:")
    print("  • Customer segmentation and behavior")
    print("  • Product performance and recommendations")
    print("  • Sales trends and seasonality")
    print("  • Geographic sales patterns")
    print("\nType your question or 'exit' to quit.\n")
    print("─" * 63)


def print_thinking():
    """Show thinking indicator."""
    print("\n🤔 Analyzing your question...", end="", flush=True)


def print_processing():
    """Show processing indicator."""
    print("\r🔍 Processing query...      ", end="", flush=True)


def print_response(response: str, state: dict):
    """Print formatted response to user.
    
    Args:
        response: The response text
        state: Final state from graph execution
    """
    print("\r" + " " * 30 + "\r", end="")  # Clear progress indicator
    
    print("\n" + "─" * 63)
    print("\n📊 Analysis Results:\n")
    print(response)
    
    # Show additional metadata if in debug mode
    if logging.getLogger().level == logging.DEBUG:
        print("\n" + "─" * 63)
        print("Debug Information:")
        print(f"  Analysis Type: {state.get('analysis_type', 'N/A')}")
        if state.get('sql_query'):
            print(f"  SQL Query: {state['sql_query'][:100]}...")
        if state.get('query_results') is not None:
            df = state['query_results']
            print(f"  Rows Returned: {len(df)}")
    
    print("\n" + "─" * 63)


def run_interactive_cli():
    """Run the interactive CLI chat loop."""
    # Setup
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    load_environment()
    
    print_banner()
    
    # Initialize BigQuery client
    try:
        print("🔧 Initializing BigQuery connection...", end="", flush=True)
        project_id = os.getenv("GCP_PROJECT_ID")
        dataset_id = os.getenv("BIGQUERY_DATASET", "bigquery-public-data.thelook_ecommerce")
        initialize_bigquery_client(project_id=project_id, dataset_id=dataset_id)
        print("\r✅ BigQuery connection established!    ")
    except Exception as e:
        print(f"\r❌ Failed to connect to BigQuery: {e}")
        print("\nPlease ensure:")
        print("  1. Google Cloud SDK is installed and configured")
        print("  2. You have authenticated with: gcloud auth application-default login")
        print("  3. Your GCP project has BigQuery API enabled")
        sys.exit(1)
    
    # Create LangGraph agent
    try:
        print("🤖 Initializing AI agent...", end="", flush=True)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        graph = create_data_analysis_graph(model_name=model_name)
        print(f"\r✅ AI agent ready! (using {model_name})    ")
    except Exception as e:
        print(f"\r❌ Failed to initialize agent: {e}")
        sys.exit(1)
    
    print("\n" + "─" * 63 + "\n")
    
    # Main chat loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
                print("\n👋 Thank you for using the Data Analysis Agent. Goodbye!\n")
                break
            
            # Skip empty input
            if not user_input:
                continue
            
            # Show help if requested
            if user_input.lower() in ['help', '?']:
                print("\n📖 Help:")
                print("  • Ask questions about customer behavior, products, sales, or geography")
                print("  • Examples:")
                print("    - 'What are the top 10 selling products?'")
                print("    - 'Show me sales trends by month'")
                print("    - 'Which countries have the most customers?'")
                print("    - 'Analyze customer segments by purchase frequency'")
                print("  • Commands: 'exit', 'quit', 'help'")
                print()
                continue
            
            # Process the query
            print_thinking()
            print_processing()
            
            try:
                final_state = run_analysis(user_input, graph, verbose=False)
                response = get_response_from_state(final_state)
                print_response(response, final_state)
            except KeyboardInterrupt:
                print("\n\n⚠️  Query interrupted by user.\n")
                continue
            except Exception as e:
                print(f"\r❌ Error processing query: {e}")
                logging.exception("Query processing error")
                print()
        
        except KeyboardInterrupt:
            print("\n\n👋 Exiting... Goodbye!\n")
            break
        except EOFError:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            logging.exception("Unexpected error in main loop")


def main():
    """Main entry point."""
    try:
        run_interactive_cli()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()

