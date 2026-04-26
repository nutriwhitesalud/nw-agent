from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Priority = Literal["low", "normal", "high", "urgent"]


class HealthResponse(BaseModel):
    status: str


# ── Lookup ────────────────────────────────────────────────────────────────────

class CustomerLookupRequest(BaseModel):
    """Accepts phone (primary, WhatsApp E.164), customer_id (Zoho record id), or email."""
    phone: str | None = None        # WhatsApp number: +584145610594
    customer_id: str | None = None  # Zoho Contact record id
    email: str | None = None


class PatientProfile(BaseModel):
    """Slimmed-down Contact record safe to expose to the agent."""
    contact_id: str
    full_name: str
    email: str | None
    phone: str | None
    language: str | None                # Idioma field
    patient_status: str | None          # Estado_de_Paciente
    patient_type: str | None            # Paciente (Nuevo / Recurrente)
    community_type: str | None          # Tipo_de_Comunidad
    specialist: str | None              # Especialista.name
    consult_reason: list[str]           # Motivo_de_Consulta


# Backward-compat alias used by the OpenClaw plugin tool name "customer_lookup"
CustomerProfile = PatientProfile


# ── Deals (Tratos / Plans) ────────────────────────────────────────────────────

class CustomerOrdersRequest(BaseModel):
    customer_id: str


class DealRecord(BaseModel):
    deal_id: str
    deal_name: str
    stage: str | None
    amount: float | None
    plan_status: str | None         # Estado_del_plan
    plan_duration: str | None       # Vigencia_del_plan
    consultations_total: int | None # Consultas_del_Plan
    consultations_used: int | None  # Total_Consultas_Vistas
    exams_pending: int | None       # Ex_menes_Pendientes
    payment_method: str | None      # Formas_de_pago
    specialist: str | None


# Backward-compat alias
OrderRecord = DealRecord


# ── Consultas ─────────────────────────────────────────────────────────────────

class CustomerTicketsRequest(BaseModel):
    customer_id: str


class ConsultaRecord(BaseModel):
    consulta_id: str
    number: int | None              # N_de_Consulta
    type: str | None                # Tipo_de_consulta
    scheduled_date: str | None      # Fecha_Programada
    appointment_status: str | None  # Estado_de_la_Cita
    specialist: str | None          # Especialista
    connection_link: str | None     # Link_de_Conexi_n


# Backward-compat alias — "tickets" maps to consultas in NW context
TicketRecord = ConsultaRecord


# ── Examenes ──────────────────────────────────────────────────────────────────

class ExamenRecord(BaseModel):
    examen_id: str
    exam_name: str | None           # Nombre_del_examen.name
    process_status: str | None      # Estatus_del_Proceso
    kit_sent_date: str | None       # Fecha_Env_o_Kit
    results_received_date: str | None  # Fecha_Resultados_Recibidos
    admin_status: str | None        # Estado_Administrativo


# ── Ticket Draft (reused as handoff note) ─────────────────────────────────────

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


# ── Handoff ───────────────────────────────────────────────────────────────────

class HandoffRequest(BaseModel):
    conversation_id: str
    reason: str = Field(min_length=10, max_length=2000)
    priority: Priority = "high"
    customer_id: str | None = None  # Zoho Contact record id


class HandoffResponse(BaseModel):
    handoff_id: str
    contact_id: str | None
    note_id: str | None             # Zoho Note id if created
    status: str
    message: str
