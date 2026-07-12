"""
/consumables  – Niveles y estado de consumibles (tóner, tambores, etc.)
               vía SOAP MPS API.

AssetConsumablesFeed campos:
  AccountID, AssetID,
  Consumables[]: Description, MaxCapacity, SupplyLevel, Unit
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


# ── GET /consumables  ─────────────────────────────────────────────────────────

@router.get("/", summary="Estado de consumibles de todos los activos")
def list_consumables(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Devuelve los niveles actuales de consumibles (tóner, drum, fuser, etc.)
    para todos los activos de la cuenta.

    `SupplyLevel` indica el porcentaje restante del consumible.
    """
    req = base_request(page=page, page_size=page_size)
    return _call("AssetConsumablesGetList", req)


# ── GET /consumables/asset/{asset_id}  ───────────────────────────────────────

@router.get("/asset/{asset_id}", summary="Consumibles de un activo específico")
def consumables_by_asset(asset_id: str):
    """
    Devuelve los niveles de consumibles para el activo indicado (AssetID).
    """
    req = base_request()
    req["Filters"] = [value_filter("AssetID", [asset_id])]
    return _call("AssetConsumablesGetList", req)


# ── GET /consumables/low  ─────────────────────────────────────────────────────

@router.get("/low", summary="Activos con consumibles bajos")
def low_consumables(
    threshold: int = Query(20, ge=0, le=100, description="Umbral de nivel bajo (%)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Filtra todos los activos que tienen al menos un consumible con nivel ≤ `threshold`%.
    Los resultados se procesan en memoria después de obtenerlos de la API Xerox,
    ya que el SOAP no admite filtro por SupplyLevel directamente.
    """
    req = base_request(page=page, page_size=page_size)
    raw = _call("AssetConsumablesGetList", req)

    low = []
    items = raw if isinstance(raw, list) else (raw.get("AssetConsumablesFeed") or [])
    for asset in items:
        consumables = asset.get("Consumables") or []
        low_items = [
            c for c in consumables
            if c.get("SupplyLevel") is not None and c["SupplyLevel"] <= threshold
        ]
        if low_items:
            low.append({**asset, "Consumables": low_items})
    return {"threshold_pct": threshold, "assets_with_low_consumables": low}


# ── GET /consumables/ohb  ─────────────────────────────────────────────────────

@router.get("/ohb", summary="Inventario OHB (On-Hand Buffer) de consumibles")
def consumables_ohb(asset_id: str = Query(..., description="AssetID del equipo")):
    """
    Devuelve el inventario de buffer a mano (On-Hand Buffer) para el activo indicado.
    Útil para gestión de stock en sitio.
    """
    req = base_request()
    req["Filters"] = [value_filter("AssetID", [asset_id])]
    return _call("AssetConsumablesOHBGet", req)


# ── GET /consumables/orders  ──────────────────────────────────────────────────

@router.get("/orders", summary="Órdenes de suministro (SupplierOrders)")
def supplier_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    start_date: Optional[date] = Query(None, description="Fecha inicio de la orden"),
    end_date:   Optional[date] = Query(None, description="Fecha fin de la orden"),
):
    """
    Devuelve las órdenes de suministro registradas.
    Si se proporcionan fechas, filtra por OrderDate del proveedor.
    """
    req = base_request(page=page, page_size=page_size)
    if start_date and end_date:
        start = datetime.combine(start_date, datetime.min.time())
        end   = datetime.combine(end_date,   datetime.max.time().replace(microsecond=0))
        req["Filters"] = [date_range_filter("OrderDate", start, end)]
    return _call("SupplierOrderGetList", req)


@router.get("/orders/{order_id}", summary="Detalle de una orden de suministro")
def get_supplier_order(order_id: str):
    """Devuelve el detalle completo de una orden de suministro por su ID."""
    req = base_request()
    req["ObjectIDs"] = [order_id]
    return _call("SupplierOrderGet", req)


# ── GET /consumables/catalog  ─────────────────────────────────────────────────

@router.get("/catalog", summary="Catálogo de suministros disponibles")
def consumables_catalog(
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
):
    """
    Lista todos los suministros (tóner, partes, etc.) disponibles en el catálogo Xerox.
    """
    req = base_request(page=page, page_size=page_size)
    return _call("SupplyGetList", req)
