# SPDX-FileCopyrightText: Copyright (c) 2025. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Memory & Database Interaction Agent module.

This module defines the Memory & Database Interaction agent that handles retrieval
and storage of financial data across various database types.
"""

import json
import pandas as pd
import os
import psycopg2
import psycopg2.extras
from typing import Dict, Any, Optional, List, Union
from pydantic.fields import Field
from datetime import datetime

from langchain.tools import tool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from aiq.builder.builder import Builder
from aiq.builder.framework_enum import LLMFrameworkEnum
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig
from aiq.profiler.decorators.function_tracking import track_function

from . import utils
from .prompts import MEMORY_DATABASE_AGENT_PROMPT


class MemoryDatabaseInteractionConfig(FunctionBaseConfig, name="memory_database_interaction"):
    """
    Configuration for the Memory & Database Interaction agent.
    """
    llm_name: LLMRef
    test_mode: bool = Field(default=True, description="Whether to run in test mode")
    test_data_path: Optional[str] = Field(
        default=None, 
        description="Path to the main test dataset in CSV format")
    benign_fallback_data_path: Optional[str] = Field(
        default=None, 
        description="Path to JSON file with baseline/normal system behavior data")
    db_credentials_path: Optional[str] = Field(
        default=None,
        description="Path to TimescaleDB credentials file")


@register_function(config_type=MemoryDatabaseInteractionConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def memory_database_interaction_function(config: MemoryDatabaseInteractionConfig, builder: Builder):
    """
    Function to create and register the memory & database interaction agent.
    
    Args:
        config: Configuration for the memory & database interaction agent
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
    
    # Get LLM for the memory & database interaction agent
    llm: BaseChatModel = await builder.get_llm(config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    # Database connection parameters
    db_params = {}
    if not config.test_mode and config.db_credentials_path:
        try:
            # Load database credentials from env file
            with open(config.db_credentials_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            db_params[key] = value
            
            # Extract connection string
            if 'TIMESCALE_SERVICE_URL' in db_params:
                db_params['connection_string'] = db_params['TIMESCALE_SERVICE_URL']
            else:
                # Construct connection string from individual parameters
                db_params['connection_string'] = f"postgres://{db_params.get('PGUSER', '')}:{db_params.get('PGPASSWORD', '')}@{db_params.get('PGHOST', '')}:{db_params.get('PGPORT', '')}/" + \
                                               f"{db_params.get('PGDATABASE', '')}?sslmode={db_params.get('PGSSLMODE', 'require')}"
            
            utils.logger.info(f"Loaded database connection parameters from {config.db_credentials_path}")
        except Exception as e:
            utils.logger.error(f"Error loading database credentials: {e}")
            db_params = {}

    def get_db_connection():
        """
        Get a connection to the TimescaleDB.
        
        Returns:
            A psycopg2 connection object
        """
        if config.test_mode:
            utils.logger.warning("Attempt to connect to database in test mode")
            return None
        
        try:
            # Connect to the TimescaleDB
            connection = psycopg2.connect(db_params['connection_string'])
            utils.logger.info("Connected to TimescaleDB")
            return connection
        except Exception as e:
            utils.logger.error(f"Error connecting to TimescaleDB: {e}")
            return None

    async def _retrieve_from_database(query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal function to retrieve data from appropriate database(s).
        
        Args:
            query_params: Parameters for the data retrieval
        
        Returns:
            Dictionary with retrieved data
        """
        if config.test_mode:
            # In test mode, use fallback data from JSON file
            mock_data = utils.get_fallback_data("memory_database_interaction", query_params)
            if mock_data:
                return mock_data
            
            # If no specific mock data is found, return a default message
            utils.logger.warning("No matching fallback data found for query in memory_database_interaction.json")
            return {
                "error": "No matching fallback data found for this query. Please update the fallback data JSON file."
            }
        else:
            # In live mode, retrieve actual data from appropriate database
            db_type = query_params.get("db_type", "unknown")
            query = query_params.get("query", "")
            
            # Connect to TimescaleDB
            conn = get_db_connection()
            if not conn:
                return {"error": "Failed to connect to database"}
            
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                if db_type == "time_series":
                    # Time-series database (financial metrics)
                    utils.logger.info(f"Querying time-series database for: {query}")
                    
                    # Extract relevant keywords to determine which table to query
                    # This is a simplified approach - in a real implementation, you'd use
                    # more sophisticated query parsing or query templates
                    if "revenue" in query.lower():
                        sql_query = """
                        SELECT time_bucket('3 months', date) AS quarter, 
                               SUM(revenue) AS revenue, 
                               (SUM(revenue) - LAG(SUM(revenue)) OVER (ORDER BY time_bucket('3 months', date))) / 
                               NULLIF(LAG(SUM(revenue)) OVER (ORDER BY time_bucket('3 months', date)), 0) AS growth_rate
                        FROM financial_metrics
                        WHERE date >= NOW() - INTERVAL '2 years'
                        GROUP BY quarter
                        ORDER BY quarter DESC
                        LIMIT 8;
                        """
                    elif "margin" in query.lower() or "profit" in query.lower():
                        sql_query = """
                        SELECT time_bucket('3 months', date) AS quarter,
                               AVG(gross_margin) AS gross_margin,
                               AVG(operating_margin) AS operating_margin,
                               AVG(net_profit_margin) AS net_profit_margin
                        FROM financial_metrics
                        WHERE date >= NOW() - INTERVAL '2 years'
                        GROUP BY quarter
                        ORDER BY quarter DESC
                        LIMIT 8;
                        """
                    elif "cash flow" in query.lower():
                        sql_query = """
                        SELECT time_bucket('3 months', date) AS quarter,
                               SUM(operating_cash_flow) AS operating_cash_flow,
                               SUM(investing_cash_flow) AS investing_cash_flow,
                               SUM(financing_cash_flow) AS financing_cash_flow,
                               SUM(operating_cash_flow + investing_cash_flow + financing_cash_flow) AS net_cash_flow
                        FROM cash_flow_metrics
                        WHERE date >= NOW() - INTERVAL '2 years'
                        GROUP BY quarter
                        ORDER BY quarter DESC
                        LIMIT 8;
                        """
                    else:
                        # Generic financial metrics query
                        sql_query = """
                        SELECT time_bucket('3 months', date) AS quarter,
                               AVG(revenue) AS avg_revenue,
                               AVG(gross_margin) AS avg_gross_margin,
                               AVG(operating_margin) AS avg_operating_margin,
                               AVG(net_profit_margin) AS avg_net_profit_margin
                        FROM financial_metrics
                        WHERE date >= NOW() - INTERVAL '1 year'
                        GROUP BY quarter
                        ORDER BY quarter DESC
                        LIMIT 4;
                        """
                    
                    cursor.execute(sql_query)
                    result = cursor.fetchall()
                    
                    # Convert result to dict for JSON serialization
                    time_series_data = {
                        "data": [dict(row) for row in result],
                        "metadata": {
                            "source": "TimescaleDB",
                            "last_updated": datetime.now().isoformat(),
                            "query": sql_query
                        }
                    }
                    
                    return {"time_series_data": time_series_data}
                
                elif db_type == "vector":
                    # Vector database (embeddings)
                    utils.logger.info(f"Querying vector database for: {query}")
                    
                    # This assumes you have set up pgvector extension in TimescaleDB
                    # and have a table with embeddings stored
                    sql_query = """
                    SELECT id, content, metadata, 
                           embedding <-> pgvector_function(%) AS distance
                    FROM embeddings_table
                    ORDER BY distance
                    LIMIT 5;
                    """
                    
                    # Note: Actual implementation would require embedding the query first
                    # and then using that embedding in the search
                    # For simplicity, we're just showing a placeholder
                    
                    return {"error": "Vector database querying requires embedding generation first"}
                
                else:
                    # Non-TimescaleDB tables would be handled separately
                    return {"error": f"Database type {db_type} not supported by TimescaleDB connection"}
                
            except Exception as e:
                utils.logger.error(f"Error executing query: {e}")
                return {"error": f"Database query error: {str(e)}"}
            
            finally:
                # Close the database connection
                if conn:
                    conn.close()

    async def _update_database(query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal function to update data in appropriate database(s).
        
        Args:
            query_params: Parameters for the data update
        
        Returns:
            Dictionary with update result
        """
        if config.test_mode:
            # In test mode, pretend the update was successful
            mock_data = utils.get_fallback_data("memory_database_update", query_params)
            if mock_data:
                return mock_data
            
            # If no specific mock data is found, return a default success message
            return {
                "status": "success",
                "message": "Data update simulated in test mode",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # In live mode, update actual data in appropriate database
            db_type = query_params.get("db_type", "unknown")
            data = query_params.get("data", {})
            
            # Connect to TimescaleDB
            conn = get_db_connection()
            if not conn:
                return {"error": "Failed to connect to database"}
            
            try:
                cursor = conn.cursor()
                
                if db_type == "time_series":
                    # Time-series database (financial metrics)
                    utils.logger.info(f"Updating time-series database")
                    
                    # Implementation would depend on the exact structure of your data
                    # For now, just returning a placeholder
                    
                    return {"error": "Direct updates to time series database not implemented for security reasons"}
                
                elif db_type == "vector":
                    # Vector database (embeddings)
                    utils.logger.info(f"Updating vector database")
                    
                    # Implementation would depend on the exact structure of your data
                    # For now, just returning a placeholder
                    
                    return {"error": "Direct updates to vector database not implemented for security reasons"}
                
                else:
                    return {"error": f"Database type {db_type} not supported by TimescaleDB connection"}
                
            except Exception as e:
                utils.logger.error(f"Error executing update: {e}")
                return {"error": f"Database update error: {str(e)}"}
            
            finally:
                # Close the database connection
                if conn:
                    conn.close()

    async def _determine_data_requirements(query: str) -> Dict[str, Any]:
        """
        Use LLM to determine what data is needed to answer a query.
        
        Args:
            query: The user's query
        
        Returns:
            Dictionary with data requirements
        """
        system_msg = SystemMessage(content=MEMORY_DATABASE_AGENT_PROMPT)
        user_msg = HumanMessage(content=f"QUERY: {query}\n\nPlease determine what data sources and fields are needed to answer this query.")
        
        response = await llm.ainvoke([system_msg, user_msg])
        
        # Parse the response to extract data requirements
        try:
            # For demonstration purposes, assume the LLM returns a JSON string
            requirements = json.loads(response.content)
        except:
            # If parsing fails, use a simple heuristic approach
            requirements = {
                "data_sources": [],
                "fields": []
            }
            
            # Simple keyword matching for data sources
            if any(word in query.lower() for word in ["revenue", "profit", "margin", "income", "cost"]):
                requirements["data_sources"].append("time_series")
                requirements["fields"].extend(["revenue", "cost", "profit"])
            
            if any(word in query.lower() for word in ["report", "document", "filing"]):
                requirements["data_sources"].append("document")
            
            if any(word in query.lower() for word in ["relation", "connection", "linked", "associated"]):
                requirements["data_sources"].append("knowledge_graph")
            
            # Default to time-series if nothing else matches
            if not requirements["data_sources"]:
                requirements["data_sources"].append("time_series")
        
        return requirements

    @track_function()
    async def memory_database_interaction_tool(query: str, operation: str = "retrieve", data_source: str = "auto", data: str = None) -> str:
        """
        Memory & Database Interaction Agent that handles data retrieval and updates.
        This agent interacts with various database sources including time-series financial metrics, 
        documents, and vector storage to fetch or update data as needed.
        
        Args:
            query: The specific query or description of the data need
            operation: The operation to perform ("retrieve" or "update")
            data_source: The target data source (auto, time_series, document, vector)
            data: Optional data to store or update (for update operations only, in JSON format)
        
        Returns:
            Retrieved data or update confirmation in a structured format
        """
        utils.logger.info(f"Memory & Database Agent: Operation={operation}, Query={query}, Source={data_source}")
        
        try:
            if operation.lower() == "retrieve":
                # Data retrieval operation
                
                # Determine required data if not specified
                if data_source == "auto":
                    requirements = await _determine_data_requirements(query)
                    data_sources = requirements["data_sources"]
                else:
                    data_sources = [data_source]
                
                # Query parameters
                query_params = {
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Retrieve data from each required source
                results = {}
                for source in data_sources:
                    query_params["db_type"] = source
                    source_data = await _retrieve_from_database(query_params)
                    results[source] = source_data
                
                # Format response
                if len(results) == 1:
                    # If only one source, return directly
                    return json.dumps(list(results.values())[0], indent=2)
                else:
                    # If multiple sources, combine them
                    return json.dumps(results, indent=2)
                
            elif operation.lower() == "update":
                # Data update operation
                if not data_source or data_source == "auto":
                    return json.dumps({
                        "error": "Data source must be explicitly specified for update operations"
                    }, indent=2)
                
                if not data:
                    return json.dumps({
                        "error": "No data provided for update operation"
                    }, indent=2)
                
                # Parse the data
                if isinstance(data, str):
                    try:
                        parsed_data = json.loads(data)
                    except:
                        parsed_data = {"raw_content": data}
                else:
                    parsed_data = data
                
                # Query parameters
                query_params = {
                    "db_type": data_source,
                    "data": parsed_data,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Update the database
                result = await _update_database(query_params)
                
                # Format response
                return json.dumps(result, indent=2)
                
            else:
                # Unknown operation
                return json.dumps({
                    "error": f"Unknown operation: {operation}. Supported operations are 'retrieve' and 'update'."
                }, indent=2)
                
        except Exception as e:
            utils.logger.error(f"Error in memory database interaction: {e}")
            return json.dumps({
                "error": f"Error in memory database interaction: {str(e)}"
            }, indent=2)

    try:
        # Return the unified memory database interaction tool
        yield FunctionInfo.from_fn(
            memory_database_interaction_tool, 
            description="Interact with financial databases to retrieve or update data across various sources"
        )
    finally:
        # Cleanup code if needed (like closing connections)
        utils.logger.info("Cleaning up memory & database interaction agent resources") 