import asyncio

from fastapi import APIRouter

from src.checker_config import checkers
from src.checkers.base import BaseChecker
from src.schema import (
    FraudCheckerDetail,
    FraudDetectionResult,
    Intervention,
)

router = APIRouter(prefix="/fraud", tags=["fraud-detection"])


def calculate_fraud_score(results: list[FraudCheckerDetail]) -> tuple[bool, float]:
    # do some aggregation here
    # for now let's do simple weighted average
    total_score = sum(result.fraud_rating * result.result_weight for result in results)
    average_score = total_score / sum(result.result_weight for result in results)
    fraud_detected = any(result.fraud_detected for result in results)
    return fraud_detected, average_score


async def run_checkers(
    checkers: list[BaseChecker], intervention: Intervention
) -> FraudDetectionResult:
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
    return await run_checkers(checkers, intervention)
