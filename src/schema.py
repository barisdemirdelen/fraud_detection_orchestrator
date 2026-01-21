import uuid
from enum import Enum

from pydantic import BaseModel


class Image(BaseModel):
    id: uuid.UUID
    url: str


class Intervention(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    images: list[Image]


class FraudCheckerType(Enum):
    INTERVENTION = "INTERVENTION"
    TEXT = "TEXT"
    IMAGE = "IMAGE"


class FraudCheckerDetail(BaseModel):
    checker_name: str
    checker_type: FraudCheckerType
    image: Image | None = None
    fraud_detected: bool
    fraud_rating: float
    reason: str
    result_weight: float


class FraudDetectionResult(BaseModel):
    intervention_id: uuid.UUID
    fraud_detected: bool
    fraud_rating: float
    details: list[FraudCheckerDetail]
