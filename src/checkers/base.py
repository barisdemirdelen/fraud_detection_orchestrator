import abc
import dataclasses
from abc import ABC

from src.schema import FraudCheckerDetail, FraudCheckerType, Intervention


@dataclasses.dataclass
class BaseChecker(ABC):
    type: FraudCheckerType

    @abc.abstractmethod
    def check(self, intervention: Intervention) -> FraudCheckerDetail: ...
