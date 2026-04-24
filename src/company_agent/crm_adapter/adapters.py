from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from uuid import uuid4

from .models import (
    CustomerProfile,
    HandoffRequest,
    HandoffResponse,
    OrderRecord,
    TicketDraftRequest,
    TicketDraftResponse,
    TicketRecord,
)


class BaseCrmAdapter(ABC):
    @abstractmethod
    def lookup_customer(self, customer_id: str | None, email: str | None) -> CustomerProfile | None:
        raise NotImplementedError

    @abstractmethod
    def list_orders(self, customer_id: str) -> Sequence[OrderRecord]:
        raise NotImplementedError

    @abstractmethod
    def list_tickets(self, customer_id: str) -> Sequence[TicketRecord]:
        raise NotImplementedError

    @abstractmethod
    def create_ticket_draft(self, request: TicketDraftRequest) -> TicketDraftResponse:
        raise NotImplementedError

    @abstractmethod
    def handoff(self, request: HandoffRequest) -> HandoffResponse:
        raise NotImplementedError


class MockCrmAdapter(BaseCrmAdapter):
    def __init__(self) -> None:
        self._customers = {
            "cust_1001": CustomerProfile(
                customer_id="cust_1001",
                name="Ana Diaz",
                email="ana@example.com",
                plan="growth",
                status="active",
                locale="es-VE",
            ),
            "cust_1002": CustomerProfile(
                customer_id="cust_1002",
                name="Jordan Lee",
                email="jordan@example.com",
                plan="starter",
                status="past_due",
                locale="en-US",
            ),
        }
        self._orders = {
            "cust_1001": [
                OrderRecord(
                    order_id="ord_7001",
                    status="fulfilled",
                    total="USD 149.00",
                    placed_at="2026-04-20T15:30:00Z",
                )
            ],
            "cust_1002": [
                OrderRecord(
                    order_id="ord_7002",
                    status="processing",
                    total="USD 49.00",
                    placed_at="2026-04-22T12:15:00Z",
                )
            ],
        }
        self._tickets = {
            "cust_1001": [
                TicketRecord(
                    ticket_id="tic_9001",
                    status="open",
                    subject="Invoice clarification",
                    updated_at="2026-04-23T10:12:00Z",
                )
            ],
            "cust_1002": [],
        }

    def lookup_customer(self, customer_id: str | None, email: str | None) -> CustomerProfile | None:
        if customer_id and customer_id in self._customers:
            return self._customers[customer_id]

        if email:
            for customer in self._customers.values():
                if customer.email.lower() == email.lower():
                    return customer

        return None

    def list_orders(self, customer_id: str) -> Sequence[OrderRecord]:
        return self._orders.get(customer_id, [])

    def list_tickets(self, customer_id: str) -> Sequence[TicketRecord]:
        return self._tickets.get(customer_id, [])

    def create_ticket_draft(self, request: TicketDraftRequest) -> TicketDraftResponse:
        return TicketDraftResponse(
            draft_id=f"draft_{uuid4().hex[:10]}",
            customer_id=request.customer_id,
            summary=request.summary,
            details=request.details,
            priority=request.priority,
            status="draft_created",
        )

    def handoff(self, request: HandoffRequest) -> HandoffResponse:
        return HandoffResponse(
            handoff_id=f"handoff_{uuid4().hex[:10]}",
            queue="customer-support-tier-1",
            status="queued",
        )


class PlaceholderHttpCrmAdapter(BaseCrmAdapter):
    def lookup_customer(self, customer_id: str | None, email: str | None) -> CustomerProfile | None:
        raise NotImplementedError("Implement your real CRM lookup here.")

    def list_orders(self, customer_id: str) -> Sequence[OrderRecord]:
        raise NotImplementedError("Implement your real CRM order lookup here.")

    def list_tickets(self, customer_id: str) -> Sequence[TicketRecord]:
        raise NotImplementedError("Implement your real CRM ticket lookup here.")

    def create_ticket_draft(self, request: TicketDraftRequest) -> TicketDraftResponse:
        raise NotImplementedError("Implement your real CRM ticket draft creation here.")

    def handoff(self, request: HandoffRequest) -> HandoffResponse:
        raise NotImplementedError("Implement your real handoff workflow here.")

