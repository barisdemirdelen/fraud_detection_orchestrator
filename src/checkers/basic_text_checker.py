from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class BasicTextChecker(BaseChecker):
    async def check(self, intervention: Intervention) -> FraudCheckerDetail:
        return FraudCheckerDetail(
            checker_type=self.type,
            fraud_detected=False,
            fraud_rating=0.0,
            reason="No issues found in text content.",
            result_weight=self.result_weight,
        )
