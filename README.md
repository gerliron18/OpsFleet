# E-Commerce Data Analysis LangGraph Agent

A sophisticated AI agent built with LangGraph that analyzes e-commerce data from Google BigQuery's public dataset and generates actionable business insights using Google Gemini.

## 🎯 Features

- **Intelligent Query Understanding**: Automatically classifies user questions into analysis categories
- **Dynamic SQL Generation**: Creates optimized BigQuery SQL queries based on natural language requests
- **Comprehensive Analysis Types**:
  - Customer segmentation and behavior analysis
  - Product performance and recommendations
  - Sales trends and seasonality patterns
  - Geographic sales distributions
- **Error Recovery**: Automatic retry logic with SQL error correction
- **Interactive CLI**: User-friendly command-line interface with progress indicators
- **Rate Limiting**: Built-in handling for API rate limits with exponential backoff

## 🏗️ Architecture

The agent uses LangGraph's state graph pattern for explicit control flow:

```
User Query
    ↓
┌─────────────────┐
│ Analyze Request │ ← Determine intent & analysis type
└─────────────────┘
    ↓
┌─────────────────┐
│  Generate SQL   │ ← Create BigQuery SQL query
└─────────────────┘
    ↓
┌─────────────────┐
│ Execute Query   │ ← Run query on BigQuery
└─────────────────┘
    ↓
    ├─ Error? → Retry (max 2x) → Generate SQL
    ↓
┌─────────────────┐
│ Analyze Results │ ← Generate business insights
└─────────────────┘
    ↓
┌─────────────────┐
│    Respond      │ ← Format & return to user
└─────────────────┘
```

### Components

- **State Management** (`agent/state.py`): Typed state tracking query context and results
- **Graph Nodes** (`agent/nodes.py`): Core logic for each processing step
- **Graph Builder** (`agent/graph.py`): StateGraph construction with conditional routing
- **LLM Integration** (`llm/gemini_client.py`): Gemini configuration with retry logic
- **BigQuery Tools** (`tools/bigquery_tools.py`): Query execution and schema retrieval
- **System Prompts** (`prompts/system_prompts.py`): Carefully crafted prompts for each step
- **Testing** (`tests/test_all_analysis_types.py`): Testing the whole agent flow for all 4 analysis types

## 📋 Prerequisites

- Python 3.9+
- Google Cloud account with BigQuery access
- Google AI Studio API key (free tier available)

## 🚀 Setup

### 1. Clone the Repository

```bash
git clone [<repository-url>](https://github.com/gerliron18/OpsFleet.git)
cd OpsFleet
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Google Cloud

Authenticate with Google Cloud for BigQuery access:

```bash
# Install Google Cloud SDK if not already installed
# Download from: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login

# Set your project (optional)
gcloud config set project YOUR_PROJECT_ID
```

### 4. Get Google AI Studio API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp env.example .env
```

Edit `.env` and add your API key:

```env
# Required: Google AI Studio API Key
GOOGLE_API_KEY=your_api_key_here

# Optional: GCP Project ID (uses default if not set)
# GCP_PROJECT_ID=your_project_id

# Optional: BigQuery Dataset (default shown)
BIGQUERY_DATASET=bigquery-public-data.thelook_ecommerce

# Optional: Gemini Model (default: gemini-2.5-flash)
# GEMINI_MODEL=gemini-2.5-flash

# Optional: Logging Level (default: INFO)
LOG_LEVEL=INFO
```

## 💻 Usage

### Start the Interactive CLI

```bash
python main.py
```

### Example Queries

#### Customer Segmentation
```
What are the top customer segments by purchase frequency?
Show me RFM analysis for customers
Which customers have the highest lifetime value?
```

#### Product Performance
```
What are the top 10 best-selling products?
Show me product performance by category
Which products have the highest profit margins?
```

#### Sales Trends
```
Show me monthly sales trends for the last year
Analyze sales seasonality patterns
What were the sales trends during holiday seasons?
```

#### Geographic Analysis
```
Which countries generate the most revenue?
Show me sales distribution by region
What are the top cities by order volume?
```

### CLI Commands

- Type your question in natural language
- `help` or `?` - Show help information
- `exit`, `quit`, `q`, `bye` - Exit the application

## 🧪 Example Session

