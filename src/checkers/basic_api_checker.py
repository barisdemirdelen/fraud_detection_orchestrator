from src.checkers.base import BaseChecker
from src.schema import FraudCheckerDetail, Intervention


class BasicApiChecker(BaseChecker):
    def check(self, intervention: Intervention) -> FraudCheckerDetail:
        # result = api call()

        return FraudCheckerDetail(
            checker_type=self.type,
            fraud_detected=False,
            confidence_score=0.0,
            reason="Api returned no issues.",
        )
