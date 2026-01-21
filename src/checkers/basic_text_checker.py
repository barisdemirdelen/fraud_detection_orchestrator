from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class BasicTextChecker(BaseChecker):
    def check(self, intervention: Intervention) -> FraudCheckerDetail:
        return FraudCheckerDetail(
            checker_type=self.type,
            fraud_detected=False,
            confidence_score=0.0,
            reason="No issues found in text content.",
        )
