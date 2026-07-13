"""
/tickets - Tickets de servicio via SOAP MPS API.

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
from soap_client import (
    base_request, date_range_filter, value_filter,
    apply_filters, call_soap
)

router = APIRouter()


def _call(operation: str, req: dict):
    try:
        return call_soap(operation, req)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# GET /tickets
# ------------------------------------------------------------------------------

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


# GET /tickets/range
# ------------------------------------------------------------------------------

@router.get("/range", summary="Tickets creados en un intervalo de fechas")
def tickets_by_range(
    start_date: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date:   date = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    status:     Optional[str] = Query(None, description="Filtrar por nombre de estado"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Devuelve los tickets cuya creacion (DateOccurred) este en el rango.
    Opcionalmente filtra por Status (Open, Closed, etc.).
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    filters = [date_range_filter("DateOccurred", start, end)]
    if status:
        filters.append(value_filter("Status", [status]))

    req = base_request(page=page, page_size=page_size)
    apply_filters(req, filters)
    req["SortField"]     = "DateOccurred"
    req["SortDirection"] = "Descending"
    return _call("TicketGetList", req)


# GET /tickets/asset/{asset_id}
# ------------------------------------------------------------------------------

@router.get("/asset/{asset_id}", summary="Historial de tickets de un activo")
def tickets_by_asset(
    asset_id:   str,
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Historico completo de incidentes reportados para una impresora/MFD especifica.
    """
    req = base_request(page=page, page_size=page_size)
    filters = [value_filter("AssetID", [asset_id])]
    if start_date and end_date:
        start = datetime.combine(start_date, datetime.min.time())
        end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))
        filters.append(date_range_filter("DateOccurred", start, end))
    apply_filters(req, filters)
    req["SortField"]     = "DateOccurred"
    req["SortDirection"] = "Descending"
    return _call("TicketGetList", req)


# GET /tickets/{ticket_id}
# ------------------------------------------------------------------------------

@router.get("/{ticket_id}", summary="Detalle completo de un ticket")
def get_ticket(ticket_id: str):
    """
    Devuelve todos los campos del ticket identificado por su TicketID (GUID).
    """
    req = base_request()
    req["ObjectIDs"] = {"string": [ticket_id]}
    return _call("TicketGet", req)


# GET /tickets/{ticket_id}/activities
# ------------------------------------------------------------------------------

@router.get("/{ticket_id}/activities", summary="Actividades del ticket")
def ticket_activities(ticket_id: str):
    """
    Historial de actividades/actualizaciones registradas en el ticket.
    """
    req = base_request()
    filters = [value_filter("TicketID", [ticket_id])]
    apply_filters(req, filters)
    return _call("TicketActivityGet", req)


# GET /tickets/{ticket_id}/assignments
# ------------------------------------------------------------------------------

@router.get("/{ticket_id}/assignments", summary="Asignaciones del ticket")
def ticket_assignments(ticket_id: str):
    """
    Tecnicos y equipos asignados al ticket.
    """
    req = base_request()
    filters = [value_filter("TicketID", [ticket_id])]
    apply_filters(req, filters)
    return _call("TicketAssignmentGetList", req)