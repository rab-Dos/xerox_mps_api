"""
Configuración centralizada – credenciales y URLs.
En producción, carga estos valores desde variables de entorno o un vault.
"""
import os

# ── Credenciales MPS SOAP API ──────────────────────────────────────────────────
MPS_USERNAME   = os.getenv("MPS_USERNAME",  "")
MPS_PASSWORD   = os.getenv("MPS_PASSWORD",  "")
MPS_API_KEY    = os.getenv("MPS_API_KEY",   "")
MPS_ACCOUNT_ID = os.getenv("MPS_ACCOUNT_ID","")

# ── URLs MPS SOAP ──────────────────────────────────────────────────────────────
MPS_WSDL_URL = os.getenv(
    "MPS_WSDL_URL",
    "https://office.services.xerox.com/MPSAPIV2/Services/Service.svc?singleWsdl"
)
MPS_SERVICE_URL = os.getenv(
    "MPS_SERVICE_URL",
    "https://office.services.xerox.com/MPSAPIV2/Services/Service.svc"
)

# ── Credenciales SA-API (REST) ─────────────────────────────────────────────────
SA_API_KEY    = os.getenv("SA_API_KEY",    "b010af12-2df5-4af6-8c2d-2eae38d5019e")
SA_API_BASE   = os.getenv(
    "SA_API_BASE",
    "https://eipsupportassistant.services.xerox.com/SupportAssistant/API/V3"
)

# ── Paginación por defecto ─────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 500
