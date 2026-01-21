import asyncio

from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class BasicApiChecker(BaseChecker):
    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        # result = api call()

        await asyncio.sleep(0.5)

        return FraudCheckerDetail(
            checker_type=self.type,
            fraud_detected=False,
            fraud_rating=0.4,
            reason="Api returned no issues.",
            result_weight=self.result_weight,
        )
