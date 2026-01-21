import abc
import dataclasses
from abc import ABC

from src.schema import FraudCheckerDetail, FraudCheckerType, Image, Intervention


@dataclasses.dataclass
class BaseChecker(ABC):
    type: FraudCheckerType
    result_weight: float = 1.0

    @abc.abstractmethod
    async def check(
        self, intervention: Intervention
    ) -> FraudCheckerDetail | list[FraudCheckerDetail]: ...

    def create_result(
        self,
        fraud_detected: bool,
        fraud_rating: float,
        reason: str | None = None,
        image: Image | None = None,
    ) -> FraudCheckerDetail:
        if reason is None:
            reason = "No issues found."

        return FraudCheckerDetail(
            checker_type=self.type,
            fraud_detected=fraud_detected,
            fraud_rating=fraud_rating,
            reason=reason,
            result_weight=self.result_weight,
            image=image,
        )
