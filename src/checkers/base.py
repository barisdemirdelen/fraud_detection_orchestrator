import abc
import dataclasses
from abc import ABC

from src.schema import FraudCheckerDetail, FraudCheckerType, Intervention


@dataclasses.dataclass
class BaseChecker(ABC):
    type: FraudCheckerType
    result_weight: float = 1.0

    @abc.abstractmethod
    async def check(self, intervention: Intervention) -> FraudCheckerDetail: ...
