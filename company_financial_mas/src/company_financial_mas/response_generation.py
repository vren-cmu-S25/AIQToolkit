# SPDX-FileCopyrightText: Copyright (c) 2025. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Response Generation Agent module.

This module defines the Response Generation agent responsible for formatting financial insights
into clear, user-friendly responses with appropriate visualizations.
"""

import json
from typing import Dict, Any, List
from pydantic.fields import Field

from langchain.tools import tool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from aiq.builder.builder import Builder
from aiq.builder.framework_enum import LLMFrameworkEnum
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig

from . import utils
from .prompts import RESPONSE_GENERATION_PROMPT


class ResponseGenerationConfig(FunctionBaseConfig, name="response_generation"):
    """
    Configuration for the Response Generation agent.
    """
    llm_name: LLMRef
    test_mode: bool = Field(default=True, description="Whether to run in test mode")


@register_function(config_type=ResponseGenerationConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def response_generation_function(config: ResponseGenerationConfig, builder: Builder):
    """
    Function to create and register the response generation agent.
    
    Args:
        config: Configuration for the response generation agent
        builder: AIQ builder instance
    
    Returns:
        Tool function wrapped for AIQ
    """
    # Get LLM for the response generation agent
    llm: BaseChatModel = await builder.get_llm(config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    @tool("response_generation", return_direct=False)
    async def response_generation_tool(query: str, aggregated_insights: str) -> str:
        """
        Format financial insights into clear, user-friendly responses with appropriate visualizations.
        This tool translates technical financial analysis into accessible language, selects appropriate
        visualization formats, and adapts responses to the user's financial sophistication level.
        
        Args:
            query: The original financial query
            aggregated_insights: Comprehensive insights from the aggregation agent
        
        Returns:
            User-friendly financial analysis with visualization recommendations and supporting evidence
        """
        utils.logger.info(f"Generating response for query: {query}")
        
        try:
            if config.test_mode:
                # Check for mock data
                mock_data = utils.get_fallback_data("response_generation", {"query": query})
                if mock_data:
                    if isinstance(mock_data, str):
                        return mock_data
                    else:
                        return json.dumps(mock_data, indent=2)
            
            # Prepare messages for the LLM
            system_msg = SystemMessage(content=RESPONSE_GENERATION_PROMPT)
            user_msg = HumanMessage(content=f"QUERY: {query}\n\nAGGREGATED INSIGHTS: {aggregated_insights}")
            
            # Get formatted response from LLM
            response = await llm.ainvoke([system_msg, user_msg])
            
            return response.content
        except Exception as e:
            utils.logger.error(f"Error in response generation: {e}")
            return f"Error generating response: {str(e)}"

    yield response_generation_tool 