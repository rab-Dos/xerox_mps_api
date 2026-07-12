"""
/tickets  – Tickets de servicio vía SOAP MPS API.

TicketFeed campos:
  AccountID, AgentID, AssetID, ChargebackCodeID, CloseDate, ContactID,
  ControlID, DateOccurred, LastActivityDate, LocationID, ModifiedDate,
  ReferenceNumber, ResolvedDate, RespondDate, SLAResolution, SLAResponse,
  ServiceID, ServiceName, Status, StatusID, TicketID, TicketNumber, VersionNumber
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from soap_client import get_soap_client, base_request, date_range_filter, value_filter
from zeep.helpers import serialize_object

router = APIRouter()


def _call(operation: str, request: dict):
    try:
        client = get_soap_client()
        method = getattr(client.service, operation)
        result = method(request=request)
        return serialize_object(result)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ── GET /tickets  ─────────────────────────────────────────────────────────────

@router.get("/", summary="Listar todos los tickets")
def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    sort_field: str = Query("DateOccurred", description="Campo de ordenamiento"),
    sort_direction: str = Query("Descending", description="Ascending | Descending"),
):
    """
    Devuelve todos los tickets de servicio de la cuenta, paginados.
    """
    req = base_request(page=page, page_size=page_size)
    req["SortField"]     = sort_field
    req["SortDirection"] = sort_direction
    return _call("TicketGetList", req)


# ── GET /tickets/today  ───────────────────────────────────────────────────────

@router.get("/today", summary="Tickets abiertos hoy")
def tickets_today(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Tickets cuya DateOccurred (fecha de apertura) sea el día de hoy.
    """
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end   = datetime.combine(today, datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"]       = [date_range_filter("DateOccurred", start, end)]
    req["SortField"]     = "DateOccurred"
    req["SortDirection"] = "Descending"
    return _call("TicketGetList", req)


# ── GET /tickets/range  ───────────────────────────────────────────────────────

@router.get("/range", summary="Tickets en intervalo de fechas (por apertura)")
def tickets_by_range(
    start_date: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date:   date = Query(..., description="Fecha fin   (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Tickets abiertos (DateOccurred) entre `start_date` y `end_date`.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"]       = [date_range_filter("DateOccurred", start, end)]
    req["SortField"]     = "DateOccurred"
    req["SortDirection"] = "Descending"
    return _call("TicketGetList", req)


# ── GET /tickets/closed/range  ────────────────────────────────────────────────

@router.get("/closed/range", summary="Tickets cerrados en intervalo de fechas")
def tickets_closed_range(
    start_date: date = Query(..., description="Fecha inicio"),
    end_date:   date = Query(..., description="Fecha fin"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Tickets cuya CloseDate cae en el intervalo indicado.
    Útil para reportes de resolución SLA.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"]       = [date_range_filter("CloseDate", start, end)]
    req["SortField"]     = "CloseDate"
    req["SortDirection"] = "Descending"
    return _call("TicketGetList", req)


# ── GET /tickets/modified/range  ──────────────────────────────────────────────

@router.get("/modified/range", summary="Tickets modificados en intervalo de fechas")
def tickets_modified_range(
    start_date: date = Query(..., description="Fecha inicio"),
    end_date:   date = Query(..., description="Fecha fin"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Tickets que fueron actualizados (ModifiedDate) en el intervalo dado.
    Permite sincronización incremental con sistemas externos.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"]       = [date_range_filter("ModifiedDate", start, end)]
    req["SortField"]     = "ModifiedDate"
    req["SortDirection"] = "Descending"
    return _call("TicketGetList", req)


# ── GET /tickets/activity/range  ──────────────────────────────────────────────

@router.get("/activity/range", summary="Tickets con actividad reciente en intervalo")
def tickets_activity_range(
    start_date: date = Query(..., description="Fecha inicio"),
    end_date:   date = Query(..., description="Fecha fin"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Tickets con LastActivityDate en el rango indicado.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"]       = [date_range_filter("LastActivityDate", start, end)]
    req["SortField"]     = "LastActivityDate"
    req["SortDirection"] = "Descending"
    return _call("TicketGetList", req)


# ── GET /tickets/asset/{asset_id}  ────────────────────────────────────────────

@router.get("/asset/{asset_id}", summary="Tickets de un activo específico")
def tickets_by_asset(
    asset_id: str,
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Tickets asociados a un activo (AssetID). Acepta filtro de fecha opcional.
    """
    req = base_request(page=page, page_size=page_size)
    filters = [value_filter("AssetID", [asset_id])]
    if start_date and end_date:
        start = datetime.combine(start_date, datetime.min.time())
        end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))
        filters.append(date_range_filter("DateOccurred", start, end))
    req["Filters"]       = filters
    req["SortField"]     = "DateOccurred"
    req["SortDirection"] = "Descending"
    return _call("TicketGetList", req)


# ── GET /tickets/{ticket_id}  ─────────────────────────────────────────────────

@router.get("/{ticket_id}", summary="Detalle completo de un ticket")
def get_ticket(ticket_id: str):
    """
    Devuelve todos los campos del ticket identificado por su TicketID (GUID).
    """
    req = base_request()
    req["ObjectIDs"] = [ticket_id]
    return _call("TicketGet", req)


# ── GET /tickets/{ticket_id}/activities  ──────────────────────────────────────

@router.get("/{ticket_id}/activities", summary="Actividades del ticket")
def ticket_activities(ticket_id: str):
    """
    Historial de actividades/actualizaciones registradas en el ticket.
    """
    req = base_request()
    req["Filters"] = [value_filter("TicketID", [ticket_id])]
    return _call("TicketActivityGet", req)


# ── GET /tickets/{ticket_id}/assignments  ─────────────────────────────────────

@router.get("/{ticket_id}/assignments", summary="Asignaciones del ticket")
def ticket_assignments(ticket_id: str):
    """
    Técnicos y equipos asignados al ticket.
    """
    req = base_request()
    req["Filters"] = [value_filter("TicketID", [ticket_id])]
    return _call("TicketAssignmentsGet", req)
