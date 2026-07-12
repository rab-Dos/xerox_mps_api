"""
/assets  – Consulta de activos (impresoras/MFDs) vía SOAP MPS API.

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


# ── GET /assets  ──────────────────────────────────────────────────────────────

@router.get("/", summary="Listar todos los activos")
def list_assets(
    page: int = Query(1,   ge=1,   description="Número de página"),
    page_size: int = Query(500, ge=1, le=1000, description="Registros por página"),
    sort_field: Optional[str] = Query(None, description="Campo de ordenamiento (ej. SerialNumber)"),
    sort_direction: Optional[str] = Query("Ascending", description="Ascending | Descending"),
):
    """
    Devuelve la lista paginada de todos los activos (impresoras/MFDs) registrados
    en la cuenta Xerox MPS.
    """
    req = base_request(page=page, page_size=page_size)
    if sort_field:
        req["SortField"] = sort_field
        req["SortDirection"] = sort_direction
    return _call("AssetGetList", req)


# ── GET /assets/today  ────────────────────────────────────────────────────────

@router.get("/today", summary="Activos modificados hoy")
def assets_modified_today(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Filtra activos cuya fecha de modificación (ModifiedDate) corresponda al día de hoy.
    """
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end   = datetime.combine(today, datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"] = [date_range_filter("ModifiedDate", start, end)]
    return _call("AssetGetList", req)


# ── GET /assets/range  ────────────────────────────────────────────────────────

@router.get("/range", summary="Activos modificados en un intervalo")
def assets_by_date_range(
    start_date: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date:   date = Query(..., description="Fecha fin   (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Filtra activos modificados entre `start_date` y `end_date` (inclusive).
    Útil para detectar nuevos equipos o cambios de configuración.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"] = [date_range_filter("ModifiedDate", start, end)]
    return _call("AssetGetList", req)


# ── GET /assets/scope-changes  ────────────────────────────────────────────────

@router.get("/scope-changes", summary="Activos con cambio de alcance en intervalo")
def assets_scope_changes(
    start_date: date = Query(..., description="Fecha inicio"),
    end_date:   date = Query(..., description="Fecha fin"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Detecta equipos que entraron o salieron del alcance contractual (ScopeChangeDate)
    en el intervalo indicado.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"] = [date_range_filter("ScopeChangeDate", start, end)]
    return _call("AssetGetList", req)


# ── GET /assets/in-scope-count  ───────────────────────────────────────────────

@router.get("/in-scope-count", summary="Conteo de activos en alcance por grupo")
def in_scope_count(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Devuelve el conteo de activos vigentes en el contrato, agrupados por código de cargo.
    """
    req = base_request(page=page, page_size=page_size)
    return _call("AssetInScopeCountGetList", req)


# ── GET /assets/{asset_id}  ───────────────────────────────────────────────────

@router.get("/{asset_id}", summary="Detalle completo de un activo")
def get_asset(asset_id: str):
    """
    Devuelve todos los campos de un activo específico por su AssetID (GUID).
    """
    req = base_request()
    req["ObjectIDs"] = [asset_id]
    return _call("AssetGet", req)


# ── GET /assets/{asset_id}/locations  ─────────────────────────────────────────

@router.get("/{asset_id}/locations", summary="Historial de ubicaciones del activo")
def asset_locations(asset_id: str):
    """
    Devuelve las ubicaciones registradas para el activo indicado.
    """
    req = base_request()
    req["Filters"] = [value_filter("AssetID", [asset_id])]
    return _call("AssetLocationGetList", req)


# ── GET /assets/{asset_id}/change-history  ────────────────────────────────────

@router.get("/{asset_id}/change-history", summary="Historial de cambios del activo")
def asset_change_history(
    asset_id: str,
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Devuelve el historial de cambios (configuración, estado, contrato) del activo.
    Si se indican fechas, filtra por ChangeHistoryDate.
    """
    req = base_request(page=page, page_size=page_size)
    filters = [value_filter("AssetID", [asset_id])]
    if start_date and end_date:
        start = datetime.combine(start_date, datetime.min.time())
        end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))
        filters.append(date_range_filter("ChangeHistoryDate", start, end))
    req["Filters"] = filters
    return _call("AssetChangeHistoryGetList", req)


# ── GET /assets/{asset_id}/price-plans  ──────────────────────────────────────

@router.get("/{asset_id}/price-plans", summary="Planes de precio del activo")
def asset_price_plans(asset_id: str):
    req = base_request()
    req["Filters"] = [value_filter("AssetID", [asset_id])]
    return _call("AssetPricePlanGetList", req)
