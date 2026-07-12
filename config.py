"""
Configuración centralizada – credenciales y URLs.
En producción, carga estos valores desde variables de entorno o un vault.
"""
import os
import configparser

# ── Credenciales MPS SOAP API ──────────────────────────────────────────────────
ruta = 'config/access.ini'
config = configparser.ConfigParser()
config.read(ruta)
    
MPS_USERNAME   = os.getenv("MPS_USERNAME",  config.get("XEROX", "mps_username"))
MPS_PASSWORD   = os.getenv("MPS_PASSWORD",  config.get("XEROX", "mps_password"))
MPS_API_KEY    = os.getenv("MPS_API_KEY",   config.get("XEROX", "mps_api_key"))
MPS_ACCOUNT_ID = os.getenv("MPS_ACCOUNT_ID",config.get("XEROX", "mps_account_id"))

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
SA_API_KEY    = os.getenv("SA_API_KEY", config.get("XEROX", "sa_api_key"))
SA_API_BASE   = os.getenv(
    "SA_API_BASE",
    "https://eipsupportassistant.services.xerox.com/SupportAssistant/API/V3"
)

# ── Paginación por defecto ─────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 500
