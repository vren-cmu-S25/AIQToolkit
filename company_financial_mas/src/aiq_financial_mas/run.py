# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
from typing import Dict, Optional

from aiq.builder.builder import Builder
from aiq.cli.register_workflow import register_workflow
from aiq.data_models.component_ref import LLMRef

from .agents.controller_agent import ControllerAgentConfig, controller_agent
from .agents.profitability_agent import ProfitabilityAgentConfig, profitability_agent
from .utils.logging import log_header, log_footer, log_step


@register_workflow
async def financial_analysis_workflow(
    query: str,
    llm_name: LLMRef,
    test_mode: bool = True,
    context: Optional[Dict] = None
) -> Dict:
    """
    Main workflow for financial analysis.

    Args:
        query (str): The user's financial analysis query
        llm_name (LLMRef): The LLM to use for analysis
        test_mode (bool): Whether to run in test mode
        context (Optional[Dict]): Additional context for the analysis

    Returns:
        Dict: The analysis results
    """
    log_header("Financial Analysis Workflow")

    try:
        # Initialize the builder
        builder = Builder()

        # Configure the controller agent
        controller_config = ControllerAgentConfig(
            llm_name=llm_name,
            test_mode=test_mode
        )

        # Configure the profitability agent
        profitability_config = ProfitabilityAgentConfig(
            llm_name=llm_name,
            test_mode=test_mode
        )

        # Register the agents
        controller_fn = await controller_agent(controller_config, builder)
        profitability_fn = await profitability_agent(profitability_config, builder)

        # Execute the analysis
        log_step("Starting Analysis", f"Processing query: {query}")
        
        # Get the analysis plan from the controller
        analysis_context = await controller_fn(query, context)
        
        # Execute the analysis plan
        results = await _execute_analysis_plan(
            analysis_context,
            builder,
            {
                "profitability": profitability_fn
            }
        )

        log_step("Analysis Complete", "Generating final report")
        log_footer()
        
        return results

    except Exception as e:
        log_header("Error in Financial Analysis Workflow", dash_length=50)
        raise e


async def _execute_analysis_plan(
    context: Dict,
    builder: Builder,
    agents: Dict
) -> Dict:
    """
    Execute the analysis plan using the appropriate agents.

    Args:
        context (Dict): The analysis context and plan
        builder (Builder): The AIQ builder instance
        agents (Dict): Dictionary of available analysis agents

    Returns:
        Dict: The analysis results
    """
    results = {
        "query": context["query"],
        "analysis_results": {},
        "recommendations": []
    }

    # Execute each step in the analysis plan
    for step in context["analysis_plan"]["analysis_steps"]:
        agent_name = step["agent"]
        if agent_name in agents:
            agent_fn = agents[agent_name]
            step_results = await agent_fn(
                financial_data=context.get("financial_data", {}),
                metrics=step.get("inputs", []),
                time_period=context.get("time_period")
            )
            results["analysis_results"][step["step"]] = step_results

    return results


if __name__ == "__main__":
    # Example usage
    async def main():
        query = "Analyze our company's profitability trends over the last quarter"
        results = await financial_analysis_workflow(
            query=query,
            llm_name=LLMRef(name="gpt-4"),
            test_mode=True
        )
        print(json.dumps(results, indent=2))

    asyncio.run(main()) 