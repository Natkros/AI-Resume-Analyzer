import time
import uuid

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, jobs, matching, recommendations, resumes
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger, request_id_ctx

configure_logging()
logger = get_logger("app")
settings = get_settings()

app = FastAPI(
    title="AI Resume Analyzer & Job Matcher",
    version="0.1.0",
    description="Explainable resume-job compatibility analysis: parsing, skill taxonomy, "
    "semantic matching, ATS analysis, and grounded LLM recommendations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = str(uuid.uuid4())
    request_id_ctx.set(rid)
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = rid
    logger.info("request_completed", path=request.url.path, method=request.method,
                status_code=response.status_code, duration_ms=duration_ms)
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    rid = request_id_ctx.get()
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        body = {"error": {**detail, "request_id": rid}}
    else:
        body = {"error": {"code": "HTTP_ERROR", "message": str(detail), "request_id": rid}}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    rid = request_id_ctx.get()
    logger.error("unhandled_exception", path=request.url.path, error=str(exc), request_id=rid)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred.", "request_id": rid}},
    )


app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(matching.router)
app.include_router(recommendations.router)


@app.get("/health")
def health():
    return {"status": "ok"}
