import io
import time
import hashlib
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, RedirectResponse, Response

from app.core.config import settings, VersionInfo
from app.core.auth import get_current_user, require_admin
from app.models.schemas import (
    ProcessMagazineResponse,
    TranslateRequest,
    TranslateResponse,
    PredictIntentRequest,
    PredictIntentResponse,
    ExtractEntitiesRequest,
    ExtractEntitiesResponse,
    UploadCorpusRequest,
    UploadCorpusResponse,
    TrainTriggerRequest,
    TrainTriggerResponse,
    HealthResponse,
    StatusResponse,
    IntentScore,
    SuggestedAction,
)
from app.utils.logging import configure_logging, logger
from app.utils.rate_limit import rate_limit_dep
from app.utils.tracing import setup_tracing
from app.utils.cache import cache
from app.utils.av_scan import scanner
from app.middleware.security import SecurityHeadersMiddleware
from app.services.ocr import OcrService
from app.services.tokenizer import TokenizerService
from app.services.translation import TranslationService
from app.services.intent import IntentService
from app.services.ner import NerService

from prometheus_fastapi_instrumentator import Instrumentator


configure_logging()
app = FastAPI(title="Magazine AI Backend", version="0.1.0")

setup_tracing(app)
Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.add_middleware(SecurityHeadersMiddleware)

ocr_service = OcrService()
_tok = TokenizerService()
trans_service = TranslationService()
intent_service = IntentService()
ner_service = NerService()

_start_time = time.time()
_version = VersionInfo()


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


@app.get("/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/v1/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    uptime = time.time() - _start_time
    return StatusResponse(
        status="ok",
        uptime_seconds=uptime,
        model_versions={
            "translation": _version.translation_model,
            "intent": _version.intent_model,
            "ner": _version.ner_model,
        },
    )


@app.post("/v1/translate", response_model=TranslateResponse, dependencies=[Depends(rate_limit_dep)])
async def translate(req: TranslateRequest) -> TranslateResponse:
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")
    ckey = cache.hash_key(["translate", req.src_lang, req.tgt_lang, text])
    cached = cache.get_json(ckey)
    if cached:
        return TranslateResponse(**cached)
    translated = trans_service.translate(text, req.src_lang, req.tgt_lang)
    resp = TranslateResponse(translated_text=translated)
    cache.set_json(ckey, resp.model_dump())
    return resp


@app.post("/v1/predict-intent", response_model=PredictIntentResponse, dependencies=[Depends(rate_limit_dep)])
async def predict_intent(req: PredictIntentRequest) -> PredictIntentResponse:
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")
    scores = intent_service.predict(text, top_k=req.top_k)
    return PredictIntentResponse(scores=[IntentScore(label=l, score=s) for l, s in scores])


@app.post("/v1/extract-entities", response_model=ExtractEntitiesResponse, dependencies=[Depends(rate_limit_dep)])
async def extract_entities(req: ExtractEntitiesRequest) -> ExtractEntitiesResponse:
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")
    ents = ner_service.extract(text)
    return ExtractEntitiesResponse(entities=ents)


@app.post("/v1/process-magazine", response_model=ProcessMagazineResponse, dependencies=[Depends(rate_limit_dep)])
async def process_magazine(
    file: UploadFile = File(...),
    target_language: str = Form(default="en"),
    user_id: Optional[str] = Form(default=None),
) -> ProcessMagazineResponse:
    start = time.time()

    if file.content_type not in {"image/jpeg", "image/png", "application/pdf"}:
        raise HTTPException(status_code=415, detail="Unsupported media type")

    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Payload too large")
    try:
        scanner.scan_bytes(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Infected file detected")

    req_id = hashlib.sha256(content).hexdigest()[:16]

    ckey = cache.hash_key(["process", target_language, req_id])
    cached = cache.get_json(ckey)
    if cached:
        return ProcessMagazineResponse(**cached)

    original_text = ocr_service.extract_text(content)
    tokens = _tok.tokenize(original_text)
    translated = trans_service.translate(original_text, src_lang="ja", tgt_lang=target_language)
    intent_scores = intent_service.predict(original_text, top_k=1)
    top_intent = IntentScore(label=intent_scores[0][0], score=round(intent_scores[0][1], 2))
    entities = ner_service.extract(original_text)

    actions = []
    if entities:
        query = original_text[:120]
        actions.append(
            SuggestedAction(
                action="search_online",
                label="Search this product online",
                payload={"query": query},
            )
        )

    elapsed_ms = int((time.time() - start) * 1000)
    resp = ProcessMagazineResponse(
        id=req_id,
        original_text=original_text,
        translated_text=translated,
        tokens=tokens,
        intent=top_intent,
        entities=entities,
        suggested_actions=actions,
        warnings=[],
        processing_time_ms=elapsed_ms,
    )
    cache.set_json(ckey, resp.model_dump())
    return resp


@app.post("/v1/upload-corpus", response_model=UploadCorpusResponse, dependencies=[Depends(rate_limit_dep)])
async def upload_corpus(
    req: UploadCorpusRequest,
    user=Depends(get_current_user),
) -> UploadCorpusResponse:
    dataset = req.dataset_name
    job_id = hashlib.sha256(f"{dataset}:{user.get('sub','')}:{time.time()}".encode()).hexdigest()[:16]
    return UploadCorpusResponse(job_id=job_id)


@app.post("/v1/train", response_model=TrainTriggerResponse, dependencies=[Depends(rate_limit_dep)])
async def trigger_train(
    req: TrainTriggerRequest,
    admin=Depends(require_admin),
) -> TrainTriggerResponse:
    job_id = hashlib.sha256(f"train:{req.task}:{admin.get('sub','')}:{time.time()}".encode()).hexdigest()[:16]
    return TrainTriggerResponse(job_id=job_id)


@app.exception_handler(Exception)
async def default_exception_handler(request, exc):  # type: ignore
    logger.error("unhandled_exception", error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
