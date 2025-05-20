# SPDX-FileCopyrightText: Copyright (c) 2025. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Profitability Analysis Agent module.

This module defines the Profitability Analysis agent that analyzes various profitability metrics
such as revenue, costs, margins, and earnings.
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
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
from .prompts import PROFITABILITY_ANALYSIS_PROMPT


class ProfitabilityAnalysisConfig(FunctionBaseConfig, name="profitability_analysis"):
    """
    Configuration for the Profitability Analysis agent.
    """
    llm_name: LLMRef
    test_mode: bool = Field(default=True, description="Whether to run in test mode")
    test_data_path: Optional[str] = Field(
        default=None, 
        description="Path to the main test dataset in CSV format")
    benign_fallback_data_path: Optional[str] = Field(
        default=None, 
        description="Path to JSON file with baseline/normal system behavior data")


@register_function(config_type=ProfitabilityAnalysisConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def profitability_analysis_function(config: ProfitabilityAnalysisConfig, builder: Builder):
    """
    Function to create and register the profitability analysis agent.
    
    Args:
        config: Configuration for the profitability analysis agent
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
    
    # Get LLM for the profitability analysis agent
    llm: BaseChatModel = await builder.get_llm(config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    async def _analyze_profitability(query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal function to analyze profitability metrics.
        
        Args:
            query_params: Parameters for the profitability analysis
        
        Returns:
            Dictionary with profitability analysis results
        """
        if config.test_mode:
            # In test mode, use fallback data from JSON file
            mock_data = utils.get_fallback_data("profitability_analysis", query_params)
            if mock_data:
                return mock_data
            
            # If no specific mock data is found, return a default message
            utils.logger.warning("No matching fallback data found for query in profitability_analysis.json")
            return {
                "error": "No matching fallback data found for this query. Please update the fallback data JSON file."
            }
        else:
            # In live mode, retrieve actual profitability data
            # This would typically involve database queries or API calls to financial systems
            # For now, we'll just return a placeholder
            utils.logger.info("Live mode profitability analysis not implemented yet")
            return {"error": "Live mode profitability analysis not implemented yet"}

    async def _generate_profitability_insights(data: Dict[str, Any], query: str) -> str:
        """
        Generate insights from profitability data using LLM.
        
        Args:
            data: Profitability data and metrics
            query: The original query
        
        Returns:
            Insights and analysis text
        """
        # Format the data for the LLM
        data_str = json.dumps(data, indent=2)
        
        # Prepare messages for the LLM
        system_msg = SystemMessage(content=PROFITABILITY_ANALYSIS_PROMPT)
        user_msg = HumanMessage(content=f"QUERY: {query}\n\nPROFITABILITY DATA: {data_str}")
        
        # Get insights from LLM
        response = await llm.ainvoke([system_msg, user_msg])
        return response.content

    @track_function()
    async def profitability_analysis_tool(query: str) -> str:
        """
        Analyze company profitability metrics such as revenue, costs, margins, and earnings.
        This tool examines financial performance indicators like gross margin, operating margin,
        net profit margin, ROI, ROA, ROE, and other profitability ratios.
        
        Args:
            query: A specific question about company profitability, such as "What has been our gross margin trend over the last 4 quarters?" or "How does our operating margin compare to industry benchmarks?"
        
        Returns:
            Detailed analysis of relevant profitability metrics with insights and recommendations
        """
        utils.logger.info(f"Running profitability analysis for: {query}")
        
        try:
            # Extract parameters from the query for analysis
            query_params = {
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
            
            # Get profitability data
            profitability_data = await _analyze_profitability(query_params)
            
            # Generate insights using LLM
            insights = await _generate_profitability_insights(profitability_data, query)
            
            return insights
        except Exception as e:
            utils.logger.error(f"Error in profitability analysis: {e}")
            return f"Error performing profitability analysis: {str(e)}"

    try:
        # Use FunctionInfo.from_fn to properly wrap the function
        yield FunctionInfo.from_fn(
            profitability_analysis_tool, 
            description="Analyze company profitability metrics such as revenue, costs, margins, and earnings"
        )
    finally:
        # Cleanup code if needed (like closing connections)
        utils.logger.info("Cleaning up profitability analysis agent resources") 