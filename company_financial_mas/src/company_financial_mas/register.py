# SPDX-FileCopyrightText: Copyright (c) 2025. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Main module to register the Financial Controller Agent workflow with the AIQ toolkit.
"""

import logging
import os
from typing import Dict, Any, List

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage
from langgraph.graph import START
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from pydantic.fields import Field

from aiq.builder.builder import Builder
from aiq.builder.framework_enum import LLMFrameworkEnum
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig
from aiq.profiler.decorators.function_tracking import track_function

# Import all tools and agents
from . import utils
from . import profitability_analysis
from . import query_understanding_planning
from . import response_generation
from .prompts import FINANCIAL_CONTROLLER_PROMPT


class FinancialControllerAgentConfig(FunctionBaseConfig, name="financial_controller_agent"):
    """
    Configuration for the Financial Controller Agent workflow. This agent orchestrates multiple specialized
    financial analysis agents to answer complex financial queries by:
    1. Understanding and planning the query analysis process
    2. Gathering data from appropriate financial sources
    3. Engaging specialized analysis agents for domain-specific insights
    4. Aggregating and synthesizing findings
    5. Generating a comprehensive financial response
    """
    tool_names: list[str] = []
    llm_name: LLMRef
    test_mode: bool = Field(default=True, description="Whether to run in test mode")
    test_data_path: str | None = Field(
        default="company_financial_mas/data/test/test_queries.csv",
        description="Path to the main test dataset in CSV format containing financial queries and expected results")
    test_output_path: str | None = Field(
        default=".tmp/aiq/company_financial_mas/output/test_output.csv",
        description="Path to save the test output CSV file")


@register_function(config_type=FinancialControllerAgentConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def financial_controller_agent_workflow(config: FinancialControllerAgentConfig, builder: Builder):
    """
    Main workflow function for the Financial Controller Agent.
    
    Args:
        config: Configuration for the financial controller agent
        builder: AIQ builder instance
    
    Returns:
        Async generator yielding the response function
    """
    # Get the main controller LLM
    llm: BaseChatModel = await builder.get_llm(config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    # Get tools for the controller agent
    tool_names = config.tool_names
    tools = []
    for tool_name in tool_names:
        tool = builder.get_tool(tool_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
        tools.append(tool)
    
    # Bind tools to the LLM
    llm_n_tools = llm.bind_tools(tools, parallel_tool_calls=True)

    # Define assistant function that processes messages with the LLM
    async def controller_assistant(state: MessagesState):
        """
        Financial controller assistant function that handles user queries through the LLM.
        
        Args:
            state: Current message state
        
        Returns:
            Updated message state with LLM response
        """
        # Create system message with prompt
        sys_msg = SystemMessage(content=FINANCIAL_CONTROLLER_PROMPT)
        # Invoke LLM with system message and conversation history
        return {"messages": [await llm_n_tools.ainvoke([sys_msg] + state["messages"])]}

    # Initialize state graph for managing conversation flow
    builder_graph = StateGraph(MessagesState)

    # Get tools specified in config
    tools = builder.get_tools(config.tool_names, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    # Add nodes to graph
    builder_graph.add_node("controller_assistant", controller_assistant)
    builder_graph.add_node("tools", ToolNode(tools))

    # Define graph edges to control conversation flow
    builder_graph.add_edge(START, "controller_assistant")
    builder_graph.add_conditional_edges(
        "controller_assistant",
        tools_condition,
    )
    builder_graph.add_edge("tools", "controller_assistant")

    # Compile graph into executable agent
    agent_executor = builder_graph.compile()

    @track_function()
    async def _process_query(input_message: str) -> str:
        """
        Process a financial query through the agent workflow.
        
        Args:
            input_message: User's financial query
        
        Returns:
            Detailed financial analysis response
        """
        utils.logger.info(f"Processing query: {input_message}")
        
        # Process query through agent
        output = await agent_executor.ainvoke({"messages": [HumanMessage(content=input_message)]})
        result = output["messages"][-1].content
        
        return result

    async def _response_fn(input_message: str) -> str:
        """
        Process financial query and return analysis.
        
        Args:
            input_message: User's financial query
        
        Returns:
            Detailed financial analysis response
        """
        try:
            result = await _process_query(input_message)
            return result
        finally:
            utils.logger.info("Finished agent execution")

    async def _response_test_fn(input_message: str) -> str:
        """
        Test mode response function that processes multiple queries from a CSV file.
        
        Args:
            input_message: Not used in test mode, queries are read from CSV instead
        
        Returns:
            Confirmation message after processing completes
        """
        if config.test_output_path is None:
            raise ValueError("test_output_path must be provided")

        # Load test queries from CSV file
        df = utils.get_test_data()
        df["output"] = ""  # Initialize output column
        utils.log_header(f"Processing {len(df)} Financial Queries")

        # Analyze each query and store results
        for i, (index, row) in enumerate(df.iterrows()):
            query = row["query"]
            utils.log_header(f"Query {i + 1}/{len(df)}", dash_length=50)
            utils.logger.info(query)
            report = await _process_query(query)
            df.loc[df.index == index, "output"] = report
            utils.log_footer(dash_length=50)

        utils.log_header("Saving Results")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(config.test_output_path), exist_ok=True)
        
        # Write results to output CSV
        df.to_csv(config.test_output_path, index=False)

        utils.log_footer()
        return f"Successfully processed {len(df)} financial queries. Results saved to {config.test_output_path}"

    try:
        if config.test_mode:
            utils.preload_test_data(test_data_path=config.test_data_path)
            utils.log_header("Running in test mode", dash_length=120, level=logging.INFO)
            yield _response_test_fn
        else:
            yield _response_fn

    except GeneratorExit:
        utils.logger.info("Exited early!")
    finally:
        utils.logger.info("Cleaning up") 