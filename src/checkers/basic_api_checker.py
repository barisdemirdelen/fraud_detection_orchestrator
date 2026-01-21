import asyncio

from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class BasicApiChecker(BaseChecker):
    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        # Simulate an api call
        await asyncio.sleep(0.5)

        return self.create_result(fraud_detected=False, fraud_rating=0.4)
