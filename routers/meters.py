"""
/meters  – Lecturas de medidores (raw y facturables) vía SOAP MPS API.

RawMeterReadFeed campos:
  AssetID, AssetNumber, ControlID, Count, Credit, InScope, IsCredit,
  IsRollOver, Manufacturer, MeterName, ModifiedDate, RawMeterReadID,
  ReadDate, SerialNumber, Valid, VersionNumber

BillableMeterReadFeed campos:
  AssetID, AssetNumber, BillableMeterReadID, ChargebackCodeID, ControlID,
  Count, Manufacturer, MeterName, ModifiedDate, RawMeterReadDate, ReadDate,
  SerialNumber, VersionNumber, Volume
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


# ══════════════════════════════════════════════════════════════════════════════
# RAW METERS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/raw", summary="Lecturas raw de medidores – todos los activos")
def raw_meters_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    sort_field: Optional[str] = Query("ReadDate", description="Campo de ordenamiento"),
    sort_direction: str = Query("Descending", description="Ascending | Descending"),
):
    """
    Lista todas las lecturas raw de medidores registradas en la cuenta, paginadas.
    """
    req = base_request(page=page, page_size=page_size)
    req["SortField"]     = sort_field
    req["SortDirection"] = sort_direction
    return _call("RawMeterGetList", req)


@router.get("/raw/today", summary="Lecturas raw del día de hoy")
def raw_meters_today(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Devuelve todas las lecturas raw cuya ReadDate sea hoy (UTC).
    Útil para dashboards en tiempo real.
    """
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end   = datetime.combine(today, datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"] = [date_range_filter("ReadDate", start, end)]
    req["SortField"]     = "ReadDate"
    req["SortDirection"] = "Descending"
    return _call("RawMeterGetList", req)


@router.get("/raw/range", summary="Lecturas raw en intervalo de fechas")
def raw_meters_range(
    start_date: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date:   date = Query(..., description="Fecha fin   (YYYY-MM-DD)"),
    meter_name: Optional[str] = Query(None, description="Ej: 'Total Impressions'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Lecturas raw de todos los activos entre `start_date` y `end_date`.
    Opcionalmente filtra por nombre de medidor (MeterName).
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    filters = [date_range_filter("ReadDate", start, end)]
    if meter_name:
        filters.append(value_filter("MeterName", [meter_name]))
    req["Filters"] = filters
    req["SortField"]     = "ReadDate"
    req["SortDirection"] = "Descending"
    return _call("RawMeterGetList", req)


@router.get("/raw/latest", summary="Última lectura raw por activo")
def raw_meters_latest(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Devuelve la lectura más reciente de cada combinación Asset/MeterName.
    Ideal para conocer el estado actual de toda la flota.
    """
    req = base_request(page=page, page_size=page_size)
    req["SortField"]     = "ReadDate"
    req["SortDirection"] = "Descending"
    return _call("RawMeterGetLatestList", req)


@router.get("/raw/asset/{asset_id}", summary="Lecturas raw de un activo específico")
def raw_meters_by_asset(
    asset_id: str,
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
    meter_name: Optional[str]  = Query(None, description="Filtrar por nombre de medidor"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Lecturas raw para un activo concreto (AssetID).
    Si se proveen fechas, filtra el intervalo; sin fechas devuelve el historial completo.
    """
    req = base_request()
    req["ObjectIDs"] = [asset_id]
    return _call("RawMeterGet", req)


@router.get("/raw/serial/{serial_number}", summary="Lecturas raw por número de serie")
def raw_meters_by_serial(
    serial_number: str,
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Lecturas raw filtradas por SerialNumber del dispositivo.
    """
    start = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0)) if end_date else None

    req = base_request(page=page, page_size=page_size)
    filters = [value_filter("SerialNumber", [serial_number])]
    if start and end:
        filters.append(date_range_filter("ReadDate", start, end))
    req["Filters"] = filters
    req["SortField"]     = "ReadDate"
    req["SortDirection"] = "Descending"
    return _call("RawMeterGetList", req)


# ══════════════════════════════════════════════════════════════════════════════
# BILLABLE METERS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/billable", summary="Medidores facturables – todos los activos")
def billable_meters_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    sort_direction: str = Query("Descending"),
):
    """
    Lista todas las lecturas facturables (BillableMeterRead) de la cuenta.
    """
    req = base_request(page=page, page_size=page_size)
    req["SortField"]     = "ReadDate"
    req["SortDirection"] = sort_direction
    return _call("BillableMeterGetList", req)


@router.get("/billable/today", summary="Medidores facturables del día de hoy")
def billable_meters_today(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Lecturas facturables generadas hoy.
    """
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end   = datetime.combine(today, datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    req["Filters"] = [date_range_filter("ReadDate", start, end)]
    req["SortField"]     = "ReadDate"
    req["SortDirection"] = "Descending"
    return _call("BillableMeterGetList", req)


@router.get("/billable/range", summary="Medidores facturables en intervalo")
def billable_meters_range(
    start_date: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date:   date = Query(..., description="Fecha fin   (YYYY-MM-DD)"),
    meter_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Lecturas facturables en el intervalo indicado.
    Clave para calcular volúmenes de impresión mensuales / trimestrales.
    """
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))

    req = base_request(page=page, page_size=page_size)
    filters = [date_range_filter("ReadDate", start, end)]
    if meter_name:
        filters.append(value_filter("MeterName", [meter_name]))
    req["Filters"] = filters
    req["SortField"]     = "ReadDate"
    req["SortDirection"] = "Descending"
    return _call("BillableMeterGetList", req)


@router.get("/billable/asset/{asset_id}", summary="Medidores facturables por activo")
def billable_meters_by_asset(asset_id: str):
    """
    Devuelve las lecturas facturables registradas para un activo específico.
    """
    req = base_request()
    req["ObjectIDs"] = [asset_id]
    return _call("BillableMeterGet", req)


# ══════════════════════════════════════════════════════════════════════════════
# BILLABLE ASSET COUNT
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/billable/asset-count", summary="Conteo de activos facturables por grupo")
def billable_asset_count(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Cantidad de activos facturables agrupados por plan de precio y código de cargo.
    """
    req = base_request(page=page, page_size=page_size)
    return _call("BillableAssetCountGetList", req)
