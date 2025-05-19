# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

class ControllerPrompts:
    QUERY_UNDERSTANDING = """
    You are a financial analysis expert. Analyze the following user query and create an analysis plan:

    User Query: {query}

    Current Context: {current_context}

    Please provide a structured analysis plan that includes:
    1. Query classification (e.g., profitability, liquidity, risk, etc.)
    2. Required data points and metrics
    3. Analysis steps and sequence
    4. Required specialized agents
    5. Expected outputs and visualizations

    Format your response as a JSON object with the following structure:
    {{
        "query_type": "string",
        "required_metrics": ["string"],
        "analysis_steps": [
            {{
                "step": "string",
                "agent": "string",
                "inputs": ["string"],
                "outputs": ["string"]
            }}
        ],
        "visualizations": ["string"]
    }}
    """

    AGENT_COORDINATION = """
    You are coordinating multiple financial analysis agents. Based on the analysis plan and current results:

    Analysis Plan: {analysis_plan}
    Current Results: {current_results}

    Determine the next steps and agent assignments. Consider:
    1. Dependencies between analysis steps
    2. Data availability
    3. Priority of analysis components
    4. Resource constraints

    Format your response as a JSON object with the following structure:
    {{
        "next_steps": [
            {{
                "step": "string",
                "agent": "string",
                "priority": "high|medium|low",
                "dependencies": ["string"]
            }}
        ],
        "blocked_steps": ["string"],
        "completed_steps": ["string"]
    }}
    """

    RESULT_SYNTHESIS = """
    You are synthesizing results from multiple financial analysis agents. Review the following:

    Analysis Plan: {analysis_plan}
    Agent Results: {agent_results}

    Create a comprehensive synthesis that:
    1. Identifies key findings
    2. Highlights correlations between different metrics
    3. Points out potential concerns or opportunities
    4. Suggests actionable insights

    Format your response as a JSON object with the following structure:
    {{
        "key_findings": ["string"],
        "correlations": [
            {{
                "metrics": ["string"],
                "relationship": "string",
                "significance": "high|medium|low"
            }}
        ],
        "concerns": ["string"],
        "opportunities": ["string"],
        "recommendations": ["string"]
    }}
    """ 