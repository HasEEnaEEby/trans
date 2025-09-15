from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class IntentScore(BaseModel):
    label: str
    score: float


class Entity(BaseModel):
    type: str
    text: str
    start: Optional[int] = None
    end: Optional[int] = None
    confidence: Optional[float] = None
    value: Optional[float] = None
    currency: Optional[str] = None


class SuggestedAction(BaseModel):
    action: str
    label: str
    payload: Dict[str, Any]


class ProcessMagazineResponse(BaseModel):
    id: str
    original_text: str
    translated_text: str
    tokens: List[str]
    intent: IntentScore
    entities: List[Entity]
    suggested_actions: List[SuggestedAction]
    warnings: List[str]
    processing_time_ms: int


class TranslateRequest(BaseModel):
    text: str
    src_lang: str = Field(default="ja")
    tgt_lang: str = Field(default="en")


class TranslateResponse(BaseModel):
    translated_text: str


class PredictIntentRequest(BaseModel):
    text: str
    lang: str = Field(default="ja")
    top_k: int = Field(default=3, ge=1, le=10)


class PredictIntentResponse(BaseModel):
    scores: List[IntentScore]


class ExtractEntitiesRequest(BaseModel):
    text: str
    lang: str = Field(default="ja")


class ExtractEntitiesResponse(BaseModel):
    entities: List[Entity]


class UploadCorpusRequest(BaseModel):
    format: str = Field(pattern="^(json|csv)$")
    dataset_name: str
    notes: Optional[str] = None


class UploadCorpusResponse(BaseModel):
    job_id: str


class TrainTriggerRequest(BaseModel):
    task: str = Field(pattern="^(intent|ner)$")


class TrainTriggerResponse(BaseModel):
    job_id: str


class HealthResponse(BaseModel):
    status: str


class StatusResponse(BaseModel):
    status: str
    uptime_seconds: float
    model_versions: Dict[str, str]
