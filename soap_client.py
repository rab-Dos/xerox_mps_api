"""
Cliente SOAP para Xerox MPS API.

Para operaciones sin filtros: Zeep.
Para operaciones con Filters polimorficos (xs:anyType WCF): envelope manual con lxml + httpx.
"""
from __future__ import annotations
from functools import lru_cache
from lxml import etree
import httpx
from zeep import Client, Settings
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken
from zeep.plugins import HistoryPlugin
from zeep.helpers import serialize_object
from config import (
    MPS_WSDL_URL, MPS_SERVICE_URL,
    MPS_USERNAME, MPS_PASSWORD,
    MPS_API_KEY, MPS_ACCOUNT_ID,
    DEFAULT_PAGE_SIZE,
)

# -- Namespaces ----------------------------------------------------------------
_NS = {
    "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
    "api":     "http://api.services.xerox.com",
    "mps":     "http://schemas.datacontract.org/2004/07/Xerox.MPS",
    "arr":     "http://schemas.microsoft.com/2003/10/Serialization/Arrays",
    "wsse":    "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd",
    "wsu":     "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd",
    "wsa":     "http://www.w3.org/2005/08/addressing",
    "xsi":     "http://www.w3.org/2001/XMLSchema-instance",
}

_SOAP_ACTION_BASE = "http://api.services.xerox.com/MPSAPI/"
history = HistoryPlugin()


# -- Zeep client (operaciones sin filtros) ------------------------------------
@lru_cache(maxsize=1)
def get_soap_client() -> Client:
    transport = Transport(timeout=60, operation_timeout=120)
    settings  = Settings(strict=False, xml_huge_tree=True)
    return Client(
        wsdl=MPS_WSDL_URL,
        wsse=UsernameToken(MPS_USERNAME, MPS_PASSWORD),
        transport=transport,
        settings=settings,
        plugins=[history],
    )


# -- Request base --------------------------------------------------------------
def base_request(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE, **extra) -> dict:
    return {
        "APIKey":     MPS_API_KEY,
        "AccountID":  MPS_ACCOUNT_ID,
        "PageNumber": page,
        "PageSize":   page_size,
        **extra,
    }


def _fmt(dt) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S") if hasattr(dt, "strftime") else str(dt)


# -- Constructores de filtros --------------------------------------------------
def date_range_filter(column: str, start, end) -> dict:
    return {
        "_type":      "DateRangeFilterParameter",
        "ColumnName": column,
        "StartDate":  _fmt(start),
        "EndDate":    _fmt(end),
    }


def value_filter(column: str, values: list) -> dict:
    return {
        "_type":        "FilterParameter",
        "ColumnName":   column,
        "ColumnValues": [str(v) for v in values],
    }


def apply_filters(req: dict, filters: list) -> dict:
    req["_filters"] = filters
    return req


