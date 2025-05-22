# SPDX-FileCopyrightText: Copyright (c) 2025. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
SQL Interaction Agent module.

This module defines the SQL Interaction agent that handles database queries,
providing tools for listing tables, retrieving schema information, and executing SQL queries.
"""

import json
import os
import pandas as pd
from typing import Dict, Any, Optional, List, Union
from pydantic.fields import Field
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlparse
from dotenv import load_dotenv

from langchain.tools import tool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

from aiq.builder.builder import Builder
from aiq.builder.framework_enum import LLMFrameworkEnum
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig
from aiq.profiler.decorators.function_tracking import track_function

from . import utils
from .prompts import SQL_INTERACTION_PROMPT

# Configuration for the ListTablesToolConfig
class ListTablesToolConfig(FunctionBaseConfig, name="list_tables_tool"):
    """
    Configuration for the list tables tool.
    """
    description: str = Field(
        default="List all available tables in the database.",
        description="Description of the tool for the agent.")
    test_mode: bool = Field(default=False, description="Whether to run in test mode")
    connection_string: Optional[str] = Field(
        default=None,
        description="Database connection string")
    db_env_path: Optional[str] = Field(
        default=None,
        description="Path to the database credentials .env file")
    benign_fallback_data_path: Optional[str] = Field(
        default=None, 
        description="Path to JSON file with baseline/normal system behavior data")

# Configuration for the GetSchemaToolConfig
class GetSchemaToolConfig(FunctionBaseConfig, name="get_schema_tool"):
    """
    Configuration for the get schema tool.
    """
    description: str = Field(
        default="Get the schema information for a specific table. Args: table_name: str",
        description="Description of the tool for the agent.")
    test_mode: bool = Field(default=False, description="Whether to run in test mode")
    connection_string: Optional[str] = Field(
        default=None,
        description="Database connection string")
    db_env_path: Optional[str] = Field(
        default=None,
        description="Path to the database credentials .env file")
    benign_fallback_data_path: Optional[str] = Field(
        default=None, 
        description="Path to JSON file with baseline/normal system behavior data")

# Configuration for the DBQueryToolConfig
class DBQueryToolConfig(FunctionBaseConfig, name="db_query_tool"):
    """
    Configuration for the database query tool.
    """
    description: str = Field(
        default="Execute a SQL query and return the results. Args: query: str",
        description="Description of the tool for the agent.")
    test_mode: bool = Field(default=False, description="Whether to run in test mode")
    connection_string: Optional[str] = Field(
        default=None,
        description="Database connection string")
    db_env_path: Optional[str] = Field(
        default=None,
        description="Path to the database credentials .env file")
    max_rows: int = Field(
        default=100,
        description="Maximum number of rows to return from a query")
    benign_fallback_data_path: Optional[str] = Field(
        default=None, 
        description="Path to JSON file with baseline/normal system behavior data")

# Configuration for the SQL Interaction Agent
class SQLInteractionConfig(FunctionBaseConfig, name="sql_interaction"):
    """
    Configuration for the SQL Interaction agent.
    """
    tool_names: list[str] = []
    llm_name: LLMRef
    agent_type: str = Field(
        default="react_agent", 
        description="Type of agent to use: 'react_agent' or 'tool_calling_agent'")
    test_mode: bool = Field(default=False, description="Whether to run in test mode")
    db_env_path: Optional[str] = Field(
        default=None,
        description="Path to the database credentials .env file")
    connection_string: Optional[str] = Field(
        default=None,
        description="Database connection string")
    max_rows: int = Field(
        default=100,
        description="Maximum number of rows to return from a query")
    test_data_path: Optional[str] = Field(
        default=None, 
        description="Path to the main test dataset in CSV format")
    benign_fallback_data_path: Optional[str] = Field(
        default=None, 
        description="Path to JSON file with baseline/normal system behavior data")


class DatabaseConnection:
    """
    Database connection manager for SQL Interaction agent.
    """
    def __init__(self, connection_string: Optional[str] = None, env_file_path: Optional[str] = None):
        """
        Initialize database connection manager.
        
        Args:
            connection_string: Direct connection string to the database
            env_file_path: Path to .env file containing connection details
        """
        self.connection_string = connection_string
        self.env_file_path = env_file_path
        self.conn = None
        
        # Load environment variables if env_file_path is provided
        if env_file_path:
            if os.path.exists(env_file_path):
                load_dotenv(env_file_path)
                
                # First try to get a complete connection string
                self.connection_string = os.getenv("TIMESCALE_SERVICE_URL")
                
                # If no connection string found, build it from individual components
                if not self.connection_string:
                    user = os.getenv("PGUSER")
                    password = os.getenv("PGPASSWORD")
                    host = os.getenv("PGHOST")
                    port = os.getenv("PGPORT")
                    dbname = os.getenv("PGDATABASE")
                    sslmode = os.getenv("PGSSLMODE", "require")
                    
                    if user and password and host and port and dbname:
                        self.connection_string = f"postgres://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
                    else:
                        utils.logger.error("Missing required database connection parameters in environment file")
            else:
                utils.logger.error(f"Environment file not found: {env_file_path}")
        else:
            utils.logger.warning("No environment file path provided")
    
    def connect(self):
        """
        Establish a connection to the database.
        
        Returns:
            Database connection object
        """
        if self.conn is None or self.conn.closed:
            try:
                if not self.connection_string:
                    utils.logger.error("No connection string available")
                    raise ValueError("No database connection string available")
                
                self.conn = psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)
                self.conn.autocommit = True
                utils.logger.info("Successfully connected to the database")
            except Exception as e:
                utils.logger.error(f"Error connecting to database: {e}")
                raise
        return self.conn
    
    def close(self):
        """
        Close the database connection.
        """
        if self.conn and not self.conn.closed:
            self.conn.close()
            utils.logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: Optional[Dict] = None, max_rows: int = 100) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a DataFrame.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            max_rows: Maximum number of rows to return
        
        Returns:
            DataFrame containing query results
        """
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                utils.logger.info(f"Executing query: {query}")
                cur.execute(query, params)
                if cur.description:  # Check if the query returns data
                    rows = cur.fetchmany(max_rows)
                    utils.logger.info(f"Query returned {len(rows)} rows")
                    return pd.DataFrame(rows)
                utils.logger.info("Query executed successfully (no result rows)")
                return pd.DataFrame()  # Empty DataFrame for non-SELECT queries
        except Exception as e:
            utils.logger.error(f"Error executing query: {e}")
            raise


