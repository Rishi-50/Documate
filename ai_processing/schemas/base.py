from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ProcessingStage(str, Enum):
    PENDING = "PENDING"
    OCR = "OCR"
    INTELLIGENCE = "INTELLIGENCE"
    ORGANIZATION = "ORGANIZATION"
    EMBEDDING = "EMBEDDING"
    ASSISTANT = "ASSISTANT"
    COMPLETED = "COMPLETED"


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ProcessingResult(BaseModel):
    stage: ProcessingStage
    status: ProcessingStatus
    message: str
    execution_time: float = 0.0
    payload: Optional[Dict[str, Any]] = None