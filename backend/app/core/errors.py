"""Common error schemas and codes.

Architecture §5 HTTP/DTO common rules.
"""
from pydantic import BaseModel, ConfigDict

from app.schemas.common import ResponseMeta


class FieldError(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    path: str
    code: str
    message: str


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    code: str
    message: str
    fields: list[FieldError] = []
    retryable: bool = False
    status_url: str | None = None


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    error: ErrorDetail
    meta: ResponseMeta