# -- Constructor de envelope SOAP manual --------------------------------------
def _make_envelope(operation: str, req: dict) -> bytes:
    m   = _NS["mps"]
    arr = _NS["arr"]
    xsi = _NS["xsi"]

    envelope = etree.Element(
        f"{{{_NS['soapenv']}}}Envelope",
        nsmap={k: v for k, v in _NS.items()},
    )

    # Header
    header  = etree.SubElement(envelope, f"{{{_NS['soapenv']}}}Header")
    action  = etree.SubElement(header, f"{{{_NS['wsa']}}}Action")
    action.text = f"{_SOAP_ACTION_BASE}{operation}"
    to_el   = etree.SubElement(header, f"{{{_NS['wsa']}}}To")
    to_el.text  = MPS_SERVICE_URL
    sec     = etree.SubElement(header, f"{{{_NS['wsse']}}}Security")
    tok     = etree.SubElement(sec, f"{{{_NS['wsse']}}}UsernameToken")
    usr     = etree.SubElement(tok, f"{{{_NS['wsse']}}}Username")
    usr.text = MPS_USERNAME
    pwd     = etree.SubElement(tok, f"{{{_NS['wsse']}}}Password",
        attrib={"Type": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText"})
    pwd.text = MPS_PASSWORD

    # Body
    body    = etree.SubElement(envelope, f"{{{_NS['soapenv']}}}Body")
    op_el   = etree.SubElement(body, f"{{{_NS['api']}}}{operation}")
    request = etree.SubElement(op_el, f"{{{_NS['api']}}}request")

    def txt(tag_ns, tag_name, value):
        el = etree.SubElement(request, f"{{{tag_ns}}}{tag_name}")
        el.text = str(value)

    txt(m, "APIKey",     req.get("APIKey",    MPS_API_KEY))
    txt(m, "AccountID",  req.get("AccountID", MPS_ACCOUNT_ID))
    txt(m, "PageNumber", req.get("PageNumber", 1))
    txt(m, "PageSize",   req.get("PageSize",  DEFAULT_PAGE_SIZE))
    if req.get("SortDirection"):
        txt(m, "SortDirection", req["SortDirection"])
    if req.get("SortField"):
        txt(m, "SortField", req["SortField"])

    filters = req.get("_filters", [])
    if filters:
        filters_el = etree.SubElement(request, f"{{{m}}}Filters")
        for f in filters:
            ftype  = f["_type"]
            any_el = etree.SubElement(
                filters_el,
                f"{{{arr}}}anyType",
                attrib={f"{{{xsi}}}type": f"mps:{ftype}"},
            )
            col = etree.SubElement(any_el, f"{{{m}}}ColumnName")
            col.text = f["ColumnName"]

            if ftype == "DateRangeFilterParameter":
                end_el = etree.SubElement(any_el, f"{{{m}}}EndDate")
                end_el.text = f["EndDate"]
                start_el = etree.SubElement(any_el, f"{{{m}}}StartDate")
                start_el.text = f["StartDate"]

            elif ftype == "FilterParameter":
                cv_el = etree.SubElement(any_el, f"{{{m}}}ColumnValues")
                for v in f.get("ColumnValues", []):
                    s_el = etree.SubElement(cv_el, f"{{{arr}}}string")
                    s_el.text = v

    return etree.tostring(envelope, xml_declaration=True, encoding="utf-8")


# -- Parser de respuesta XML --------------------------------------------------
def _xml_to_dict(el: etree._Element):
    """
    Convierte un elemento lxml en dict/list/str Python.
    Un elemento sin hijos y sin texto devuelve None.
    Un elemento con un unico hijo repetido devuelve lista.
    """
    children = list(el)

    if not children:
        text = el.text
        if text and text.strip():
            return text.strip()
        return None

    result = {}
    for child in children:
        tag   = etree.QName(child.tag).localname
        value = _xml_to_dict(child)
        if tag in result:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(value)
        else:
            result[tag] = value
    return result


def _parse_response(resp_text: bytes, operation: str) -> dict:
    """
    Extrae el contenido del elemento *Result de la respuesta SOAP.
    Si el result esta vacio devuelve {"items": [], "total": 0} en lugar de null.
    """
    root = etree.fromstring(resp_text)

    result_tag   = f"{operation}Result"
    # Busca con namespace explicito primero
    result_els = root.findall(f".//{{{_NS['api']}}}{result_tag}")
    # Si no, busca por local-name (namespace cualquiera)
    if not result_els:
        result_els = root.findall(f".//*[local-name()='{result_tag}']")

    if not result_els:
        # Sin elemento Result -> devuelve raw del Body para diagnostico
        body = root.find(f"{{{_NS['soapenv']}}}Body")
        if body is None:
            body = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Body")
        return {
            "items": [],
            "total": 0,
            "_raw": etree.tostring(body, pretty_print=True).decode() if body is not None else "",
        }

    result_el = result_els[0]
    children  = list(result_el)

    # Elemento vacio (<Result/> o <Result></Result>) -> lista vacia
    if not children:
        return {"items": [], "total": 0}

    # Elemento con hijos -> convierte cada hijo a dict
    items = []
    for child in children:
        items.append(_xml_to_dict(child))

    return {"items": items, "total": len(items)}


# -- Dispatcher principal -----------------------------------------------------
def call_soap(operation: str, req: dict):
    if req.get("_filters"):
        return _call_raw(operation, req)
    return _call_zeep(operation, req)


def _call_zeep(operation: str, req: dict):
    clean = {k: v for k, v in req.items() if not k.startswith("_")}
    client = get_soap_client()
    result = getattr(client.service, operation)(request=clean)
    return serialize_object(result)


def _call_raw(operation: str, req: dict):
    xml_body = _make_envelope(operation, req)
    headers  = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction":   f'"{_SOAP_ACTION_BASE}{operation}"',
    }

    print(f"[DEBUG] XML enviado ({operation}):\n{xml_body.decode()}")

    resp = httpx.post(
        MPS_SERVICE_URL,
        content=xml_body,
        headers=headers,
        timeout=120,
        verify=True,
    )

    print(f"[DEBUG] HTTP {resp.status_code} | Respuesta:\n{resp.text[:3000]}")

    if resp.status_code != 200:
        try:
            root  = etree.fromstring(resp.content)
            fault = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Fault")
            msg   = fault.findtext("faultstring") if fault is not None else resp.text[:500]
        except Exception:
            msg = resp.text[:500]
        raise RuntimeError(f"SOAP Fault [{resp.status_code}]: {msg}")

    return _parse_response(resp.content, operation)
