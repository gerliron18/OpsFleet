# Architecture Documentation

## Overview

The E-Commerce Data Analysis Agent is built using LangGraph, a framework for building stateful, multi-step LLM applications. The system follows a graph-based architecture where each node performs a specific task, and conditional edges control the flow based on the results.

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface (CLI)                    │
│  - Interactive chat loop                                    │
│  - Input validation                                         │
│  - Response formatting                                      │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph State Machine                   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Node 1: Analyze Request                              │ │
│  │  - Classify user intent                               │ │
│  │  - Determine analysis type                            │ │
│  └───────────────────────────────────────────────────────┘ │
│                             ↓                               │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Node 2: Generate SQL                                 │ │
│  │  - Retrieve table schemas                             │ │
│  │  - Construct BigQuery SQL query                       │ │
│  │  - Validate query safety                              │ │
│  └───────────────────────────────────────────────────────┘ │
│                             ↓                               │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Node 3: Execute Query                                │ │
│  │  - Run query on BigQuery                              │ │
│  │  - Handle execution errors                            │ │
│  └───────────────────────────────────────────────────────┘ │
│                             ↓                               │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Conditional Router                                   │ │
│  │  - Success → Analyze Results                          │ │
│  │  - Error + Can Retry → Generate SQL (fix & retry)    │ │
│  │  - Error + Max Retries → Respond (with error)        │ │
│  └───────────────────────────────────────────────────────┘ │
│                             ↓                               │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Node 4: Analyze Results                              │ │
│  │  - Process query results                              │ │
│  │  - Generate business insights                         │ │
│  │  - Create recommendations                             │ │
│  └───────────────────────────────────────────────────────┘ │
│                             ↓                               │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Node 5: Respond                                      │ │
│  │  - Format final response                              │ │
│  │  - Add metadata                                       │ │
│  └───────────────────────────────────────────────────────┘ │
└───────────────────┬─────────────────────────────────────────┘
                    │
    ┌───────────────┴───────────────┐
    ↓                               ↓
┌─────────────────────┐   ┌──────────────────────┐
│  Google Gemini LLM  │   │  Google BigQuery     │
│  - Intent analysis  │   │  - Query execution   │
│  - SQL generation   │   │  - Schema retrieval  │
│  - Insight creation │   │  - Public dataset    │
└─────────────────────┘   └──────────────────────┘
```

## Detailed Component Breakdown

### 1. State Management (`agent/state.py`)

The agent maintains a typed state that flows through all nodes:

**AgentState Schema:**
- `messages`: Chat history (List[BaseMessage])
- `user_query`: Current user question (str)
- `analysis_type`: Classified analysis category (Optional[str])
- `sql_query`: Generated SQL query (Optional[str])
- `query_results`: DataFrame from BigQuery (Optional[pd.DataFrame])
- `insights`: Generated business insights (Optional[str])
- `error`: Error message if any (Optional[str])
- `retry_count`: Number of retry attempts (int)
- `schema_context`: Cached table schemas (Optional[Dict])

This typed state ensures data consistency and makes debugging easier.

### 2. Graph Nodes (`agent/nodes.py`)

Each node is a pure function that takes the current state and returns updates:

#### Node 1: `analyze_request_node`
**Purpose:** Classify user intent into analysis categories
- **Input:** User query
- **LLM Task:** Intent classification
- **Output:** Analysis type (customer_segmentation, product_performance, sales_trends, geographic_patterns, general_query)
- **Error Handling:** Defaults to general_query on failure

#### Node 2: `generate_sql_node`
**Purpose:** Generate BigQuery SQL query
- **Input:** User query, analysis type, table schemas
- **LLM Task:** SQL query generation
- **Output:** Validated SQL query
- **Features:**
  - Retrieves and caches table schemas
  - Validates query safety (no DROP, DELETE, etc.)
  - Handles error recovery (regenerates SQL if previous attempt failed)
- **Error Handling:** Returns validation errors for dangerous queries

#### Node 3: `execute_query_node`
**Purpose:** Execute SQL on BigQuery
- **Input:** SQL query
- **Operation:** Direct BigQuery execution via client
- **Output:** DataFrame with results
- **Error Handling:** 
  - Captures BigQuery errors
  - Increments retry counter
  - Returns error details for recovery

#### Node 4: `analyze_results_node`
**Purpose:** Generate business insights from data
- **Input:** Query results, user query, analysis type
- **LLM Task:** Data analysis and insight generation
- **Output:** Formatted insights with recommendations
- **Features:**
  - Handles empty result sets
  - Formats data for LLM context
  - Provides fallback insights on error
- **Error Handling:** Returns basic stats if LLM fails

#### Node 5: `respond_node`
**Purpose:** Format final response
- **Input:** All previous state data
- **Operation:** Message formatting
- **Output:** AIMessage with formatted response
- **Features:**
  - Handles success, partial success, and failure cases
  - Adds data summary metadata
  - User-friendly error messages

### 3. Routing Logic (`agent/graph.py`)

**Conditional Router (`route_after_execution`):**
```python
if error AND can_retry AND retry_count < max_retries:
    return "generate_sql"  # Try to fix SQL and retry
