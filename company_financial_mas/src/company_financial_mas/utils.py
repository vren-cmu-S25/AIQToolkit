# SPDX-FileCopyrightText: Copyright (c) 2025. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Utility functions for the financial analysis multi-agent system.
"""

import json
import logging
import os
import pandas as pd
from typing import Dict, Any, Optional, List, Union

# Configure logging
logger = logging.getLogger("company_financial_mas")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Global variables for test data
_test_data = None
_benign_fallback_data = None

def log_header(message: str, dash_length: int = 80, level: int = logging.INFO) -> None:
    """
    Log a header message with dashes above and below.
    
    Args:
        message: The message to log as a header
        dash_length: The length of the dash line
        level: The logging level to use
    """
    dashes = "-" * dash_length
    logger.log(level, dashes)
    logger.log(level, message)
    logger.log(level, dashes)

def log_footer(dash_length: int = 80, level: int = logging.INFO) -> None:
    """
    Log a footer line of dashes.
    
    Args:
        dash_length: The length of the dash line
        level: The logging level to use
    """
    dashes = "-" * dash_length
    logger.log(level, dashes)

def preload_test_data(test_data_path: Optional[str] = None, 
                      benign_fallback_data_path: Optional[str] = None) -> None:
    """
    Preload test data for use in test mode.
    
    Args:
        test_data_path: Path to the main test dataset in CSV format
        benign_fallback_data_path: Path to JSON file with baseline/normal system behavior data
    """
    global _test_data, _benign_fallback_data
    
    if test_data_path and os.path.exists(test_data_path):
        logger.info(f"Loading test data from {test_data_path}")
        _test_data = pd.read_csv(test_data_path)
    else:
        logger.warning(f"Test data file not found at {test_data_path}")
        # Create empty test data
        _test_data = pd.DataFrame(columns=["query", "expected_answer"])
    
    if benign_fallback_data_path and os.path.exists(benign_fallback_data_path):
        logger.info(f"Loading benign fallback data from {benign_fallback_data_path}")
        with open(benign_fallback_data_path, 'r') as f:
            _benign_fallback_data = json.load(f)
    else:
        logger.warning(f"Benign fallback data file not found at {benign_fallback_data_path}")
        # Create empty fallback data
        _benign_fallback_data = {}

def get_test_data() -> pd.DataFrame:
    """
    Get the test data DataFrame.
    
    Returns:
        The test data DataFrame
    """
    global _test_data
    if _test_data is None:
        logger.warning("Test data not loaded, initializing empty DataFrame")
        _test_data = pd.DataFrame(columns=["query", "expected_answer"])
    return _test_data

def get_fallback_data(tool_name: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get fallback data for a specific tool call in test mode.
    
    Args:
        tool_name: The name of the tool being called
        query_params: The parameters for the tool call
    
    Returns:
        A dictionary with mock response data
    """
    global _benign_fallback_data
    if _benign_fallback_data is None:
        logger.warning("Benign fallback data not loaded, returning empty dict")
        return {}
    
    # Try to find the tool in the fallback data
    if tool_name in _benign_fallback_data:
        tool_data = _benign_fallback_data[tool_name]
        
        # Handle list-based pattern matching (legacy format)
        if isinstance(tool_data, list):
            query = query_params.get("query", "").lower()
            for pattern_data in tool_data:
                pattern = pattern_data.get("query_pattern", "").lower()
                if pattern and pattern in query:
                    logger.info(f"Found matching pattern '{pattern}' for query: {query}")
                    return pattern_data.get("data", {})
            
            # If no specific pattern matched, return the first entry as default if available
            if tool_data:
                logger.info(f"No specific pattern matched for query, using default data")
                return tool_data[0].get("data", {})
        
        # Handle get_schema_tool with direct table name lookup
        elif tool_name == "get_schema_tool" and "table_name" in query_params:
            table_name = query_params.get("table_name")
            if table_name in tool_data:
                logger.info(f"Found schema for table: {table_name}")
                return tool_data[table_name]
            else:
                logger.warning(f"No schema found for table: {table_name}")
                return {}
        
        # Handle db_query_tool with exact query matching
        elif tool_name == "db_query_tool" and "query" in query_params:
            query = query_params.get("query")
            # Try exact match first
            if query in tool_data:
                logger.info(f"Found exact match for query: {query}")
                return tool_data[query]
            
            # If no exact match, look for partial matches
            for stored_query, data in tool_data.items():
                # Check if words in the query match words in the stored query
                query_words = set(query.lower().split())
                stored_words = set(stored_query.lower().split())
                
                # If there's significant overlap, use this data
                overlap = query_words.intersection(stored_words)
                if len(overlap) > 3 or (len(overlap) > 0 and len(overlap) / len(query_words) > 0.5):
                    logger.info(f"Found partial match for query: {query}")
                    return data
            
            logger.warning(f"No matching query found for: {query}")
            return {}
        
        # For other tools or if direct lookup doesn't apply, return the data directly
        else:
            return tool_data
    
    logger.warning(f"No fallback data found for tool {tool_name}")
    return {}

