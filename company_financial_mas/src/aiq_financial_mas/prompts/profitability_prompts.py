# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

class ProfitabilityPrompts:
    ANALYZE_PROFITABILITY = """
    You are a financial analysis expert specializing in profitability analysis. Analyze the following financial data:

    Financial Data: {financial_data}
    Metrics to Analyze: {metrics}
    Time Period: {time_period}

    Please provide a comprehensive analysis that includes:
    1. Calculation and interpretation of each profitability metric
    2. Comparison with industry benchmarks
    3. Trend analysis over the specified time period
    4. Identification of key drivers affecting profitability
    5. Potential areas for improvement

    Format your response as a JSON object with the following structure:
    {{
        "metrics_analysis": [
            {{
                "metric": "string",
                "value": "number",
                "benchmark": "number",
                "interpretation": "string",
                "trend": "improving|stable|declining"
            }}
        ],
        "key_drivers": [
            {{
                "driver": "string",
                "impact": "positive|negative|neutral",
                "magnitude": "high|medium|low"
            }}
        ],
        "improvement_areas": [
            {{
                "area": "string",
                "potential_impact": "string",
                "difficulty": "high|medium|low"
            }}
        ]
    }}
    """

    COMPARE_PROFITABILITY = """
    Compare the profitability metrics between two time periods or companies:

    Current Data: {current_data}
    Comparison Data: {comparison_data}
    Metrics: {metrics}

    Please provide a comparative analysis that includes:
    1. Percentage changes in each metric
    2. Relative performance analysis
    3. Key factors driving differences
    4. Implications for business strategy

    Format your response as a JSON object with the following structure:
    {{
        "comparative_analysis": [
            {{
                "metric": "string",
                "current_value": "number",
                "comparison_value": "number",
                "change_percentage": "number",
                "significance": "high|medium|low"
            }}
        ],
        "key_differences": [
            {{
                "factor": "string",
                "impact": "string",
                "recommendation": "string"
            }}
        ]
    }}
    """

    FORECAST_PROFITABILITY = """
    Based on historical data and current trends, forecast future profitability:

    Historical Data: {historical_data}
    Current Trends: {current_trends}
    Forecast Period: {forecast_period}

    Please provide a forecast that includes:
    1. Projected values for key profitability metrics
    2. Confidence levels for each projection
    3. Key assumptions made
    4. Potential risks and opportunities

    Format your response as a JSON object with the following structure:
    {{
        "forecast": [
            {{
                "metric": "string",
                "projected_value": "number",
                "confidence_level": "high|medium|low",
                "assumptions": ["string"]
            }}
        ],
        "risks": [
            {{
                "risk": "string",
                "probability": "high|medium|low",
                "impact": "high|medium|low"
            }}
        ],
        "opportunities": [
            {{
                "opportunity": "string",
                "potential_impact": "string",
                "feasibility": "high|medium|low"
            }}
        ]
    }}
    """ 