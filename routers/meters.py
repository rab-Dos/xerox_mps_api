"""
/meters  – Lecturas de medidores (raw y facturables) vía SOAP MPS API.
"""
from __future__ import annotations
from datetime import date, datetime
import pprint, traceback
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from soap_client import (
    base_request, date_range_filter, value_filter,
    apply_filters, call_soap,
)

router = APIRouter()


def _call(operation: str, req: dict):
    print(f"\n🚀 [{operation}] Payload:")
    pprint.pprint({k: v for k, v in req.items() if k != "_filters"})
    try:
        return call_soap(operation, req)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# RAW METERS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/raw", summary="Lecturas raw – todos los activos")
def raw_meters_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    sort_field: Optional[str] = Query("ReadDate"),
    sort_direction: str = Query("Descending"),
):
    req = base_request(page=page, page_size=page_size)
    req["SortField"]     = sort_field
    req["SortDirection"] = sort_direction
    return _call("RawMeterGetList", req)


@router.get("/raw/today", summary="Lecturas raw del día de hoy")
def raw_meters_today(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end   = datetime.combine(today, datetime.max.time().replace(microsecond=0))
    req = base_request(page=page, page_size=page_size)
    apply_filters(req, [date_range_filter("ReadDate", start, end)])
    req["SortField"] = "ReadDate"
    req["SortDirection"] = "Descending"
    return _call("RawMeterGetList", req)


@router.get("/raw/range", summary="Lecturas raw en intervalo de fechas")
def raw_meters_range(
    start_date: date = Query(...),
    end_date:   date = Query(...),
    meter_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))
    filters = [date_range_filter("ReadDate", start, end)]
    if meter_name:
        filters.append(value_filter("MeterName", [meter_name]))
    req = base_request(page=page, page_size=page_size)
    apply_filters(req, filters)
    req["SortField"] = "ReadDate"
    req["SortDirection"] = "Descending"
    return _call("RawMeterGetList", req)


@router.get("/raw/latest", summary="Última lectura raw por activo")
def raw_meters_latest(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    req = base_request(page=page, page_size=page_size)
    req["SortField"]     = "ReadDate"
    req["SortDirection"] = "Descending"
    return _call("RawMeterGetLatestList", req)


@router.get("/raw/asset/{asset_id}", summary="Lecturas raw de un activo")
def raw_meters_by_asset(asset_id: str):
    req = base_request()
    req["ObjectIDs"] = {"string": [asset_id]}
    return _call("RawMeterGet", req)


@router.get("/raw/serial/{serial_number}", summary="Lecturas raw por número de serie")
def raw_meters_by_serial(
    serial_number: str,
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    filters = [value_filter("SerialNumber", [serial_number])]
    if start_date and end_date:
        start = datetime.combine(start_date, datetime.min.time())
        end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))
        filters.append(date_range_filter("ReadDate", start, end))
    req = base_request(page=page, page_size=page_size)
    apply_filters(req, filters)
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
    req = base_request(page=page, page_size=page_size)
    req["SortField"]     = "ReadDate"
    req["SortDirection"] = sort_direction
    return _call("BillableMeterGetList", req)


@router.get("/billable/today", summary="Medidores facturables del día de hoy")
def billable_meters_today(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end   = datetime.combine(today, datetime.max.time().replace(microsecond=0))
    req = base_request(page=page, page_size=page_size)
    apply_filters(req, [date_range_filter("ReadDate", start, end)])
    req["SortField"]     = "ReadDate"
    req["SortDirection"] = "Descending"
    return _call("BillableMeterGetList", req)


@router.get("/billable/range", summary="Medidores facturables en intervalo")
def billable_meters_range(
    start_date: date = Query(...),
    end_date:   date = Query(...),
    meter_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    start = datetime.combine(start_date, datetime.min.time())
    end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))
    filters = [date_range_filter("ReadDate", start, end)]
    if meter_name:
        filters.append(value_filter("MeterName", [meter_name]))
    req = base_request(page=page, page_size=page_size)
    apply_filters(req, filters)
    req["SortField"]     = "ReadDate"
    req["SortDirection"] = "Descending"
    return _call("BillableMeterGetList", req)


@router.get("/billable/asset/{asset_id}", summary="Medidores facturables por activo")
def billable_meters_by_asset(asset_id: str):
    req = base_request()
    req["ObjectIDs"] = {"string": [asset_id]}
    return _call("BillableMeterGet", req)


@router.get("/billable/asset-count", summary="Conteo de activos facturables")
def billable_asset_count(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    req = base_request(page=page, page_size=page_size)
    return _call("BillableAssetCountGetList", req)
