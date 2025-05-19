# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import Field, BaseModel

from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig

from ..utils.logging import log_header, log_footer, log_step, log_error


class DatabaseConfig(BaseModel):
    """Configuration for database connections."""
    vector_db: Dict[str, Any]  # Pinecone/Weaviate config
    timescale_db: Dict[str, Any]  # TimescaleDB config
    document_db: Dict[str, Any]  # MongoDB config


class DBAgentConfig(FunctionBaseConfig, name="database_agent"):
    description: str = Field(
        default="Manages all database interactions for the financial analysis system.",
        description="Description of the database interaction agent."
    )
    llm_name: LLMRef
    db_config: DatabaseConfig
    test_mode: bool = Field(default=True, description="Whether to run in test mode")


@register_function(config_type=DBAgentConfig)
async def db_agent(config: DBAgentConfig, builder: Builder):
    async def _arun(
        operation: str,
        data: Dict,
        db_type: str = "vector",
        collection: Optional[str] = None,
        query: Optional[Dict] = None,
        time_range: Optional[Dict] = None
    ) -> Dict:
        """
        Unified database interaction function.

        Args:
            operation (str): The operation to perform (store, retrieve, update, delete)
            data (Dict): The data to operate on
            db_type (str): Type of database to use (vector, timescale, document)
            collection (Optional[str]): Collection/table name
            query (Optional[Dict]): Query parameters
            time_range (Optional[Dict]): Time range for time-series queries

        Returns:
            Dict: Operation results
        """
        log_header(f"Database Agent - {operation.upper()} Operation")

        try:
            if db_type == "vector":
                return await _handle_vector_db(operation, data, collection, query)
            elif db_type == "timescale":
                return await _handle_timescale_db(operation, data, collection, time_range)
            elif db_type == "document":
                return await _handle_document_db(operation, data, collection, query)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")

        except Exception as e:
            log_error(e, f"Database operation failed: {operation}")
            raise e
        finally:
            log_footer()

    async def _handle_vector_db(
        operation: str,
        data: Dict,
        collection: Optional[str],
        query: Optional[Dict]
    ) -> Dict:
        """Handle vector database operations."""
        log_step("Vector DB Operation", f"Collection: {collection}")

        if operation == "store":
            # Store embeddings and metadata
            return await _store_vector_data(data, collection)
        elif operation == "retrieve":
            # Semantic search
            return await _retrieve_vector_data(query, collection)
        elif operation == "update":
            # Update vector embeddings and metadata
            return await _update_vector_data(data, collection)
        elif operation == "delete":
            # Delete vectors
            return await _delete_vector_data(query, collection)
        else:
            raise ValueError(f"Unsupported vector DB operation: {operation}")

    async def _handle_timescale_db(
        operation: str,
        data: Dict,
        collection: Optional[str],
        time_range: Optional[Dict]
    ) -> Dict:
        """Handle time-series database operations."""
        log_step("Timescale DB Operation", f"Collection: {collection}")

        if operation == "store":
            # Store time-series data
            return await _store_timeseries_data(data, collection)
        elif operation == "retrieve":
            # Retrieve time-series data
            return await _retrieve_timeseries_data(collection, time_range)
        elif operation == "update":
            # Update time-series data
            return await _update_timeseries_data(data, collection)
        elif operation == "delete":
            # Delete time-series data
            return await _delete_timeseries_data(collection, time_range)
        else:
            raise ValueError(f"Unsupported timescale DB operation: {operation}")

    async def _handle_document_db(
        operation: str,
        data: Dict,
        collection: Optional[str],
        query: Optional[Dict]
    ) -> Dict:
        """Handle document database operations."""
        log_step("Document DB Operation", f"Collection: {collection}")

        if operation == "store":
            # Store documents
            return await _store_document_data(data, collection)
        elif operation == "retrieve":
            # Retrieve documents
            return await _retrieve_document_data(query, collection)
        elif operation == "update":
            # Update documents
            return await _update_document_data(data, collection)
        elif operation == "delete":
            # Delete documents
            return await _delete_document_data(query, collection)
        else:
            raise ValueError(f"Unsupported document DB operation: {operation}")

    # Vector DB Operations
    async def _store_vector_data(data: Dict, collection: str) -> Dict:
        """Store vector data with metadata."""
        # Implementation for storing vector data
        return {"status": "success", "operation": "store_vector"}

    async def _retrieve_vector_data(query: Dict, collection: str) -> Dict:
        """Retrieve vector data using semantic search."""
        # Implementation for retrieving vector data
        return {"status": "success", "operation": "retrieve_vector"}

    async def _update_vector_data(data: Dict, collection: str) -> Dict:
        """Update vector data and metadata."""
        # Implementation for updating vector data
        return {"status": "success", "operation": "update_vector"}

    async def _delete_vector_data(query: Dict, collection: str) -> Dict:
        """Delete vector data."""
        # Implementation for deleting vector data
        return {"status": "success", "operation": "delete_vector"}

    # Timescale DB Operations
    async def _store_timeseries_data(data: Dict, collection: str) -> Dict:
        """Store time-series data."""
        # Implementation for storing time-series data
        return {"status": "success", "operation": "store_timeseries"}

    async def _retrieve_timeseries_data(collection: str, time_range: Dict) -> Dict:
        """Retrieve time-series data."""
        # Implementation for retrieving time-series data
        return {"status": "success", "operation": "retrieve_timeseries"}

    async def _update_timeseries_data(data: Dict, collection: str) -> Dict:
        """Update time-series data."""
        # Implementation for updating time-series data
        return {"status": "success", "operation": "update_timeseries"}

    async def _delete_timeseries_data(collection: str, time_range: Dict) -> Dict:
        """Delete time-series data."""
        # Implementation for deleting time-series data
        return {"status": "success", "operation": "delete_timeseries"}

    # Document DB Operations
    async def _store_document_data(data: Dict, collection: str) -> Dict:
        """Store document data."""
        # Implementation for storing document data
        return {"status": "success", "operation": "store_document"}

    async def _retrieve_document_data(query: Dict, collection: str) -> Dict:
        """Retrieve document data."""
        # Implementation for retrieving document data
        return {"status": "success", "operation": "retrieve_document"}

    async def _update_document_data(data: Dict, collection: str) -> Dict:
        """Update document data."""
        # Implementation for updating document data
        return {"status": "success", "operation": "update_document"}

    async def _delete_document_data(query: Dict, collection: str) -> Dict:
        """Delete document data."""
        # Implementation for deleting document data
        return {"status": "success", "operation": "delete_document"}

    yield FunctionInfo.from_fn(
        _arun,
        description=config.description,
    ) 