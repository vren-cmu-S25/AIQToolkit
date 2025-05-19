# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, List, Optional
from pydantic import Field

from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig

from ..utils.logging import log_header, log_footer
from ..prompts.controller_prompts import ControllerPrompts


class ControllerAgentConfig(FunctionBaseConfig, name="financial_controller"):
    description: str = Field(
        default="The main controller agent that orchestrates the financial analysis process.",
        description="Description of the controller agent."
    )
    llm_name: LLMRef
    test_mode: bool = Field(default=True, description="Whether to run in test mode")


@register_function(config_type=ControllerAgentConfig)
async def controller_agent(config: ControllerAgentConfig, builder: Builder):
    async def _arun(query: str, context: Optional[Dict] = None) -> Dict:
        log_header("Financial Controller Agent")

        try:
            # Initialize context if not provided
            if context is None:
                context = {
                    "query": query,
                    "analysis_results": {},
                    "current_step": "query_understanding",
                    "next_steps": []
                }

            # Get query understanding and planning
            prompt = ControllerPrompts.QUERY_UNDERSTANDING.format(
                query=query,
                current_context=str(context)
            )

            # Get analysis plan from LLM
            analysis_plan = await builder.llm_ainvoke(config.llm_name, prompt)

            # Update context with analysis plan
            context["analysis_plan"] = analysis_plan

            # Execute the analysis plan
            # This will be implemented to coordinate with other agents
            # based on the analysis plan

            log_footer()
            return context

        except Exception as e:
            log_header("Error in Controller Agent", dash_length=50)
            raise e

    yield FunctionInfo.from_fn(
        _arun,
        description=config.description,
    ) 