"""
/shipments  – Envíos de suministros vía SOAP MPS API.

ShipmentFeed campos:
  CarrierID, CarrierName, ChargebackCodeID, ControlID, ModifiedDate,
  ReceivedDate, ShipmentID, ShippedDate, Status, StatusID,
  SupplierOrderID, TrackingNumber, VersionNumber
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
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


# ── GET /shipments  ───────────────────────────────────────────────────────────

@router.get("/", summary="Listar todos los envíos")
def list_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    sort_direction: str = Query("Descending"),
):
    """
    Devuelve todos los envíos registrados en la cuenta, paginados.
    """
    req = base_request(page=page, page_size=page_size)
    req["SortField"]     = "ShippedDate"
    req["SortDirection"] = sort_direction
    return _call("ShipmentGetList", req)


# ── GET /shipments/today  ─────────────────────────────────────────────────────

@router.get("/today", summary="Envíos despachados hoy")
def shipments_today(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Envíos cuya ShippedDate corresponda al día de hoy.
    """
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end   = datetime.combine(today, datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"]       = [date_range_filter("ShippedDate", start, end)]
    req["SortField"]     = "ShippedDate"
    req["SortDirection"] = "Descending"
    return _call("ShipmentGetList", req)


# ── GET /shipments/range  ─────────────────────────────────────────────────────

@router.get("/range", summary="Envíos despachados en intervalo de fechas")
def shipments_by_range(
    start_date: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date:   date = Query(..., description="Fecha fin   (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Envíos con ShippedDate en el intervalo indicado.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"]       = [date_range_filter("ShippedDate", start, end)]
    req["SortField"]     = "ShippedDate"
    req["SortDirection"] = "Descending"
    return _call("ShipmentGetList", req)


# ── GET /shipments/received/range  ────────────────────────────────────────────

@router.get("/received/range", summary="Envíos recibidos en intervalo de fechas")
def shipments_received_range(
    start_date: date = Query(..., description="Fecha inicio"),
    end_date:   date = Query(..., description="Fecha fin"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Envíos cuya ReceivedDate cae en el rango indicado.
    Útil para confirmar entrega de suministros.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"]       = [date_range_filter("ReceivedDate", start, end)]
    req["SortField"]     = "ReceivedDate"
    req["SortDirection"] = "Descending"
    return _call("ShipmentGetList", req)


# ── GET /shipments/modified/range  ────────────────────────────────────────────

@router.get("/modified/range", summary="Envíos modificados en intervalo")
def shipments_modified_range(
    start_date: date = Query(...),
    end_date:   date = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Envíos actualizados (ModifiedDate) en el intervalo. Sirve para sincronización.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"]       = [date_range_filter("ModifiedDate", start, end)]
    req["SortField"]     = "ModifiedDate"
    req["SortDirection"] = "Descending"
    return _call("ShipmentGetList", req)


# ── GET /shipments/{shipment_id}  ─────────────────────────────────────────────

@router.get("/{shipment_id}", summary="Detalle de un envío")
def get_shipment(shipment_id: str):
    """Devuelve el detalle completo de un envío por su ShipmentID (GUID)."""
    req = base_request()
    req["ObjectIDs"] = [shipment_id]
    return _call("ShipmentGet", req)


# ── GET /shipments/carriers  ──────────────────────────────────────────────────

@router.get("/carriers/list", summary="Transportistas disponibles")
def list_carriers(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """Devuelve el catálogo de transportistas (carriers) disponibles."""
    req = base_request(page=page, page_size=page_size)
    return _call("ShippingCarrierGetList", req)
