"""
/assets - Consulta de activos (impresoras/MFDs) via SOAP MPS API.

Campos disponibles en AssetFeed:
  AccountID, AccountName, AssetID, AssetNumber, AssetTag3rdParty,
  ChangeHistoryDate, ContractNumber, ContractTypeDescription, ControlID,
  DNSName, Group, GroupID, InScope, IsDeleted, IsDirectDevice, LocationID,
  MACAddress, Manufacturer, ManufacturerID, Model, ModelID, ModifiedDate,
  PricePlanID, ScopeChangeDate, SerialNumber, VersionNumber
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


# GET /assets
# ------------------------------------------------------------------------------

@router.get("/", summary="Listar todos los activos")
def list_assets(
    page: int = Query(1,   ge=1,   description="Numero de pagina"),
    page_size: int = Query(500, ge=1, le=1000, description="Registros por pagina"),
    sort_field: Optional[str] = Query("AssetNumber", description="Campo de ordenamiento"),
    sort_direction: str = Query("Ascending", description="Ascending | Descending"),
):
    """
    Devuelve la lista completa de dispositivos bajo contrato, paginados.
    """
    req = base_request(page=page, page_size=page_size)
    req["SortField"]     = sort_field
    req["SortDirection"] = sort_direction
    return _call("AssetGetList", req)


# GET /assets/range
# ------------------------------------------------------------------------------

@router.get("/range", summary="Activos modificados en un rango de fechas")
def assets_by_date_range(
    start_date: date = Query(..., description="Fecha inicial (YYYY-MM-DD)"),
    end_date:   date = Query(..., description="Fecha final (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Filtra los activos cuya ModifiedDate se encuentre en el rango provisto.
    Util para procesos de sincronizacion incremental.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    filters = [date_range_filter("ModifiedDate", start, end)]
    req = base_request(page=page, page_size=page_size)
    apply_filters(req, filters)
    req["SortField"]     = "ModifiedDate"
    req["SortDirection"] = "Descending"
    return _call("AssetGetList", req)


# GET /assets/{asset_id}
# ------------------------------------------------------------------------------

@router.get("/{asset_id}", summary="Detalle de un activo especifico")
def get_asset_by_id(asset_id: str):
    """
    Devuelve la ficha tecnica completa de un activo usando su ID unico (GUID).
    """
    req = base_request()
    req["ObjectIDs"] = {"string": [asset_id]}
    return _call("AssetGet", req)


# GET /assets/serial/{serial_number}
# ------------------------------------------------------------------------------

@router.get("/serial/{serial_number}", summary="Buscar activo por Numero de Serie")
def get_asset_by_serial(serial_number: str):
    """
    Busca un dispositivo por su numero de serie exacto de fabricante.
    """
    filters = [value_filter("SerialNumber", [serial_number])]
    req = base_request(page=1, page_size=1)
    apply_filters(req, filters)
    return _call("AssetGetList", req)


# GET /assets/{asset_id}/locations
# ------------------------------------------------------------------------------

@router.get("/{asset_id}/locations", summary="Historial de ubicaciones del activo")
def asset_locations(asset_id: str):
    """
    Lista las sedes, departamentos o direcciones fisicas registradas para el activo indicado.
    """
    req = base_request()
    filters = [value_filter("AssetID", [asset_id])]
    apply_filters(req, filters)
    return _call("AssetLocationGetList", req)


# GET /assets/{asset_id}/change-history
# ------------------------------------------------------------------------------

@router.get("/{asset_id}/change-history", summary="Historial de cambios del activo")
def asset_change_history(
    asset_id: str,
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Devuelve el historial de cambios (configuracion, estado, contrato) del activo.
    Si se indican fechas, filtra por ChangeHistoryDate.
    """
    req = base_request(page=page, page_size=page_size)
    filters = [value_filter("AssetID", [asset_id])]
    if start_date and end_date:
        start = datetime.combine(start_date, datetime.min.time())
        end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))
        filters.append(date_range_filter("ChangeHistoryDate", start, end))
    apply_filters(req, filters)
    return _call("AssetChangeHistoryGetList", req)


# GET /assets/{asset_id}/price-plans
# ------------------------------------------------------------------------------

@router.get("/{asset_id}/price-plans", summary="Planes de precios del activo")
def asset_price_plans(asset_id: str):
    """
    Lista las tarifas y planes de precios asociados al activo de manera historica o vigente.
    """
    req = base_request()
    filters = [value_filter("AssetID", [asset_id])]
    apply_filters(req, filters)
    return _call("AssetPricePlanGetList", req)