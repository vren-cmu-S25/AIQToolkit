# Company Financial Multi-Agent System (MAS)

A sophisticated financial analysis system built using NVIDIA AIQ that employs multiple specialized agents to analyze company financial data and provide comprehensive insights.

## Architecture Overview

The system follows a hierarchical multi-agent architecture:

```
User Query
    │
    ▼
Financial Controller Agent (Main LLM)
    │
    ▼
Query Understanding & Planning Agent
    │
    ├─────────┬─────────┬─────────┬─────────┬─────────┐
    ▼         ▼         ▼         ▼         ▼         ▼
Profitability  Liquidity  Efficiency  Risk &    Growth    Memory &
Analysis      Analysis   Analysis    Leverage  Analysis  Database
Agent         Agent      Agent       Agent     Agent     Agent
```

### Key Components

1. **Financial Controller Agent**
   - Orchestrates the overall analysis process
   - Manages conversation context and user interactions
   - Coordinates between specialized agents

2. **Query Understanding & Planning Agent**
   - Classifies user queries
   - Generates execution plans
   - Routes tasks to appropriate specialized agents

3. **Specialized Analysis Agents**
   - Profitability Analysis Agent
   - Liquidity Analysis Agent
   - Efficiency Analysis Agent
   - Risk & Leverage Analysis Agent
   - Growth Analysis Agent

4. **Memory & Database Interaction Agent**
   - Manages data persistence
   - Handles vector database operations
   - Maintains time-series data
   - Manages document storage
   - Maintains knowledge graphs

5. **Insight Aggregation & Visualization Agent**
   - Compiles findings from specialized agents
   - Generates visualizations
   - Synthesizes cross-metric analysis

## Project Structure

```
company_financial_mas/
├── configs/                 # Configuration files
│   ├── agent_configs/      # Agent-specific configurations
│   └── database_configs/   # Database connection settings
├── data/                   # Data storage
│   ├── raw/               # Raw financial data
│   ├── processed/         # Processed data
│   └── embeddings/        # Vector embeddings
├── src/
│   └── aiq_financial_mas/
│       ├── agents/        # Agent implementations
│       ├── tools/         # Analysis tools
│       ├── database/      # Database interactions
│       ├── utils/         # Utility functions
│       └── prompts/       # LLM prompts
└── tests/                 # Test suite
```

## Setup and Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Usage

1. Start the system:
   ```bash
   python -m aiq_financial_mas.run
   ```

2. Interact with the system through the API or CLI interface.

## Features

- Multi-agent financial analysis
- Real-time data processing
- Advanced visualization capabilities
- Comprehensive financial metrics analysis
- Natural language query interface
- Automated report generation
- Historical data analysis
- Trend prediction
- Risk assessment
- Performance benchmarking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details. 