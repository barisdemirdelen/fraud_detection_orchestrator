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
    checker_type: FraudCheckerType
    image: Image | None = None
    fraud_detected: bool
    confidence_score: float
    reason: str


class FraudDetectionResult(BaseModel):
    intervention_id: uuid.UUID
    fraud_detected: bool
    confidence_score: float
    details: list[FraudCheckerDetail]
