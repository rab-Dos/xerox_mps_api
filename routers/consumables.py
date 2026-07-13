"""
/consumables - Niveles y estado de consumibles (toner, tambores, etc.) via SOAP MPS API.

AssetConsumablesFeed campos:
  AccountID, AssetID,
  Consumables[]: Description, MaxCapacity, SupplyLevel, Unit
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


# GET /consumables
# ------------------------------------------------------------------------------

@router.get("/", summary="Estado de consumibles de todos los activos")
def list_consumables(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Devuelve los niveles actuales de consumibles (toner, drum, fuser, etc.)
    para todos los activos de la cuenta.

    SupplyLevel indica el porcentaje restante del consumible.
    """
    req = base_request(page=page, page_size=page_size)
    return _call("AssetConsumablesGetList", req)


# GET /consumables/asset/{asset_id}
# ------------------------------------------------------------------------------

@router.get("/asset/{asset_id}", summary="Consumibles de un activo especifico")
def get_asset_consumables(asset_id: str):
    """
    Muestra los niveles detallados de cada suministro de un dispositivo concreto.
    """
    req = base_request()
    req["ObjectIDs"] = {"string": [asset_id]}
    return _call("AssetConsumablesGet", req)


# GET /consumables/orders
# ------------------------------------------------------------------------------

@router.get("/orders", summary="Listar ordenes de suministro")
def list_supplier_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    start_date: Optional[date] = Query(None, description="Fecha inicio de la orden"),
    end_date:   Optional[date] = Query(None, description="Fecha fin de la orden"),
):
    """
    Devuelve las ordenes de suministro registradas.
    Si se proporcionan fechas, filtra por OrderDate del proveedor.
    """
    req = base_request(page=page, page_size=page_size)
    if start_date and end_date:
        start = datetime.combine(start_date, datetime.min.time())
        end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))
        filters = [date_range_filter("OrderDate", start, end)]
        apply_filters(req, filters)
    return _call("SupplierOrderGetList", req)


@router.get("/orders/{order_id}", summary="Detalle de una orden de suministro")
def get_supplier_order(order_id: str):
    """Devuelve el detalle completo de una orden de suministro por su ID."""
    req = base_request()
    req["ObjectIDs"] = {"string": [order_id]}
    return _call("SupplierOrderGet", req)


# GET /consumables/catalog
# ------------------------------------------------------------------------------

@router.get("/catalog", summary="Catalogo de suministros disponibles")
def consumables_catalog(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Retorna el catalogo completo de articulos/partes homologadas para reposicion
    (toners, cartuchos, kits de mantenimiento) asociados a la cuenta.
    """
    req = base_request(page=page, page_size=page_size)
    return _call("SupplyItemCatalogGetList", req)