```
You: What are the top 5 selling products?

🤔 Analyzing your question...
🔍 Processing query...

───────────────────────────────────────────────────────────────

📊 Analysis Results:

Summary:
The top 5 selling products based on order count show strong 
performance across different categories, with Product A leading 
significantly.

Detailed Findings:
1. Product A (Electronics): 1,234 orders, $45,678 revenue
2. Product B (Clothing): 1,156 orders, $38,920 revenue
...

Recommendations:
- Increase inventory for top-performing products
- Consider bundling strategies for related items
- Analyze why Product A outperforms others

───────────────────────────────────────────────────────────────
```

## 📊 Dataset Information

The agent queries the public BigQuery dataset: `bigquery-public-data.thelook_ecommerce`

### Available Tables

- **orders**: Order information (order_id, user_id, status, created_at, etc.)
- **order_items**: Line items (order_id, product_id, sale_price, etc.)
- **products**: Product catalog (product_id, name, brand, category, price, etc.)
- **users**: Customer data (user_id, name, email, age, gender, city, country, etc.)

## 🛡️ Error Handling

The agent includes comprehensive error handling:

- **SQL Errors**: Automatically attempts to fix and retry queries (up to 2 retries)
- **Rate Limits**: Exponential backoff for Gemini API rate limits
- **Query Validation**: Prevents dangerous operations (DROP, DELETE, etc.)
- **Connection Issues**: Clear error messages with troubleshooting steps

## 🧩 Technical Decisions

### Why Gemini?
- Free tier with generous quotas
- Excellent SQL generation capabilities
- Strong natural language understanding
- Easy integration with LangChain

### Why LangGraph?
- Explicit control over agent flow (vs. fully autonomous agents)
- Easy debugging with visible state transitions
- Conditional routing for error recovery
- Better reliability for production use

### Error Recovery Strategy
- Multi-layer approach: retry API calls, reformulate SQL on errors
- Non-retryable errors (auth, permissions) fail immediately
- User-friendly error messages with context

## 📁 Project Structure

```
OpsFleet/
├── main.py                # CLI entry point
├── bq_client.py           # BigQuery client wrapper
├── requirements.txt       # Python dependencies
├── env.example            # Environment variables template
├── README.md              # This file
├── setup.sh               # Setup dependencies and env
├── agent/
│   ├── __init__.py
│   ├── state.py          # State definitions
│   ├── nodes.py          # Graph node implementations
│   └── graph.py          # StateGraph construction
├── tools/
│   ├── __init__.py
│   └── bigquery_tools.py # BigQuery tool wrappers
├── llm/
│   ├── __init__.py
│   └── gemini_client.py  # Gemini LLM configuration
├── prompts/
│   ├── __init__.py
│   └── system_prompts.py # Agent system prompts
├── tests/
│   ├── __init__.py
│   ├── test_all_analysis_types.py   # Integration test for all 4 analysis types
│   ├── test_bigquery_tools.py       # Unit test for big-query tools
│   ├── test_integration.py          # Basic integration test
│   ├── test_nodes.py                # Unit test for nodes
│   ├── test_prompts.py              # Unit test for prompts
│   └── test_state.py                # Unit test for state
└── docs/
    ├── architecture.md    # Detailed architecture documentation
    └── architecture.txt   # Architecture diagram
```

## 🐛 Troubleshooting

### BigQuery Authentication Issues

```bash
# Re-authenticate
gcloud auth application-default login

# Verify authentication
gcloud auth application-default print-access-token
```

### API Key Issues

- Ensure `.env` file exists and contains `GOOGLE_API_KEY`
- Verify the API key is valid in [Google AI Studio](https://makersuite.google.com/app/apikey)
- Check for rate limit errors (free tier: 15 RPM)

### Module Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## 📈 Performance Notes

- **First Query**: ~5-10 seconds (includes schema retrieval)
- **Subsequent Queries**: ~3-5 seconds (cached schemas)
- **BigQuery Compute**: Uses free tier (1TB/month)
- **Gemini API**: Free tier limits apply (15 requests/minute)

## 🔒 Security

- SQL query validation prevents dangerous operations
- Only SELECT queries are allowed
- No write access to BigQuery
- API keys stored in `.env` (not committed to git)

## 📝 License

This project is created for educational purposes as part of a technical assignment.

## 🙋 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the architecture documentation in `docs/`
3. Enable DEBUG logging: `LOG_LEVEL=DEBUG` in `.env`
