"""
Xerox MPS Support Assistant – FastAPI Gateway
Wraps both the SOAP MPS API and the REST SA-API in clean REST endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
from routers import assets, meters, tickets, consumables, shipments, services, incidents, auth

app = FastAPI(
    title="Xerox MPS API Gateway",
    description=(
        "API Gateway para Xerox Managed Print Services. "
        "Expone los datos de activos, lecturas de medidores, tickets, consumibles, "
        "envíos, servicios e incidencias a través de endpoints REST con filtros por "
        "fecha, intervalo y dispositivo."
    ),
    version="1.0.0",
    contact={
        "name": "MCI BI & Development Team",
        "email": "hexagon@codiceintegral.com",
        "url": "https://codiceintegral.com"
    },
    docs_url=None,
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router,        prefix="/auth",        tags=["Autenticación SA-API"])
app.include_router(assets.router,      prefix="/assets",      tags=["Activos (Assets)"])
app.include_router(meters.router,      prefix="/meters",      tags=["Medidores (Meters)"])
app.include_router(tickets.router,     prefix="/tickets",     tags=["Tickets de Servicio"])
app.include_router(consumables.router, prefix="/consumables", tags=["Consumibles"])
app.include_router(shipments.router,   prefix="/shipments",   tags=["Envíos (Shipments)"])
app.include_router(services.router,    prefix="/services",    tags=["Servicios"])
app.include_router(incidents.router,   prefix="/incidents",   tags=["Incidencias SA-API"])

# ── Documentación con Scalar ──────────────────────────────────────────────────
@app.get("/docs", include_in_schema=False)
async def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url, # Usa el openapi.json generado por FastAPI
        title=app.title,             # Toma el título "Xerox MPS API Gateway"
    )

@app.get("/", tags=["Health"])
def health():
    return {
        "status": "ok",
        "description": "Xerox MPS API Gateway activo",
        "docs": "/docs",
    }