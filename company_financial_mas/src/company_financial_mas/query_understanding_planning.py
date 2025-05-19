# SPDX-FileCopyrightText: Copyright (c) 2025. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Query Understanding & Planning Agent module.

This module defines the Query Understanding & Planning agent that analyzes financial queries and
creates structured execution plans to engage appropriate specialized agents.
"""

import json
from typing import Dict, Any, List
from pydantic.fields import Field
from datetime import datetime

from langchain.tools import tool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from aiq.builder.builder import Builder
from aiq.builder.framework_enum import LLMFrameworkEnum
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig

from . import utils
from .prompts import QUERY_UNDERSTANDING_PLANNING_PROMPT


class QueryUnderstandingPlanningConfig(FunctionBaseConfig, name="query_understanding_planning"):
    """
    Configuration for the Query Understanding & Planning agent.
    """
    llm_name: LLMRef
    test_mode: bool = Field(default=True, description="Whether to run in test mode")


@register_function(config_type=QueryUnderstandingPlanningConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def query_understanding_planning_function(config: QueryUnderstandingPlanningConfig, builder: Builder):
    """
    Function to create and register the query understanding and planning agent.
    
    Args:
        config: Configuration for the query understanding and planning agent
        builder: AIQ builder instance
    
    Returns:
        Tool function wrapped for AIQ
    """
    # Get LLM for the query understanding and planning agent
    llm: BaseChatModel = await builder.get_llm(config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    @tool("query_understanding_planning", return_direct=False)
    async def query_understanding_planning_tool(query: str) -> str:
        """
        Analyze financial queries and create structured execution plans.
        This tool identifies relevant financial domains, determines which specialized agents to engage,
        and defines the specific data points and metrics needed to answer queries.
        
        Args:
            query: A financial query to analyze and plan for, such as "What's the relationship between our debt-to-equity ratio and profitability over the last 5 years?" or "How has our working capital efficiency changed since implementing the new ERP system?"
        
        Returns:
            A structured analysis and execution plan including relevant financial domains, required metrics, and recommended agent sequence
        """
        utils.logger.info(f"Analyzing query: {query}")
        
        try:
            if config.test_mode:
                # Check for mock data first
                mock_data = utils.get_fallback_data("query_understanding_planning", {"query": query})
                if mock_data:
                    if isinstance(mock_data, str):
                        return mock_data
                    else:
                        return json.dumps(mock_data, indent=2)
            
            # Prepare messages for the LLM
            system_msg = SystemMessage(content=QUERY_UNDERSTANDING_PLANNING_PROMPT)
            user_msg = HumanMessage(content=f"QUERY: {query}")
            
            # Get plan from LLM
            response = await llm.ainvoke([system_msg, user_msg])
            
            return response.content
        except Exception as e:
            utils.logger.error(f"Error in query analysis and planning: {e}")
            return f"Error analyzing query and creating plan: {str(e)}"

    yield query_understanding_planning_tool 