from __future__ import annotations

from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from resume_ai.infrastructure.correlation import (
    current_correlation_id,
    normalize_correlation_id,
)


class ApiErrorDetail(BaseModel):
    code: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    message: str = Field(min_length=1, max_length=200)
    request_id: str = Field(min_length=1, max_length=64)


class ApiErrorResponse(BaseModel):
    error: ApiErrorDetail


def api_error_response(status_code: int, code: str, message: str) -> JSONResponse:
    request_id = current_correlation_id() or normalize_correlation_id(None)
    payload = ApiErrorResponse(
        error=ApiErrorDetail(
            code=code,
            message=message,
            request_id=request_id,
        )
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))
