import asyncio
import json
import logging
import time
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.models import ApiMetric

logger = logging.getLogger("copy.requests")


class TelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        started = time.perf_counter()
        request_id = str(uuid4())
        request.state.cache_status = "BYPASS"
        request.state.tokens_used = 0
        request.state.tokens_saved = 0
        try:
            response = await call_next(request)
        except Exception:
            # Never log payloads, provider exceptions, connection strings or credentials.
            logger.error("request_failed request_id=%s", request_id)
            response = JSONResponse({"detail": "Erro interno; consulte o identificador da requisição"}, 500)
        elapsed = (time.perf_counter() - started) * 1000
        status = request.state.cache_status
        response.headers["X-Process-Time"] = f"{elapsed / 1000:.6f}"
        response.headers["X-Cache-Status"] = status
        response.headers["X-Request-ID"] = request_id
        path = request.url.path
        if path.startswith("/api/v1/") and not path.startswith("/api/v1/metrics"):
            record = {
                "request_id": request_id,
                "path": path[:300],
                "method": request.method,
                "kind": "generation"
                if path == "/api/v1/copies/generate" and request.method == "POST"
                else "api",
                "latency_ms": elapsed,
                "cache_status": status,
                "status_code": response.status_code,
                "input_hash": getattr(request.state, "input_hash", None),
                "model_name": getattr(request.state, "model_name", None),
                "tokens_used": request.state.tokens_used,
                "tokens_saved": request.state.tokens_saved,
            }
            try:
                async with asyncio.timeout(3), request.app.state.sessions() as session:
                    session.add(ApiMetric(**record))
                    await session.commit()
            except (SQLAlchemyError, TimeoutError):
                logger.error("metric_write_failed request_id=%s", request_id)
            logger.info(json.dumps(record, ensure_ascii=False))
        return response
