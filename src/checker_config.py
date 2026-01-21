"""
Fraud checker configuration and registry.

This module defines all the fraud checkers that will be used by the system.
"""

from src.checkers.basic_api_checker import BasicApiChecker
from src.checkers.basic_text_checker import BasicTextChecker
from src.schema import FraudCheckerType

# Registry of all fraud checkers
checkers = [
    BasicTextChecker(type=FraudCheckerType.TEXT),
    BasicApiChecker(type=FraudCheckerType.IMAGE, result_weight=4.0),
]
