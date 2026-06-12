"""Production-ready AI agent for Day 12 deployment lab."""
import json
import logging
import os
import signal
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import CostGuard
from app.day10_service import answer_from_corpus, corpus_summary, load_report, search_papers
from app.rate_limiter import RateLimiter
from app.storage import StateStore


logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
INSTANCE_ID = settings.instance_id or os.getenv("HOSTNAME", f"agent-{uuid.uuid4().hex[:8]}")

store = StateStore(settings.redis_url)
rate_limiter = RateLimiter(
    store=store,
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60,
)
cost_guard = CostGuard(
    store=store,
    monthly_budget_usd=settings.monthly_budget_usd,
)

is_ready = False
request_count = 0
error_count = 0


class AskRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    user_id: str
    question: str
    answer: str
    model: str
    history_count: int
    served_by: str
    timestamp: str
    sources: list[dict] = Field(default_factory=list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "instance_id": INSTANCE_ID,
        "storage": store.mode,
    }))
    is_ready = True
    yield
    is_ready = False
    logger.info(json.dumps({"event": "shutdown", "instance_id": INSTANCE_ID}))


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global request_count, error_count
    start = time.time()
    request_count += 1
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Instance-ID"] = INSTANCE_ID
        if "server" in response.headers:
            del response.headers["server"]
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((time.time() - start) * 1000, 1),
        }))
        return response
    except Exception:
        error_count += 1
        logger.exception(json.dumps({
            "event": "request_error",
            "method": request.method,
            "path": request.url.path,
        }))
        raise


@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "instance_id": INSTANCE_ID,
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
            "metrics": "GET /metrics (requires X-API-Key)",
            "day10": "GET /day10/summary, GET /day10/search?q=...",
        },
    }


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    _api_key: str = Depends(verify_api_key),
):
    rate_limiter.check(body.user_id)
    cost_guard.check_budget(body.user_id)

    history = store.load_history(body.user_id)
    store.append_history(body.user_id, "user", body.question)

    input_tokens = estimate_tokens(body.question)
    corpus_result = answer_from_corpus(build_prompt(body.question, history))
    answer = corpus_result["answer"]
    output_tokens = estimate_tokens(answer)

    store.append_history(body.user_id, "assistant", answer)
    usage = cost_guard.record_usage(body.user_id, input_tokens, output_tokens)

    logger.info(json.dumps({
        "event": "agent_call",
        "user_id": body.user_id,
        "q_len": len(body.question),
        "client": str(request.client.host) if request.client else "unknown",
        "monthly_cost_usd": usage["cost_usd"],
    }))

    return AskResponse(
        user_id=body.user_id,
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        history_count=len(store.load_history(body.user_id)),
        served_by=INSTANCE_ID,
        timestamp=datetime.now(timezone.utc).isoformat(),
        sources=corpus_result["matches"],
    )


@app.get("/day10/summary", tags=["Day 10 Data Pipeline"])
def day10_summary(_api_key: str = Depends(verify_api_key)):
    return corpus_summary()


@app.get("/day10/search", tags=["Day 10 Data Pipeline"])
def day10_search(q: str, top_k: int = 3, _api_key: str = Depends(verify_api_key)):
    return {"query": q, "results": search_papers(q, top_k=max(1, min(top_k, 10)))}


@app.get("/day10/report/{name}", tags=["Day 10 Data Pipeline"])
def day10_report(name: str, _api_key: str = Depends(verify_api_key)):
    return load_report(name)


@app.get("/health", tags=["Operations"])
def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "instance_id": INSTANCE_ID,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": request_count,
        "checks": {
            "llm": "mock" if not settings.openai_api_key else settings.llm_model,
            "storage": store.mode,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    if not is_ready:
        raise HTTPException(503, "Application is not ready")
    if settings.redis_url and not store.ping():
        raise HTTPException(503, "Redis is not ready")
    return {
        "ready": True,
        "instance_id": INSTANCE_ID,
        "storage": store.mode,
    }


@app.get("/metrics", tags=["Operations"])
def metrics(_api_key: str = Depends(verify_api_key)):
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": request_count,
        "error_count": error_count,
        "storage": store.mode,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "monthly_budget_usd": settings.monthly_budget_usd,
    }


def build_prompt(question: str, history: list[dict]) -> str:
    if not history:
        return question
    previous = history[-6:]
    context = "\n".join(f"{item['role']}: {item['content']}" for item in previous)
    return f"Conversation so far:\n{context}\n\nUser: {question}"


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) * 2)


def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))


signal.signal(signal.SIGTERM, _handle_signal)


if __name__ == "__main__":
    import uvicorn

    logger.info(json.dumps({
        "event": "run_local",
        "host": settings.host,
        "port": settings.port,
    }))
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
