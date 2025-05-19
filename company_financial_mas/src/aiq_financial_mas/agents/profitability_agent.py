# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, List, Optional
from pydantic import Field

from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig

from ..utils.logging import log_header, log_footer, log_step
from ..prompts.profitability_prompts import ProfitabilityPrompts


class ProfitabilityAgentConfig(FunctionBaseConfig, name="profitability_analysis"):
    description: str = Field(
        default="Analyzes company profitability metrics and trends.",
        description="Description of the profitability analysis agent."
    )
    llm_name: LLMRef
    test_mode: bool = Field(default=True, description="Whether to run in test mode")


@register_function(config_type=ProfitabilityAgentConfig)
async def profitability_agent(config: ProfitabilityAgentConfig, builder: Builder):
    async def _arun(
        financial_data: Dict,
        metrics: Optional[List[str]] = None,
        time_period: Optional[str] = None
    ) -> Dict:
        log_header("Profitability Analysis Agent")

        try:
            # Default metrics if none specified
            if metrics is None:
                metrics = [
                    "gross_profit_margin",
                    "operating_profit_margin",
                    "net_profit_margin",
                    "return_on_assets",
                    "return_on_equity"
                ]

            # Get profitability analysis
            prompt = ProfitabilityPrompts.ANALYZE_PROFITABILITY.format(
                financial_data=str(financial_data),
                metrics=str(metrics),
                time_period=time_period or "latest"
            )

            # Get analysis from LLM
            analysis = await builder.llm_ainvoke(config.llm_name, prompt)

            # Process and structure the results
            results = {
                "metrics_analysis": analysis,
                "trends": _extract_trends(analysis),
                "recommendations": _generate_recommendations(analysis)
            }

            log_step("Analysis Complete", f"Analyzed {len(metrics)} profitability metrics")
            log_footer()
            return results

        except Exception as e:
            log_header("Error in Profitability Analysis", dash_length=50)
            raise e

    def _extract_trends(analysis: str) -> List[Dict]:
        """
        Extract trends from the analysis results.
        
        Args:
            analysis (str): The analysis results from the LLM
            
        Returns:
            List[Dict]: List of identified trends
        """
        # This would be implemented to parse the LLM response
        # and extract trend information
        return []

    def _generate_recommendations(analysis: str) -> List[str]:
        """
        Generate recommendations based on the analysis.
        
        Args:
            analysis (str): The analysis results from the LLM
            
        Returns:
            List[str]: List of recommendations
        """
        # This would be implemented to parse the LLM response
        # and generate actionable recommendations
        return []

    yield FunctionInfo.from_fn(
        _arun,
        description=config.description,
    ) 