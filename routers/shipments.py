"""
/shipments - Envios de suministros via SOAP MPS API.

ShipmentFeed campos:
  CarrierID, CarrierName, ChargebackCodeID, ControlID, ModifiedDate,
  ReceivedDate, ShipmentID, ShippedDate, Status, StatusID,
  SupplierOrderID, TrackingNumber, VersionNumber
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
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


# GET /shipments
# ------------------------------------------------------------------------------

@router.get("/", summary="Listar todos los envios")
def list_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    sort_direction: str = Query("Descending"),
):
    """
    Devuelve todos los envios registrados en la cuenta, paginados.
    """
    req = base_request(page=page, page_size=page_size)
    req["SortField"]     = "ShippedDate"
    req["SortDirection"] = sort_direction
    return _call("ShipmentGetList", req)


# GET /shipments/range
# ------------------------------------------------------------------------------

@router.get("/range", summary="Envios despachados en rango de fechas")
def shipments_by_range(
    start_date: date = Query(...),
    end_date:   date = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Filtra los envios cuya ShippedDate se encuentre en el rango provisto.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    filters = [date_range_filter("ShippedDate", start, end)]
    apply_filters(req, filters)
    req["SortField"]     = "ShippedDate"
    req["SortDirection"] = "Descending"
    return _call("ShipmentGetList", req)


# GET /shipments/modified-range
# ------------------------------------------------------------------------------

@router.get("/modified-range", summary="Envios modificados en intervalo")
def shipments_modified_range(
    start_date: date = Query(...),
    end_date:   date = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Envios actualizados (ModifiedDate) en el intervalo. Sirve para sincronizacion.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    filters = [date_range_filter("ModifiedDate", start, end)]
    apply_filters(req, filters)
    req["SortField"]     = "ModifiedDate"
    req["SortDirection"] = "Descending"
    return _call("ShipmentGetList", req)


# GET /shipments/{shipment_id}
# ------------------------------------------------------------------------------

@router.get("/{shipment_id}", summary="Detalle de un envio")
def get_shipment(shipment_id: str):
    """Devuelve el detalle completo de un envio por su ShipmentID (GUID)."""
    req = base_request()
    req["ObjectIDs"] = {"string": [shipment_id]}
    return _call("ShipmentGet", req)


# GET /shipments/carriers
# ------------------------------------------------------------------------------

@router.get("/carriers/list", summary="Transportistas disponibles")
def list_carriers(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Lista las empresas fleteras y couriers homologados (DHL, FedEx, UPS, etc.)
    registrados para el despacho de suministros.
    """
    req = base_request(page=page, page_size=page_size)
    return _call("CarrierGetList", req)