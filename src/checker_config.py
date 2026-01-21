"""
Fraud checker configuration and registry.

This module defines all the fraud checkers that will be used by the system.
"""

from src.checkers.basic_api_checker import BasicApiChecker
from src.checkers.basic_text_checker import BasicTextChecker
from src.checkers.image_ai_checker import ImageAiChecker
from src.checkers.image_exif_checker import ImageExifChecker
from src.schema import FraudCheckerType

# Registry of all fraud checkers
checkers = [
    # BasicTextChecker(type=FraudCheckerType.TEXT),
    # BasicApiChecker(type=FraudCheckerType.IMAGE, result_weight=4.0),
    ImageAiChecker(
        type=FraudCheckerType.IMAGE,
        api_endpoint="http://127.0.0.1:8080/analyze/ai-detection",
    ),
    ImageExifChecker(
        type=FraudCheckerType.IMAGE,
        api_endpoint="http://127.0.0.1:8080/analyze/exif",
    ),
]
