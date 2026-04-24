from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI
import uvicorn

from company_agent.common.auth import require_internal_api_key
from company_agent.common.embeddings import EmbeddingClient, EmbeddingConfig
from company_agent.common.logging import configure_logging

from .config import RagSettings
from .schemas import HealthResponse, RetrieveRequest, RetrieveResponse
from .search import KnowledgeSearcher

settings = RagSettings()
logger = configure_logging(settings.app_name)
embedding_client = EmbeddingClient(
    EmbeddingConfig(
        provider=settings.embedding_provider,
        api_key=settings.openai_api_key,
        model=settings.openai_embedding_model,
    )
)
searcher = KnowledgeSearcher(settings=settings, embeddings=embedding_client)

app = FastAPI(title="RAG API", version="0.1.0")
InternalApiKey = Annotated[None, Depends(require_internal_api_key(settings.internal_api_key))]


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/v1/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest, _auth: InternalApiKey) -> RetrieveResponse:
    logger.info("retrieval request query=%r top_k=%s", request.query, request.top_k)
    return searcher.search(request)


def run() -> None:
    uvicorn.run("company_agent.rag_api.main:app", host="0.0.0.0", port=8081, reload=False)


if __name__ == "__main__":
    run()
