from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
import uvicorn

from company_agent.common.auth import require_internal_api_key
from company_agent.common.logging import configure_logging

from .adapters import BaseCrmAdapter, MockCrmAdapter, ZohoCrmAdapter
from .config import CrmSettings
from .models import (
    ConsultaRecord,
    CustomerLookupRequest,
    CustomerOrdersRequest,
    CustomerProfile,
    CustomerTicketsRequest,
    DealRecord,
    ExamenRecord,
    HandoffRequest,
    HandoffResponse,
    HealthResponse,
    TicketDraftRequest,
    TicketDraftResponse,
)

settings = CrmSettings()
logger = configure_logging(settings.app_name)


def _build_adapter() -> BaseCrmAdapter:
    if settings.crm_provider == "zoho":
        from .zoho_client import ZohoClient, ZohoTokenManager

        if not all([settings.zoho_client_id, settings.zoho_client_secret, settings.zoho_refresh_token]):
            raise RuntimeError(
                "CRM_PROVIDER=zoho requires ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN"
            )

        tokens = ZohoTokenManager(
            accounts_url=settings.zoho_accounts_url,
            client_id=settings.zoho_client_id,       # type: ignore[arg-type]
            client_secret=settings.zoho_client_secret,  # type: ignore[arg-type]
            refresh_token=settings.zoho_refresh_token,  # type: ignore[arg-type]
        )
        client = ZohoClient(api_base=settings.zoho_api_base, tokens=tokens)
        logger.info(
            "zoho adapter initialized api_base=%s sandbox=%s",
            settings.zoho_api_base,
            settings.zoho_sandbox,
        )
        return ZohoCrmAdapter(client)

    logger.info("using mock CRM adapter")
    return MockCrmAdapter()


adapter = _build_adapter()

app = FastAPI(title="CRM Adapter", version="0.2.0")
InternalApiKey = Annotated[None, Depends(require_internal_api_key(settings.internal_api_key))]


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


# ── Customer profile (lookup by phone / id / email) ───────────────────────────

@app.post("/v1/customer/profile", response_model=CustomerProfile)
def customer_profile(request: CustomerLookupRequest, _auth: InternalApiKey) -> CustomerProfile:
    profile = adapter.lookup_customer(
        phone=request.phone,
        customer_id=request.customer_id,
        email=request.email,
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return profile


# ── Deals / Plans ─────────────────────────────────────────────────────────────

@app.post("/v1/customer/orders", response_model=list[DealRecord])
def customer_orders(request: CustomerOrdersRequest, _auth: InternalApiKey) -> list[DealRecord]:
    return list(adapter.list_orders(request.customer_id))


# ── Consultas (appointments) ──────────────────────────────────────────────────

@app.post("/v1/customer/tickets", response_model=list[ConsultaRecord])
def customer_tickets(request: CustomerTicketsRequest, _auth: InternalApiKey) -> list[ConsultaRecord]:
    return list(adapter.list_tickets(request.customer_id))


@app.post("/v1/customer/consultas", response_model=list[ConsultaRecord])
def customer_consultas(request: CustomerTicketsRequest, _auth: InternalApiKey) -> list[ConsultaRecord]:
    return list(adapter.list_tickets(request.customer_id))


# ── Examenes ──────────────────────────────────────────────────────────────────

@app.post("/v1/customer/examenes", response_model=list[ExamenRecord])
def customer_examenes(request: CustomerOrdersRequest, _auth: InternalApiKey) -> list[ExamenRecord]:
    return list(adapter.list_examenes(request.customer_id))


# ── Ticket draft / note ───────────────────────────────────────────────────────

@app.post("/v1/tickets/draft", response_model=TicketDraftResponse)
def create_ticket_draft(request: TicketDraftRequest, _auth: InternalApiKey) -> TicketDraftResponse:
    logger.info("ticket draft for contact=%s", request.customer_id)
    return adapter.create_ticket_draft(request)


# ── Handoff ───────────────────────────────────────────────────────────────────

@app.post("/v1/handoff", response_model=HandoffResponse)
def handoff_human(request: HandoffRequest, _auth: InternalApiKey) -> HandoffResponse:
    logger.info("handoff conversation=%s contact=%s", request.conversation_id, request.customer_id)
    return adapter.handoff(request)


def run() -> None:
    uvicorn.run("company_agent.crm_adapter.main:app", host="0.0.0.0", port=8082, reload=False)


if __name__ == "__main__":
    run()
