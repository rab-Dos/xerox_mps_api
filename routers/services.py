"""
/services  – Servicios contratados vía SOAP MPS API y SA-API.

ServiceFeed campos: ControlID, Name, ProblemTypes, SLA, ServiceID, TicketSources

SA-API /Services retorna: ServiceID, ServiceName, ServiceEntitlement, ServiceType
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from soap_client import get_soap_client, base_request, value_filter
from sa_client import sa_client
from zeep.helpers import serialize_object

router = APIRouter()


def _call_soap(operation: str, request: dict):
    try:
        client = get_soap_client()
        method = getattr(client.service, operation)
        result = method(request=request)
        return serialize_object(result)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ── SOAP Services ──────────────────────────────────────────────────────────────

@router.get("/", summary="Catálogo de servicios MPS (SOAP)")
def list_services(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Devuelve todos los servicios disponibles en la plataforma MPS,
    incluyendo tipos de problema, SLA y fuentes de ticket.
    """
    req = base_request(page=page, page_size=page_size)
    return _call_soap("ServiceGetList", req)


@router.get("/statuses", summary="Estados de servicio disponibles")
def service_statuses(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """Lista los estados posibles para tickets de servicio."""
    req = base_request(page=page, page_size=page_size)
    return _call_soap("ServiceStatusGetList", req)


@router.get("/exit-statuses", summary="Estados de cierre de servicio")
def service_exit_statuses(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """Lista los posibles estados de salida al cerrar un ticket."""
    req = base_request(page=page, page_size=page_size)
    return _call_soap("ServiceStatusExitStatusesGetList", req)


@router.get("/late-reasons", summary="Razones de atraso en servicio")
def service_late_reasons(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """Razones estandarizadas para justificar atrasos en la resolución de tickets."""
    req = base_request(page=page, page_size=page_size)
    return _call_soap("ServiceLateReasonsGet", req)


# ── SA-API Services ────────────────────────────────────────────────────────────

@router.get("/entitlements/{serial_number}/{mac_address}",
            summary="Servicios SA-API contratados por dispositivo")
def get_device_services(serial_number: str, mac_address: str):
    """
    Consulta la SA-API REST para obtener los servicios (entitlements) asociados
    al dispositivo identificado por número de serie y dirección MAC.

    Retorna: ServiceID, ServiceName, ServiceEntitlement, ServiceType.
    ServiceType puede ser: Service | Break-fix | MACD | Supplies.
    """
    try:
        return sa_client.get_services(serial=serial_number, mac=mac_address)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
