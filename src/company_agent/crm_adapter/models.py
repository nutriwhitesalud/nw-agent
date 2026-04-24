from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Priority = Literal["low", "normal", "high", "urgent"]


class HealthResponse(BaseModel):
    status: str


class CustomerLookupRequest(BaseModel):
    customer_id: str | None = None
    email: str | None = None


class CustomerProfile(BaseModel):
    customer_id: str
    name: str
    email: str
    plan: str
    status: str
    locale: str


class OrderRecord(BaseModel):
    order_id: str
    status: str
    total: str
    placed_at: str


class TicketRecord(BaseModel):
    ticket_id: str
    status: str
    subject: str
    updated_at: str


class CustomerOrdersRequest(BaseModel):
    customer_id: str


class CustomerTicketsRequest(BaseModel):
    customer_id: str


class TicketDraftRequest(BaseModel):
    customer_id: str
    summary: str = Field(min_length=5, max_length=240)
    details: str = Field(min_length=10, max_length=4000)
    priority: Priority = "normal"


class TicketDraftResponse(BaseModel):
    draft_id: str
    customer_id: str
    summary: str
    details: str
    priority: Priority
    status: str


class HandoffRequest(BaseModel):
    conversation_id: str
    reason: str = Field(min_length=10, max_length=2000)
    priority: Priority = "high"
    customer_id: str | None = None


class HandoffResponse(BaseModel):
    handoff_id: str
    queue: str
    status: str

