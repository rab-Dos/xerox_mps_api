"""
/auth  – Gestión de tokens SA-API (REST).
"""
from fastapi import APIRouter, HTTPException
from sa_client import sa_client

router = APIRouter()


@router.post("/token", summary="Crear token SA-API")
def create_token():
    """
    Solicita un nuevo par AccessToken / RefreshToken usando el API Key configurado.
    El token se almacena internamente y se renueva de forma automática en cada llamada.
    """
    try:
        return sa_client.create_token()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/token", summary="Refrescar token SA-API")
def refresh_token():
    """Renueva el token actual usando el RefreshToken almacenado."""
    try:
        return sa_client.refresh_token()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/token", summary="Eliminar token SA-API")
def delete_token():
    """Invalida el token activo (AccessToken + RefreshToken)."""
    try:
        ok = sa_client.delete_token()
        return {"deleted": ok}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