def format_financial_number(value: Union[float, int], 
                          include_sign: bool = False, 
                          precision: int = 2,
                          abbreviate: bool = False) -> str:
    """
    Format a financial number with commas, signs, and optional abbreviation.
    
    Args:
        value: The number to format
        include_sign: Whether to include a + or - sign
        precision: The number of decimal places to include
        abbreviate: Whether to abbreviate large numbers (K, M, B)
    
    Returns:
        Formatted string representation of the number
    """
    if value is None:
        return "N/A"
    
    if abbreviate:
        if abs(value) >= 1_000_000_000:
            value = value / 1_000_000_000
            suffix = "B"
        elif abs(value) >= 1_000_000:
            value = value / 1_000_000
            suffix = "M"
        elif abs(value) >= 1_000:
            value = value / 1_000
            suffix = "K"
        else:
            suffix = ""
    else:
        suffix = ""
    
    formatted = f"{value:,.{precision}f}{suffix}"
    
    if include_sign and value > 0:
        formatted = f"+{formatted}"
    
    return formatted

def calculate_change(current: float, previous: float) -> Dict[str, Any]:
    """
    Calculate absolute and percentage change between two values.
    
    Args:
        current: The current value
        previous: The previous value
    
    Returns:
        Dictionary with absolute_change and percentage_change
    """
    if previous == 0:
        return {
            "absolute_change": current,
            "percentage_change": 0 if current == 0 else float('inf') * (1 if current > 0 else -1)
        }
    
    absolute_change = current - previous
    percentage_change = (absolute_change / abs(previous)) * 100
    
    return {
        "absolute_change": absolute_change,
        "percentage_change": percentage_change
    }

def calculate_financial_ratios(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate common financial ratios from financial statement data.
    
    Args:
        data: Dictionary containing financial statement values
    
    Returns:
        Dictionary of calculated financial ratios
    """
    ratios = {}
    
    # Profitability ratios
    if 'net_income' in data and 'revenue' in data and data['revenue'] != 0:
        ratios['net_profit_margin'] = data['net_income'] / data['revenue']
    
    if 'gross_profit' in data and 'revenue' in data and data['revenue'] != 0:
        ratios['gross_margin'] = data['gross_profit'] / data['revenue']
    
    if 'operating_income' in data and 'revenue' in data and data['revenue'] != 0:
        ratios['operating_margin'] = data['operating_income'] / data['revenue']
    
    if 'net_income' in data and 'total_assets' in data and data['total_assets'] != 0:
        ratios['return_on_assets'] = data['net_income'] / data['total_assets']
    
    if 'net_income' in data and 'shareholder_equity' in data and data['shareholder_equity'] != 0:
        ratios['return_on_equity'] = data['net_income'] / data['shareholder_equity']
    
    # Liquidity ratios
    if 'current_assets' in data and 'current_liabilities' in data and data['current_liabilities'] != 0:
        ratios['current_ratio'] = data['current_assets'] / data['current_liabilities']
    
    if all(k in data for k in ['current_assets', 'inventory', 'current_liabilities']) and data['current_liabilities'] != 0:
        ratios['quick_ratio'] = (data['current_assets'] - data['inventory']) / data['current_liabilities']
    
    if 'cash' in data and 'current_liabilities' in data and data['current_liabilities'] != 0:
        ratios['cash_ratio'] = data['cash'] / data['current_liabilities']
    
    # Efficiency ratios
    if 'revenue' in data and 'total_assets' in data and data['total_assets'] != 0:
        ratios['asset_turnover'] = data['revenue'] / data['total_assets']
    
    if 'cogs' in data and 'inventory' in data and data['inventory'] != 0:
        ratios['inventory_turnover'] = data['cogs'] / data['inventory']
    
    # Leverage ratios
    if 'total_liabilities' in data and 'total_assets' in data and data['total_assets'] != 0:
        ratios['debt_to_assets'] = data['total_liabilities'] / data['total_assets']
    
    if 'total_liabilities' in data and 'shareholder_equity' in data and data['shareholder_equity'] != 0:
        ratios['debt_to_equity'] = data['total_liabilities'] / data['shareholder_equity']
    
    if 'operating_income' in data and 'interest_expense' in data and data['interest_expense'] != 0:
        ratios['interest_coverage'] = data['operating_income'] / data['interest_expense']
    
    return ratios 