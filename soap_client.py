"""
Crea y cachea el cliente SOAP de Zeep con autenticación WS-Security.
"""
from functools import lru_cache
from zeep import Client
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken
import httpx
from config import MPS_WSDL_URL, MPS_USERNAME, MPS_PASSWORD, MPS_API_KEY, MPS_ACCOUNT_ID, DEFAULT_PAGE_SIZE


@lru_cache(maxsize=1)
def get_soap_client() -> Client:
    """Devuelve un cliente SOAP reutilizable con credenciales."""
    transport = Transport(timeout=60, operation_timeout=120)
    client = Client(
        wsdl=MPS_WSDL_URL,
        wsse=UsernameToken(MPS_USERNAME, MPS_PASSWORD),
        transport=transport,
    )
    return client


def base_request(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE, **extra) -> dict:
    """Construye el diccionario base que requieren todas las operaciones SOAP."""
    return {
        "APIKey":      MPS_API_KEY,
        "AccountID":   MPS_ACCOUNT_ID,
        "PageNumber":  page,
        "PageSize":    page_size,
        **extra,
    }


def date_range_filter(column: str, start, end) -> dict:
    """Construye un DateRangeFilterParameter para los Filters de SearchRequest."""
    return {
        "_value_1": {
            "ColumnName": column,
            "StartDate":  start,
            "EndDate":    end,
        },
        "_attr_1": {
            "{http://www.w3.org/2001/XMLSchema-instance}type":
                "{http://api.services.xerox.com}DateRangeFilterParameter"
        },
    }


def value_filter(column: str, values: list) -> dict:
    """Construye un FilterParameter de valores exactos."""
    return {
        "_value_1": {
            "ColumnName":   column,
            "ColumnValues": {"string": values},
        },
        "_attr_1": {
            "{http://www.w3.org/2001/XMLSchema-instance}type":
                "{http://api.services.xerox.com}FilterParameter"
        },
    }


def call_soap(operation: str, **kwargs):
    """Ejecuta una operación SOAP y devuelve el resultado serializado."""
    client = get_soap_client()
    method = getattr(client.service, operation)
    result = method(request=kwargs)
    # Zeep devuelve objetos; convertimos a dict vía __dict__ o serialización
    return _serialize(result)


def _serialize(obj):
    """Convierte recursivamente objetos Zeep en estructuras Python nativas."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if hasattr(obj, "__class__") and hasattr(obj, "__dict__"):
        data = {}
        for k, v in obj.__dict__.items():
            if not k.startswith("_"):
                data[k] = _serialize(v)
        return data
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    try:
        from zeep.helpers import serialize_object
        return serialize_object(obj)
    except Exception:
        return str(obj)
