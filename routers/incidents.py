"""
/incidents  – Incidencias Break-Fix y Supplies vía SA-API REST.

La SA-API limita el rango máximo a 90 días por consulta.
Tipos disponibles: Breakfix | Supply | Both
Estados disponibles: Open | Closed | Both
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sa_client import sa_client

router = APIRouter()


def _fmt(d: date) -> str:
    """Convierte fecha a string yyyy-mm-dd para la SA-API."""
    return d.strftime("%Y-%m-%d")


def _validate_range(start: date, end: date, max_days: int = 90):
    if (end - start).days > max_days:
        raise HTTPException(
            status_code=400,
            detail=f"El rango máximo es {max_days} días. "
                   f"Diferencia actual: {(end - start).days} días."
        )
    if start > end:
        raise HTTPException(status_code=400, detail="start_date debe ser anterior a end_date.")


# ══════════════════════════════════════════════════════════════════════════════
# LECTURA DE INCIDENCIAS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/{serial_number}/{mac_address}",
            summary="Incidencias de un dispositivo en intervalo de fechas")
def get_incidents(
    serial_number: str,
    mac_address:   str,
    start_date: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date:   date = Query(..., description="Fecha fin    (YYYY-MM-DD, máx 90 días desde inicio)"),
    incident_type: str = Query("Both", description="Breakfix | Supply | Both"),
    status:        str = Query("Both", description="Open | Closed | Both"),
    sandbox:       bool = Query(False, description="True para usar el entorno de pruebas"),
):
    """
    Consulta incidencias (tickets Break-Fix y/o órdenes de suministro)
    para un dispositivo en un rango de hasta 90 días.

    - **Breakfix**: fallas mecánicas / eléctricas.
    - **Supply**: pedidos de tóner, tambores u otros consumibles.
    - **Both**: ambas categorías.
    """
    _validate_range(start_date, end_date)
    try:
        return sa_client.get_incidents(
            serial=serial_number,
            mac=mac_address,
            start_date=_fmt(start_date),
            end_date=_fmt(end_date),
            incident_type=incident_type,
            status=status,
            sandbox=sandbox,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{serial_number}/{mac_address}/today",
            summary="Incidencias del día de hoy")
def get_incidents_today(
    serial_number: str,
    mac_address:   str,
    incident_type: str = Query("Both"),
    status:        str = Query("Both"),
    sandbox:       bool = Query(False),
):
    """
    Atajo para consultar incidencias del día en curso (UTC).
    """
    today = date.today()
    try:
        return sa_client.get_incidents(
            serial=serial_number,
            mac=mac_address,
            start_date=_fmt(today),
            end_date=_fmt(today),
            incident_type=incident_type,
            status=status,
            sandbox=sandbox,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{serial_number}/{mac_address}/last-week",
            summary="Incidencias de los últimos 7 días")
def get_incidents_last_week(
    serial_number: str,
    mac_address:   str,
    incident_type: str = Query("Both"),
    status:        str = Query("Both"),
    sandbox:       bool = Query(False),
):
    """Incidencias de los últimos 7 días naturales."""
    end   = date.today()
    start = end - timedelta(days=7)
    try:
        return sa_client.get_incidents(
            serial=serial_number,
            mac=mac_address,
            start_date=_fmt(start),
            end_date=_fmt(end),
            incident_type=incident_type,
            status=status,
            sandbox=sandbox,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{serial_number}/{mac_address}/last-month",
            summary="Incidencias de los últimos 30 días")
def get_incidents_last_month(
    serial_number: str,
    mac_address:   str,
    incident_type: str = Query("Both"),
    status:        str = Query("Both"),
    sandbox:       bool = Query(False),
):
    """Incidencias de los últimos 30 días naturales."""
    end   = date.today()
    start = end - timedelta(days=30)
    try:
        return sa_client.get_incidents(
            serial=serial_number,
            mac=mac_address,
            start_date=_fmt(start),
            end_date=_fmt(end),
            incident_type=incident_type,
            status=status,
            sandbox=sandbox,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{serial_number}/{mac_address}/open",
            summary="Incidencias abiertas – últimos 90 días")
def get_open_incidents(
    serial_number: str,
    mac_address:   str,
    incident_type: str = Query("Both"),
    sandbox:       bool = Query(False),
):
    """
    Atajo para ver únicamente las incidencias en estado Open de los últimos 90 días.
    """
    end   = date.today()
    start = end - timedelta(days=90)
    try:
        return sa_client.get_incidents(
            serial=serial_number,
            mac=mac_address,
            start_date=_fmt(start),
            end_date=_fmt(end),
            incident_type=incident_type,
            status="Open",
            sandbox=sandbox,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# CREAR INCIDENCIA
# ══════════════════════════════════════════════════════════════════════════════

class CreateIncidentRequest(BaseModel):
    service_id:      str
    summary:         str
    requester_name:  str
    requester_phone: str
    requester_email: str
    sandbox:         bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "service_id":      "af25b99b-a71f-e711-80f0-0025b53f03fb",
                "summary":         "Atasco de papel en bandeja 2",
                "requester_name":  "Juan García",
                "requester_phone": "55 1234 5678",
                "requester_email": "juan.garcia@empresa.com",
                "sandbox":         False,
            }
        }
    }


@router.post("/{serial_number}/{mac_address}",
             summary="Crear una nueva incidencia para un dispositivo")
def create_incident(
    serial_number: str,
    mac_address:   str,
    body: CreateIncidentRequest,
):
    """
    Abre una nueva incidencia (Break-Fix o Supplies) para el dispositivo indicado.

    Antes de llamar este endpoint, obtén el `service_id` correcto mediante
    `GET /services/entitlements/{serial_number}/{mac_address}`.

    Devuelve: `IncidentNumber` y `CreatedDate`.
    """
    try:
        return sa_client.create_incident(
            serial=serial_number,
            mac=mac_address,
            service_id=body.service_id,
            summary=body.summary,
            requester_name=body.requester_name,
            requester_phone=body.requester_phone,
            requester_email=body.requester_email,
            sandbox=body.sandbox,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# ACTUALIZAR MEDIDORES VÍA SA-API
# ══════════════════════════════════════════════════════════════════════════════

class MeterRead(BaseModel):
    MeterName:  str
    MeterCount: int


class UpdateMetersRequest(BaseModel):
    meters:          List[MeterRead]
    meter_read_date: Optional[str] = None
    sandbox:         bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "meters": [
                    {"MeterName": "Total Impressions",  "MeterCount": 150432},
                    {"MeterName": "Color Impressions",  "MeterCount": 42100},
                ],
                "meter_read_date": "2025-07-12T10:00:00",
                "sandbox": False,
            }
        }
    }


@router.post("/{serial_number}/{mac_address}/meters",
             summary="Enviar lecturas de medidores vía SA-API")
def update_meters_saapi(
    serial_number: str,
    mac_address:   str,
    body: UpdateMetersRequest,
):
    """
    Actualiza las lecturas de medidores (contador de páginas) para el dispositivo
    usando la SA-API REST.

    Nombres de medidores soportados (ver documentación Xerox):
    `Total Impressions`, `Color Impressions`, `Black Impressions`, etc.
    """
    try:
        ok = sa_client.update_meters(
            serial=serial_number,
            mac=mac_address,
            meters=[m.model_dump() for m in body.meters],
            meter_read_date=body.meter_read_date,
            sandbox=body.sandbox,
        )
        return {"success": ok, "message": "Lecturas de medidores enviadas correctamente."}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
