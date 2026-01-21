import asyncio

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
    BasicApiChecker(type=FraudCheckerType.IMAGE, result_weight=4.0),
]


def calculate_fraud_score(results: list[FraudCheckerDetail]) -> tuple[bool, float]:
    # do some aggregation here
    # for now let's do simple weighted average
    total_score = sum(result.fraud_rating * result.result_weight for result in results)
    average_score = total_score / sum(result.result_weight for result in results)
    fraud_detected = any(result.fraud_detected for result in results)
    return fraud_detected, average_score


async def run_checkers(intervention: Intervention) -> FraudDetectionResult:
    tasks = []
    for checker in checkers:
        task = checker.check(intervention)
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    fraud_detected, fraud_rating = calculate_fraud_score(results)

    return FraudDetectionResult(
        intervention_id=intervention.id,
        fraud_detected=fraud_detected,
        fraud_rating=fraud_rating,
        details=results,
    )


@router.post("/detect")
async def detect_fraud(intervention: Intervention) -> FraudDetectionResult:
    return await run_checkers(intervention)
