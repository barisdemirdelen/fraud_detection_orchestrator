from fastapi import APIRouter

from src.checkers.basic_api_checker import BasicApiChecker
from src.checkers.basic_text_checker import BasicTextChecker
from src.schema import (
    FraudCheckerDetail,
    FraudCheckerType,
    FraudDetectionResult,
    Intervention,
)

router = APIRouter(prefix="/fraud", tags=["fraud-detection"])

checkers = [
    BasicTextChecker(type=FraudCheckerType.TEXT),
    BasicApiChecker(type=FraudCheckerType.IMAGE),
]


def calculate_fraud_score(results: list[FraudCheckerDetail]) -> tuple[bool, float]:
    # do some aggregation here
    # for now let's do simple average
    total_score = sum(result.confidence_score for result in results)
    average_score = total_score / len(results)
    fraud_detected = any(result.fraud_detected for result in results)
    return fraud_detected, average_score


def run_checkers(intervention: Intervention) -> FraudDetectionResult:
    results = []
    for checker in checkers:
        result = checker.check(intervention)
        results.append(result)

    fraud_detected, confidence_score = calculate_fraud_score(results)

    return FraudDetectionResult(
        intervention_id=intervention.id,
        fraud_detected=fraud_detected,
        confidence_score=confidence_score,
        details=results,
    )


@router.post("/detect")
async def detect_fraud(intervention: Intervention) -> FraudDetectionResult:
    return run_checkers(intervention)