@register_function(config_type=ListTablesToolConfig)
async def list_tables_tool_function(config: ListTablesToolConfig, builder: Builder):
    """
    Function to create and register the list tables tool.
    
    Args:
        config: Configuration for the list tables tool
        builder: AIQ builder instance
    
    Returns:
        Tool function wrapped for AIQ
    """
    # Initialize database connection
    db_conn = None
    
    if not config.test_mode:
        db_conn = DatabaseConnection(
            connection_string=config.connection_string,
            env_file_path=config.db_env_path
        )
    
    async def _arun(query: str) -> str:
        """
        List all available tables in the database.
        
        Args:
            query: A dummy parameter (not used but required by AIQ)
        
        Returns:
            JSON string containing a list of table names
        """
        utils.logger.info("Listing database tables")
        
        if config.test_mode:
            mock_data = utils.get_fallback_data("list_tables_tool", {})
            if mock_data:
                return json.dumps(mock_data)
            
            # Default fallback data for testing
            return json.dumps({
                "tables": [
                    "financial_metrics",
                    "cash_flow_metrics",
                    "annual_metrics",
                    "profit_by_quarter"
                ]
            })
        
        try:
            query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """
            
            result_df = db_conn.execute_query(query)
            tables = result_df['table_name'].tolist()
            
            return json.dumps({"tables": tables})
        except Exception as e:
            utils.logger.error(f"Error listing tables: {e}")
            return json.dumps({"error": str(e), "tables": []})

    try:
        yield FunctionInfo.from_fn(
            _arun,
            description=config.description,
        )
    finally:
        if db_conn:
            db_conn.close()


@register_function(config_type=GetSchemaToolConfig)
async def get_schema_tool_function(config: GetSchemaToolConfig, builder: Builder):
    """
    Function to create and register the get schema tool.
    
    Args:
        config: Configuration for the get schema tool
        builder: AIQ builder instance
    
    Returns:
        Tool function wrapped for AIQ
    """
    # Initialize database connection
    db_conn = None
    
    if not config.test_mode:
        db_conn = DatabaseConnection(
            connection_string=config.connection_string,
            env_file_path=config.db_env_path
        )
    
    async def _arun(table_name: str) -> str:
        """
        Get the schema information for a specific table.
        
        Args:
            table_name: Name of the table to get schema information for
        
        Returns:
            JSON string containing column names, data types, and constraints
        """
        utils.logger.info(f"Getting schema for table: {table_name}")
        
        try:
            # Get column information
            column_query = """
            SELECT 
                column_name, 
                data_type,
                is_nullable,
                column_default
            FROM 
                information_schema.columns
            WHERE 
                table_schema = 'public' AND 
                table_name = %(table_name)s
            ORDER BY 
                ordinal_position;
            """
            
            # Get constraint information
            constraint_query = """
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name
            FROM
                information_schema.table_constraints tc
            JOIN
                information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE
                tc.table_schema = 'public' AND
                tc.table_name = %(table_name)s;
            """
            
            # Check if it's a TimescaleDB hypertable
            hypertable_query = """
            SELECT * FROM timescaledb_information.hypertables
            WHERE hypertable_name = %(table_name)s;
            """
            
            # Check if it's a view
            view_query = """
            SELECT * FROM information_schema.views
            WHERE table_schema = 'public' AND table_name = %(table_name)s;
            """
            
            columns_df = db_conn.execute_query(column_query, {"table_name": table_name})
            constraints_df = db_conn.execute_query(constraint_query, {"table_name": table_name})
            hypertable_df = db_conn.execute_query(hypertable_query, {"table_name": table_name})
            view_df = db_conn.execute_query(view_query, {"table_name": table_name})
            
            # Process column information with constraints
            columns = []
            if not columns_df.empty:
                for _, col in columns_df.iterrows():
                    constraints = ""
                    column_name = col.get('column_name', '')
                    
                    if column_name:
                        if col.get('is_nullable') == 'NO':
                            constraints += "NOT NULL "
                        
                        # Add any other constraints from the constraints query
                        if not constraints_df.empty:
                            col_constraints = constraints_df[constraints_df['column_name'] == column_name]
                            for _, constraint in col_constraints.iterrows():
                                if constraint.get('constraint_type') == 'PRIMARY KEY':
                                    constraints += "PRIMARY KEY "
                                elif constraint.get('constraint_type') == 'FOREIGN KEY':
                                    constraints += "FOREIGN KEY "
                                elif constraint.get('constraint_type') == 'UNIQUE':
                                    constraints += "UNIQUE "
                        
                        columns.append({
                            "name": column_name,
                            "type": col.get('data_type', 'unknown'),
                            "constraints": constraints.strip()
                        })
            
            # If we couldn't get column info, try a simpler approach
            if not columns:
                simple_query = "SELECT * FROM information_schema.columns WHERE table_schema = 'public' AND table_name = %(table_name)s;"
                simple_df = db_conn.execute_query(simple_query, {"table_name": table_name})
                
                if not simple_df.empty:
                    for _, row in simple_df.iterrows():
                        columns.append({
                            "name": row.get('column_name', f"column_{_}"),
                            "type": row.get('data_type', 'unknown'),
                            "constraints": "unknown"
                        })
                
                # If still no columns, try a direct query to the table
                if not columns:
                    try:
                        sample_query = f"SELECT * FROM {table_name} LIMIT 1;"
                        sample_df = db_conn.execute_query(sample_query)
                        if not sample_df.empty:
                            for col_name in sample_df.columns:
                                columns.append({
                                    "name": col_name,
                                    "type": "unknown",
                                    "constraints": "unknown"
                                })
                    except Exception as e:
                        utils.logger.error(f"Error getting sample data: {e}")
            
            result = {
                "table_name": table_name,
                "columns": columns,
                "is_hypertable": not hypertable_df.empty,
                "is_view": not view_df.empty
            }
            
            # Add time dimension if it's a hypertable
            if not hypertable_df.empty and 'time_column_name' in hypertable_df.columns:
                time_col = hypertable_df.iloc[0].get('time_column_name')
                if time_col:
                    result["time_dimension"] = time_col
            
            return json.dumps(result)
        except Exception as e:
            utils.logger.error(f"Error getting schema for table {table_name}: {e}")
            
            # Return a basic error response with any information we have
            return json.dumps({
                "error": str(e),
                "table_name": table_name,
                "columns": []
            })

    try:
        yield FunctionInfo.from_fn(
            _arun,
            description=config.description,
        )
    finally:
        if db_conn:
            db_conn.close()


@register_function(config_type=DBQueryToolConfig)
async def db_query_tool_function(config: DBQueryToolConfig, builder: Builder):
    """
    Function to create and register the database query tool.
    
    Args:
        config: Configuration for the database query tool
        builder: AIQ builder instance
    
    Returns:
        Tool function wrapped for AIQ
    """
    # Initialize database connection
    db_conn = None
    
    if not config.test_mode:
        db_conn = DatabaseConnection(
            connection_string=config.connection_string,
            env_file_path=config.db_env_path
        )
    
    async def _arun(query: str) -> str:
        """
        Execute a SQL query and return the results.
        
        Args:
            query: SQL query to execute
        
        Returns:
            JSON string containing query results and metadata
        """
        # utils.logger.info(f"Executing query: {query}")
        
        # Basic SQL validation and sanitization
        try:
            # Parse and validate SQL
            parsed = sqlparse.parse(query)
            if not parsed:
                return json.dumps({"error": "Invalid SQL query"})
            
            # Check for dangerous operations in non-test mode
            if not config.test_mode:
                sql_lower = query.lower()
                if any(op in sql_lower for op in ["drop ", "truncate ", "delete ", "update ", "alter ", "create "]):
                    return json.dumps({
                        "error": "Data modification operations are not allowed. Only SELECT queries are permitted."
                    })
        except Exception as e:
            return json.dumps({"error": f"SQL parsing error: {str(e)}"})
        
        if config.test_mode:
            mock_data = utils.get_fallback_data("db_query_tool", {"query": query})
            if mock_data:
                return json.dumps(mock_data)
            
            # Default fallback data for testing
            # ... (rest of the mock data logic)
        
        try:
            import time
            start_time = time.time()
            
            result_df = db_conn.execute_query(query, max_rows=config.max_rows)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Convert DataFrame to list of dictionaries
            if not result_df.empty:
                rows = result_df.to_dict(orient='records')
                columns = list(result_df.columns)
                row_count = len(rows)
            else:
                rows = []
                columns = []
                row_count = 0
            
            return json.dumps({
                "columns": columns,
                "rows": rows,
                "row_count": row_count,
                "execution_time_ms": execution_time_ms
            })
        except Exception as e:
            utils.logger.error(f"Error executing query: {e}")
            return json.dumps({"error": str(e)})

    try:
        yield FunctionInfo.from_fn(
            _arun,
            description=config.description,
        )
    finally:
        if db_conn:
            db_conn.close()


async def _generate_sql_insights(llm: BaseChatModel, query_result: Dict[str, Any], query: str) -> str:
    """
    Generate insights from SQL query results using LLM.
    
    Args:
        llm: Language model to use for generating insights
        query_result: Results of the SQL query
        query: The original SQL query
    
    Returns:
        Insights and analysis text
    """
    # Format the data for the LLM
    data_str = json.dumps(query_result, indent=2)
    
    # Prepare messages for the LLM
    system_msg = SystemMessage(content=SQL_INTERACTION_PROMPT)
    user_msg = HumanMessage(content=f"QUERY: {query}\n\nSQL RESULT: {data_str}")
    
    # Get insights from LLM
    response = await llm.ainvoke([system_msg, user_msg])
    return response.content


@register_function(config_type=SQLInteractionConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def sql_interaction_workflow(config: SQLInteractionConfig, builder: Builder):
    """
    Function to create and register the SQL interaction agent workflow.
    
    Args:
        config: Configuration for the SQL interaction agent
        builder: AIQ builder instance
    
    Returns:
        Tool function wrapped for AIQ
    """
    # Preload test data if in test mode
    if config.test_mode:
        utils.preload_test_data(
            test_data_path=config.test_data_path,
            benign_fallback_data_path=config.benign_fallback_data_path
        )
    
    # Get LLM for the SQL interaction agent
    llm: BaseChatModel = await builder.get_llm(config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    
    # Get tools specified in config
    tools = builder.get_tools(config.tool_names, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Define assistant function that processes messages with the LLM
    async def sql_assistant(state: MessagesState):
        # Create system message with prompt
        sys_msg = SystemMessage(content=SQL_INTERACTION_PROMPT)
        # Invoke LLM with system message and conversation history
        return {"messages": [await llm_with_tools.ainvoke([sys_msg] + state["messages"])]}
    
    # Initialize state graph for managing conversation flow
    workflow_graph = StateGraph(MessagesState)
    
    # Add nodes to graph
    workflow_graph.add_node("sql_assistant", sql_assistant)
    workflow_graph.add_node("tools", ToolNode(tools))
    
    # Define graph edges to control conversation flow
    workflow_graph.add_edge(START, "sql_assistant")
    workflow_graph.add_conditional_edges(
        "sql_assistant",
        tools_condition,
    )
    workflow_graph.add_edge("tools", "sql_assistant")
    
    # Compile graph into executable agent
    agent_executor = workflow_graph.compile()
    
    @track_function()
    async def sql_interaction_agent(input_message: str) -> str:
        """
        SQL Interaction Agent that can list tables, get schema information, and execute SQL queries.
        This agent helps users interact with the financial database by translating natural language
        questions into SQL queries and executing them.
        
        Args:
            input_message: A natural language question about financial data, such as "What was our revenue trend over the last 3 quarters?" or "Show me the cash flow metrics for Q1 2024"
        
        Returns:
            Results of the database query with relevant insights
        """
        utils.logger.info(f"SQL Interaction Agent processing query: {input_message}")
        
        try:
            # Process the user query through the agent
            output = await agent_executor.ainvoke({"messages": [HumanMessage(content=input_message)]})
            result = output["messages"][-1].content
            return result
        except Exception as e:
            utils.logger.error(f"Error in SQL interaction agent: {e}")
            return f"Error processing SQL interaction: {str(e)}"

    try:
        yield sql_interaction_agent
    finally:
        # Cleanup code if needed
        utils.logger.info("Cleaning up SQL interaction agent resources") 