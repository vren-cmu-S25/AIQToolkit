# SQL Interaction Agent

The SQL Interaction Agent is a specialized component of the Company Financial Multi-Agent System that handles database interactions. It translates natural language queries into SQL, executes them against the financial database, and interprets the results.

## Features

- **Table Listing**: Lists all available tables in the financial database
- **Schema Retrieval**: Gets detailed schema information for any table
- **SQL Query Execution**: Executes SQL queries and returns formatted results
- **Natural Language to SQL**: Translates natural language questions into SQL queries
- **Result Interpretation**: Provides insights and analysis of query results
- **TimescaleDB Integration**: Optimized for time-series financial data

## Architecture

The SQL Interaction Agent is built on the NVIDIA AIQ framework and can be configured to use either:

1. **ReAct Agent**: Reasoning and Acting agent that performs step-by-step reasoning to translate queries to SQL
2. **Tool Calling Agent**: Direct function-calling agent that leverages tool schemas for database interaction

## Tools

The agent provides three core tools:

1. **list_tables_tool**: Lists all available tables in the database
2. **get_schema_tool**: Gets detailed schema information for a specific table
3. **db_query_tool**: Executes SQL queries and returns formatted results

## Configuration

The agent can be configured via YAML:

```yaml
workflow:
  _type: sql_interaction
  llm_name: sql_agent_llm
  agent_type: "react_agent"  # or "tool_calling_agent"
  test_mode: true
  db_env_path: "data/db/timescale-db-61642-credentials.env"
  max_rows: 100
```

### Configuration Options

- **llm_name**: The LLM to use for the agent
- **agent_type**: Type of agent to use ("react_agent" or "tool_calling_agent")
- **test_mode**: Whether to run in test mode (using mock data)
- **db_env_path**: Path to the database credentials .env file
- **connection_string**: Alternative direct database connection string
- **max_rows**: Maximum number of rows to return from a query
- **test_data_path**: Path to test dataset in CSV format
- **benign_fallback_data_path**: Path to JSON file with mock data

## Usage

The SQL Interaction Agent can be used as part of the orchestration flow:

1. The Controller Agent receives a user query
2. If database access is needed, the query is sent to the SQL Interaction Agent
3. The SQL Interaction Agent:
   - Analyzes the query to understand the data needs
   - Lists available tables if needed
   - Retrieves schema information for relevant tables
   - Translates the query to SQL
   - Executes the SQL query
   - Returns formatted results to the Controller Agent
4. The Controller Agent passes the data to specialized analysis agents

## Example Queries

The agent can handle queries such as:

- "What was our revenue trend over the last 3 quarters?"
- "Show me the cash flow metrics for Q1 2024"
- "What's our average profit margin by quarter for the last year?"
- "Compare our operating margin to net profit margin over time"

## Database Schema

The agent works with the following tables:

1. **financial_metrics**: Revenue, growth rates, and margin data
2. **cash_flow_metrics**: Operating, investing, and financing cash flows
3. **annual_metrics**: Yearly financial statement data
4. **profit_by_quarter**: Aggregated quarterly profit metrics

## Security

The SQL Interaction Agent includes several security features:

- SQL query validation and sanitization
- Restriction of data modification operations (DROP, DELETE, etc.)
- Configurable row limits to prevent excessive data retrieval
- Test mode for development without accessing production data 