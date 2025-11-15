#!/usr/bin/env python3
"""Test all 4 analysis types required by the assignment."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def test_all_analysis_types():
    """Test all 4 analysis capabilities required by the assignment."""
    print("\n" + "="*70)
    print("  Testing All Analysis Types")
    print("="*70 + "\n")
    
    # Initialize
    from tools.bigquery_tools import initialize_bigquery_client
    from agent.graph import create_data_analysis_graph, run_analysis, get_response_from_state
    
    try:
        # Initialize BigQuery
        print("Initializing BigQuery client...")
        gcp_project_id = os.getenv("GCP_PROJECT_ID")
        dataset_id = os.getenv("BIGQUERY_DATASET")
        initialize_bigquery_client(project_id=gcp_project_id, dataset_id=dataset_id)
        print("✅ BigQuery connected\n")
        
        # Create graph
        print("Creating LangGraph agent...")
        graph = create_data_analysis_graph()
        print("✅ Agent ready\n")
        
        # Define test queries for each analysis type
        test_queries = [
            {
                "type": "Customer Segmentation",
                "query": "Analyze customer segments by purchase frequency and total spending",
                "expected_type": "customer_segmentation"
            },
            {
                "type": "Product Performance",
                "query": "What are the top 10 selling products by revenue?",
                "expected_type": "product_performance"
            },
            {
                "type": "Sales Trends",
                "query": "Show me monthly sales trends for the last 12 months",
                "expected_type": "sales_trends"
            },
            {
                "type": "Geographic Patterns",
                "query": "Which countries generate the most revenue?",
                "expected_type": "geographic_patterns"
            }
        ]
        
        results = []
        
        for i, test in enumerate(test_queries, 1):
            print("\n" + "="*70)
            print(f"  Test {i}/4: {test['type']}")
            print("="*70)
            print(f"Query: '{test['query']}'")
            print("\nProcessing...")
            print("-" * 70)
            
            try:
                # Run the query
                final_state = run_analysis(test['query'], graph, verbose=False)
                
                # Get response
                response = get_response_from_state(final_state)
                
                # Check results
                analysis_type = final_state.get('analysis_type')
                sql_query = final_state.get('sql_query')
                query_results = final_state.get('query_results')
                insights = final_state.get('insights')
                error = final_state.get('error')
                
                success = True
                issues = []
                
                # Validate
                if not analysis_type:
                    success = False
                    issues.append("No analysis type detected")
                elif analysis_type != test['expected_type']:
                    issues.append(f"Expected {test['expected_type']}, got {analysis_type}")
                
                if not sql_query:
                    success = False
                    issues.append("No SQL generated")
                
                if query_results is None:
                    success = False
                    issues.append("No query results")
                elif len(query_results) == 0:
                    issues.append("Empty results (but query executed)")
                
                if not insights:
                    success = False
                    issues.append("No insights generated")
                
                if error:
                    success = False
                    issues.append(f"Error: {error[:100]}")
                
                # Display results
                print("\n" + "─" * 70)
                print("RESULTS:")
                print("─" * 70)
                
                if success and not issues:
                    print("✅ SUCCESS")
                    print(f"  Analysis Type: {analysis_type}")
                    print(f"  SQL Generated: {len(sql_query)} chars")
                    if query_results is not None:
                        print(f"  Rows Returned: {len(query_results)}")
                    print(f"  Insights: {len(insights)} chars")
                    print("\nInsights Preview:")
                    print(insights[:500] + "..." if len(insights) > 500 else insights)
                else:
                    print("⚠️  PARTIAL SUCCESS" if success else "❌ FAILED")
                    print(f"  Analysis Type: {analysis_type or 'None'}")
                    if sql_query:
                        print(f"  SQL Generated: {len(sql_query)} chars")
                    if query_results is not None:
                        print(f"  Rows Returned: {len(query_results)}")
                    if issues:
                        print("  Issues:")
                        for issue in issues:
                            print(f"    - {issue}")
                
                results.append({
                    "type": test['type'],
                    "success": success and not issues,
                    "partial": success and issues,
                    "issues": issues
                })
                
            except Exception as e:
                print(f"\n❌ ERROR: {e}")
                results.append({
                    "type": test['type'],
                    "success": False,
                    "partial": False,
                    "issues": [str(e)]
                })
        
        # Summary
        print("\n\n" + "="*70)
        print("  SUMMARY")
        print("="*70 + "\n")
        
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        partial = sum(1 for r in results if r['partial'])
        failed = sum(1 for r in results if not r['success'] and not r['partial'])
        
        for result in results:
            status = "✅" if result['success'] else "⚠️" if result['partial'] else "❌"
            print(f"{status} {result['type']}")
            if result['issues']:
                for issue in result['issues']:
                    print(f"     └─ {issue}")
        
        print(f"\nTotal: {successful}/{total} fully successful")
        if partial:
            print(f"Partial: {partial}/{total} (executed but with minor issues)")
        if failed:
            print(f"Failed: {failed}/{total}")
        
        print("\n" + "="*70)
        if successful == total:
            print("🎉 ALL ANALYSIS TYPES WORKING PERFECTLY!")
        elif successful + partial == total:
            print("✅ All analysis types executed (some with minor issues)")
        else:
            print("⚠️  Some analysis types need attention")
        print("="*70 + "\n")
        
        return successful == total
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_all_analysis_types()
    sys.exit(0 if success else 1)

