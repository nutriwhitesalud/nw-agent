from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
import uvicorn

from company_agent.common.auth import require_internal_api_key
from company_agent.common.logging import configure_logging

from .adapters import MockCrmAdapter, PlaceholderHttpCrmAdapter
from .config import CrmSettings
from .models import (
    CustomerLookupRequest,
    CustomerOrdersRequest,
    CustomerProfile,
    CustomerTicketsRequest,
    HandoffRequest,
    HandoffResponse,
    HealthResponse,
    OrderRecord,
    TicketDraftRequest,
    TicketDraftResponse,
    TicketRecord,
)

settings = CrmSettings()
logger = configure_logging(settings.app_name)

adapter = MockCrmAdapter() if settings.crm_provider == "mock" else PlaceholderHttpCrmAdapter()

app = FastAPI(title="CRM Adapter", version="0.1.0")
InternalApiKey = Annotated[None, Depends(require_internal_api_key(settings.internal_api_key))]


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/v1/customer/profile", response_model=CustomerProfile)
def customer_profile(request: CustomerLookupRequest, _auth: InternalApiKey) -> CustomerProfile:
    profile = adapter.lookup_customer(request.customer_id, request.email)
    if not profile:
        raise HTTPException(status_code=404, detail="Customer not found")
    return profile


@app.post("/v1/customer/orders", response_model=list[OrderRecord])
def customer_orders(request: CustomerOrdersRequest, _auth: InternalApiKey) -> list[OrderRecord]:
    return list(adapter.list_orders(request.customer_id))


@app.post("/v1/customer/tickets", response_model=list[TicketRecord])
def customer_tickets(request: CustomerTicketsRequest, _auth: InternalApiKey) -> list[TicketRecord]:
    return list(adapter.list_tickets(request.customer_id))


@app.post("/v1/tickets/draft", response_model=TicketDraftResponse)
def create_ticket_draft(request: TicketDraftRequest, _auth: InternalApiKey) -> TicketDraftResponse:
    logger.info("creating ticket draft for customer=%s", request.customer_id)
    return adapter.create_ticket_draft(request)


@app.post("/v1/handoff", response_model=HandoffResponse)
def handoff_human(request: HandoffRequest, _auth: InternalApiKey) -> HandoffResponse:
    logger.info("handoff queued conversation=%s", request.conversation_id)
    return adapter.handoff(request)


def run() -> None:
    uvicorn.run("company_agent.crm_adapter.main:app", host="0.0.0.0", port=8082, reload=False)


if __name__ == "__main__":
    run()
