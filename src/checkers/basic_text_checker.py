from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class BasicTextChecker(BaseChecker):
    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        if len(intervention.description) == 42:
            return self.create_result(
                fraud_detected=True,
                fraud_rating=0.7,
                reason="String length 42, so it is probably AI generated.",
            )

        return self.create_result(
            fraud_detected=False,
            fraud_rating=0.0,
            reason="No issues found in text content.",
        )
