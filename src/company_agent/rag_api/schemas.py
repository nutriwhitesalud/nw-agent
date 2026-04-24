from __future__ import annotations

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    corpus: str = Field(default="default")
    product: str | None = None
    language: str | None = None


class RetrievedPassage(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    title: str
    content: str
    source_uri: str
    citation: str
    score: float
    matched_by: list[str]
    metadata: dict


class RetrieveResponse(BaseModel):
    query: str
    strategy: list[str]
    results: list[RetrievedPassage]


class HealthResponse(BaseModel):
    status: str

