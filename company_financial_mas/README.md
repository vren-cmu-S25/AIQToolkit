# Company Financial Multi-Agent System

This project implements a powerful multi-agent system (MAS) for company financial analysis using the NVIDIA AIQ toolkit. The system is designed to analyze financial data, answer complex financial queries, and provide actionable insights through a hierarchical agent structure.

## Table of Contents
- [Company Financial Multi-Agent System](#company-financial-multi-agent-system)
  - [Table of Contents](#table-of-contents)
  - [Use Case Description](#use-case-description)
    - [Why Use a Multi-Agent System?](#why-use-a-multi-agent-system)
  - [How It Works](#how-it-works)
    - [Agent Hierarchy](#agent-hierarchy)
    - [Understanding the Configuration](#understanding-the-configuration)
      - [Functions](#functions)
      - [Workflow](#workflow)
      - [LLMs](#llms)
  - [Installation and Setup](#installation-and-setup)
    - [Install This Project](#install-this-project)
    - [Set Up Environment Variables](#set-up-environment-variables)
  - [Example Usage](#example-usage)
    - [Running in Test Mode](#running-in-test-mode)
    - [Running in Live Mode](#running-in-live-mode)
    - [Running with a HTTP Server](#running-with-a-http-server)
  - [Adding Your Own Financial Data](#adding-your-own-financial-data)
  - [Fine-Tuning for Your Company](#fine-tuning-for-your-company)

## Use Case Description

This Multi-Agent System (MAS) is designed to address several key challenges in company financial analysis:

* **Complex Query Understanding**: Financial queries often require understanding of context, industry specifics, and company history
* **Data Fragmentation**: Financial data is typically spread across multiple sources and formats
* **Analytical Depth**: Different financial domains require specialized analysis techniques
* **Contextual Insight Generation**: Interpreting financial metrics requires domain knowledge and historical context
* **Decision Support**: Financial analysis must lead to actionable insights and recommendations

The system solves these challenges through a hierarchical structure of specialized agents that collaborate to:

1. **Parse and plan** responses to complex financial queries
2. **Retrieve and analyze** relevant data from multiple sources
3. **Generate domain-specific insights** across profitability, liquidity, efficiency, risk, and growth metrics
4. **Synthesize findings** into cohesive, actionable recommendations
5. **Present results** in an understandable format with appropriate visualizations

### Why Use a Multi-Agent System?

A multi-agent architecture offers several advantages over traditional financial analysis tools:

- **Specialized Expertise**: Each agent focuses on a specific financial domain, enabling deeper analysis
- **Parallel Processing**: Multiple agents can work simultaneously to analyze different aspects of a query
- **Adaptive Reasoning**: Agents can dynamically adjust their analysis based on new information discovered
- **Scalability**: Easy to extend with new specialized agents as analysis needs grow
- **Context Preservation**: Shared memory ensures consistent understanding of company context

## How It Works

The system follows a hierarchical approach to process financial queries:

[Financial MAS Architecture](./src/company_financial_mas/data/financial_mas_architecture.txt)

### Agent Hierarchy

1. **Financial Controller Agent** (Main LLM)
   - Orchestrates the overall process
   - Manages conversation context with users
   - Provides consistent interface regardless of query complexity

2. **Query Understanding & Planning Agent**
   - Classifies query type and determines which specialized agents to engage
   - Generates execution plan for complex queries
   - Maps user intent to appropriate financial domains

3. **Specialized Financial Analysis Agents**
   - **Profitability Analysis Agent**: Examines revenue, costs, margins, and earnings
   - **Liquidity Analysis Agent**: Assesses cash flow, working capital, and short-term solvency
   - **Efficiency Analysis Agent**: Evaluates resource usage, turnover ratios, and operational metrics
   - **Risk & Leverage Agent**: Analyzes debt levels, coverage ratios, and financial stability
   - **Growth Analysis Agent**: Measures historical growth and forecasts future performance

4. **Memory & Database Interaction Agent**
   - Manages data retrieval across all storage systems
   - Handles caching and query optimization
   - Coordinates access to:
     - Vector Database (conversations, embeddings)
     - Time-Series Database (financial metrics)
     - Document Database (reports, filings)
     - Knowledge Graph (entity relationships)

5. **Insight Aggregation & Visualization Agent**
   - Compiles findings from specialized agents
   - Identifies patterns, correlations, and conflicts
   - Selects appropriate visualization methods

6. **Response Generation Agent**
   - Formats final answers in user-friendly language
   - Generates visualizations and supporting evidence
   - Ensures explanations match user's financial sophistication level

### Understanding the Configuration

#### Functions

Each entry in the `functions` section defines a tool or agent that can be invoked by the main workflow agent.

Example:

```yaml
profitability_analysis:
  _type: profitability_analysis
  llm_name: financial_analysis_llm
  test_mode: true
```

* `_type`: Identifies the name of the tool/agent
* `llm_name`: LLM used by the tool for analysis
* `test_mode`: If `true`, the tool uses predefined mock results for testing

#### Workflow

The `workflow` section defines the primary agent's execution flow:

```yaml
workflow:
  _type: financial_controller_agent
  tool_names:
    - query_understanding_planning
    - profitability_analysis
    - liquidity_analysis
    # ... other tools
  llm_name: controller_llm
  test_mode: true
  test_data_path: ...
  test_output_path: ...
```

* `_type`: The name of the main agent
* `tool_names`: List of tools (from the `functions` section) used in the workflow
* `llm_name`: Main LLM used by the controller agent
* `test_mode`: Enables test execution using predefined data

#### LLMs

The `llms` section defines the available LLMs for various parts of the system:

```yaml
controller_llm:
  _type: nim
  model_name: meta/llama-3.3-70b-instruct
  temperature: 0.2
  max_tokens: 2048
```

Each agent can use a dedicated LLM tailored for its specific task.

## Installation and Setup

If you have not already done so, follow the instructions in the [NVIDIA AIQ Toolkit Install Guide](../../docs/source/quick-start/installing.md) to create the development environment and install AIQ toolkit.

### Install This Project

From the root directory of the AIQ toolkit library, run the following commands:

```bash
uv pip install -e ./company_financial_mas
```

### Set Up Environment Variables

An `NVIDIA_API_KEY` environment variable is required to run AIQ toolkit. Additionally, you might need database connection strings depending on your setup.

Create a `.env` file in the project root with:

```
NVIDIA_API_KEY=your_nvidia_api_key_here
VECTOR_DB_CONNECTION=your_vector_db_connection_string
TIMESERIES_DB_CONNECTION=your_timeseries_db_connection_string
DOCUMENT_DB_CONNECTION=your_document_db_connection_string
```

Load the environment variables with:
```bash
export $(grep -v '^#' .env | xargs)
```

## Example Usage

You can run the system in test mode or live mode.

### Running in Test Mode

Test mode lets you evaluate the system using synthetic financial data:

```bash
aiq run --config_file=company_financial_mas/configs/config_test_mode.yml --input "What was our company's profitability trend over the last 4 quarters?"
```

In test mode, the system uses predefined responses from test data files.

### Running in Live Mode

In live mode, the system connects to your actual financial databases:

```bash
aiq run --config_file=company_financial_mas/configs/config_live_mode.yml --input "How has our debt-to-equity ratio changed since implementing the new financing strategy?"
```

### Running with a HTTP Server

For continuous operation with a web interface:

```bash
python company_financial_mas/src/company_financial_mas/run.py --host 0.0.0.0 --port 5000 --env_file company_financial_mas/.env
```

This starts a server that can receive financial queries via HTTP POST requests.

## Adding Your Own Financial Data

To use your company's actual financial data:

1. Format your financial statements (balance sheets, income statements, cash flow statements) as CSV files in the `data/financial_statements` directory
2. Add key financial metrics to `data/metrics` directory as time-series CSV files
3. Place any financial reports or analysis documents in the `data/documents` directory
4. Update connection strings in your `.env` file if using external databases

## Fine-Tuning for Your Company

To customize the system for your company's specific needs:

1. Modify prompts in `src/company_financial_mas/prompts.py` to include your company's financial context
2. Adjust financial ratio calculations in the specialized agents to match your industry standards
3. Update visualization preferences in the visualization agent
4. Consider fine-tuning the underlying LLMs with your company's financial reports and terminology 