elif has_results:
    return "analyze_results"  # Success path
else:
    return "respond"  # Failure path, report error
```

**Retry Strategy:**
- Maximum 2 retries per query
- Non-retryable errors (auth, permissions) fail immediately
- SQL errors trigger regeneration with error context

### 4. LLM Integration (`llm/gemini_client.py`)

**GeminiClient Features:**
- Configurable model selection (gemini-2.5-flash, gemini-1.5-pro)
- Exponential backoff for rate limits (1s, 2s, 4s)
- Automatic retry for transient failures
- Temperature control (default: 0.1 for deterministic output)

**Rate Limit Handling:**
```python
wait_time = (2 ** attempt) * 1  # Exponential backoff
if "rate limit" in error:
    sleep(wait_time)
    retry()
```

### 5. BigQuery Integration (`tools/bigquery_tools.py`)

**Key Functions:**
- `execute_query_direct()`: Direct query execution, returns DataFrame
- `get_all_table_schemas()`: Retrieves schema for all tables
- `validate_sql_query()`: Safety checks before execution

**Query Validation:**
- Blocks dangerous operations (DROP, DELETE, UPDATE, INSERT, etc.)
- Ensures SELECT-only queries
- Validates basic syntax (parentheses matching)

### 6. Prompt Engineering (`prompts/system_prompts.py`)

**Intent Analysis Prompt:**
- Clear category definitions
- Dataset context
- Examples of each category

**SQL Generation Prompt:**
- Complete schema information
- BigQuery-specific syntax requirements
- Best practices (qualified names, efficient queries)
- User query and analysis type context

**Insight Generation Prompt:**
- Structured output format
- Requirement for actionable recommendations
- Emphasis on specific data values
- Business-focused language

## Data Flow

### Successful Query Flow

1. **User Input:** "What are the top 10 selling products?"

2. **Analyze Request:**
   - Input: User query
   - LLM classifies as: "product_performance"
   - Output: analysis_type = "product_performance"

3. **Generate SQL:**
   - Input: Query + analysis type + schemas
   - LLM generates:
   ```sql
   SELECT p.name, COUNT(*) as order_count
   FROM `bigquery-public-data.thelook_ecommerce.order_items` oi
   JOIN `bigquery-public-data.thelook_ecommerce.products` p
     ON oi.product_id = p.id
   GROUP BY p.name
   ORDER BY order_count DESC
   LIMIT 10
   ```
   - Output: validated SQL query

4. **Execute Query:**
   - Input: SQL query
   - BigQuery executes, returns DataFrame
   - Output: 10 rows with product names and counts

5. **Analyze Results:**
   - Input: DataFrame + context
   - LLM generates insights:
     - Summary of findings
     - Specific product performance metrics
     - Recommendations for inventory/marketing
   - Output: formatted insights

6. **Respond:**
   - Input: Insights
   - Formats as user-friendly message
   - Output: Final response to user

### Error Recovery Flow

1. **Query Execution Fails:**
   - SQL error: "Column 'product_name' not found"
   - State updates: error message, retry_count++

2. **Router Decision:**
   - Checks: retry_count < 2? Yes
   - Decision: Route to "generate_sql"

3. **SQL Regeneration:**
   - Input: Original query + error message
   - LLM sees error context, fixes query
   - Output: Corrected SQL (uses 'name' instead of 'product_name')

4. **Re-execute:**
   - Query succeeds
   - Continues to analyze_results

## Cloud Services Justification

### Why Google Gemini?

**Advantages:**
1. **Cost:** Free tier with 15 RPM (requests per minute)
2. **Performance:** Fast response times (~1-2s per request)
3. **Quality:** Excellent SQL generation and reasoning capabilities
4. **Integration:** Native LangChain support
5. **Quota:** Sufficient for development and demo purposes

**Alternatives Considered:**
- AWS Bedrock: More expensive, requires AWS account setup
- OpenAI GPT-4: Paid only, higher latency
- Local models: Insufficient performance for SQL generation

### Why Google BigQuery?

**Advantages:**
1. **Dataset:** Public thelook_ecommerce dataset available
2. **Free Tier:** 1TB compute/month (more than sufficient)
3. **Performance:** Fast queries on large datasets
4. **Scale:** Handles complex analytical queries efficiently
5. **Integration:** Simple Python client

**Requirements:**
- Only requires GCP authentication (free)
- No project required (can query public datasets)

### Why LangGraph?

**Advantages:**
1. **Control:** Explicit flow vs. autonomous agents
2. **Debugging:** Visible state transitions
3. **Reliability:** Predictable behavior for production
4. **Error Handling:** Easy to implement retry logic
5. **Flexibility:** Conditional routing based on results

**vs. Autonomous Agents:**
- Autonomous agents (ReAct, Function Calling) can loop indefinitely
- LangGraph provides deterministic flow
- Better for production reliability

## Error Handling Strategy

### Three-Layer Error Handling

**Layer 1: API Resilience**
- Exponential backoff for rate limits
- Automatic retry for transient failures
- Maximum 3 attempts per API call

**Layer 2: Query Recovery**
- SQL validation before execution
- Error context provided to LLM for fixing
- Maximum 2 SQL regeneration attempts

**Layer 3: User Communication**
- Clear error messages
- Troubleshooting suggestions
- Graceful degradation (basic stats if analysis fails)

### Non-Retryable Errors

The following errors fail immediately:
- Authentication/permission errors
- Invalid API keys
- Project quota exceeded
- Missing required environment variables

### Retryable Errors

These errors trigger retry logic:
- SQL syntax errors
- Column name mismatches
- Rate limit errors (429)
- Temporary network issues

## Performance Considerations

### Caching Strategy
- Table schemas cached after first retrieval
- Reduces BigQuery API calls
- Speeds up subsequent queries

### Query Optimization
- LLM instructed to use LIMIT clauses
- Efficient JOIN strategies
- Proper WHERE clause placement

### Latency Breakdown
- Intent analysis: ~1-2s
- SQL generation: ~2-3s
- Query execution: ~1-5s (depends on query complexity)
- Insight generation: ~2-3s
- **Total:** ~6-13 seconds per query

### Cost Analysis
- Gemini API: Free (15 RPM limit)
- BigQuery compute: Free (1TB/month)
- No data egress costs (results typically small)

## Security & Safety

### Query Safety
- Only SELECT queries allowed
- No data modification operations
- Read-only access to public dataset

### API Key Management
- Stored in .env (not committed)
- Loaded via python-dotenv
- Validated at startup

### Data Privacy
- No user data stored
- No logging of sensitive information
- Public dataset only

## Testing Strategy

### Manual Testing Checklist
1. Customer segmentation queries
2. Product performance analysis
3. Sales trend queries
4. Geographic analysis
5. Error scenarios (invalid queries)
6. Rate limit handling
7. Network failures
8. Empty result sets

### Example Test Queries
```python
test_queries = [
    "What are the top 10 products by revenue?",
    "Show me sales trends by month",
    "Which countries have the most orders?",
    "Analyze customer segments by age",
    "What's the average order value by category?",
]
```

## Deployment Considerations

### Environment Setup
1. Python 3.9+ environment
2. Google Cloud SDK installed
3. Authenticated with gcloud
4. Environment variables configured

### Production Enhancements (Future)
- Web interface (Gradio/Streamlit)
- Query caching (Redis)
- User authentication
- Rate limiting per user
- Query history tracking
- Export results to CSV/Excel

## Troubleshooting Guide

### Common Issues

**Issue: BigQuery authentication fails**
- Solution: Run `gcloud auth application-default login`

**Issue: API key invalid**
- Solution: Verify key in .env matches Google AI Studio

**Issue: Rate limit hit**
- Solution: Wait 1 minute or upgrade to paid tier

**Issue: Module import errors**
- Solution: `pip install -r requirements.txt --upgrade`

## Future Enhancements

### Short Term
- Add data visualization (charts/graphs)
- Export functionality (CSV, JSON)
- Query history and favorites
- More detailed error messages

### Long Term
- Multi-turn conversations with context
- Comparative analysis across time periods
- Predictive analytics
- Custom dataset support
- Web dashboard interface

---

**Document Version:** 1.0  
**Last Updated:** November 15 2025
