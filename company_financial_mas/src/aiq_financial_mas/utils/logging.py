# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def log_header(title: str, dash_length: int = 80) -> None:
    """
    Log a header with a title and dashes.

    Args:
        title (str): The title to display in the header
        dash_length (int): The length of the dash line
    """
    logger.info("=" * dash_length)
    logger.info(f"{title}")
    logger.info("=" * dash_length)


def log_footer(dash_length: int = 80) -> None:
    """
    Log a footer with dashes.

    Args:
        dash_length (int): The length of the dash line
    """
    logger.info("=" * dash_length)


def log_step(step: str, details: Optional[str] = None) -> None:
    """
    Log a step in the process with optional details.

    Args:
        step (str): The step description
        details (Optional[str]): Additional details about the step
    """
    logger.info(f"Step: {step}")
    if details:
        logger.info(f"Details: {details}")


def log_error(error: Exception, context: Optional[str] = None) -> None:
    """
    Log an error with optional context.

    Args:
        error (Exception): The error to log
        context (Optional[str]): Additional context about the error
    """
    logger.error(f"Error: {str(error)}")
    if context:
        logger.error(f"Context: {context}")


def log_result(result: str, level: str = "info") -> None:
    """
    Log a result with specified level.

    Args:
        result (str): The result to log
        level (str): The logging level (debug, info, warning, error, critical)
    """
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"Result: {result}") 