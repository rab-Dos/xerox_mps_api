# Xerox MPS API Gateway – FastAPI

API REST que unifica el acceso a **dos APIs de Xerox**:

| API | Protocolo | Propósito |
|---|---|---|
| **MPS API** (MPSAPIV2) | SOAP / WS-Security | Activos, medidores, tickets, consumibles, envíos |
| **SA-API** (SupportAssistant V3) | REST / JSON Bearer | Incidencias, servicios por dispositivo, actualización de medidores |

---

## Inicio rápido

```bash
# 1. Instalar dependencias (con uv)
uv sync

# 2. (Opcional) Sobreescribir credenciales con variables de entorno
# Editar o crear .env con tus credenciales

# 3. Levantar el servidor
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. Documentación interactiva
open http://localhost:8000/docs
```

---

## Mapa de endpoints

### 🔐 `/auth` – Gestión de tokens SA-API
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/auth/token` | Crear token (AccessToken + RefreshToken) |
| GET  | `/auth/token` | Refrescar token |
| DELETE | `/auth/token` | Eliminar token activo |

> Los tokens se gestionan automáticamente en cada llamada a SA-API. Estos endpoints son opcionales para uso manual.

---

### 🖨️ `/assets` – Activos (equipos)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/assets/` | Todos los activos (paginado) |
| GET | `/assets/today` | Activos modificados hoy |
| GET | `/assets/range?start_date=&end_date=` | Activos modificados en intervalo |
| GET | `/assets/scope-changes?start_date=&end_date=` | Cambios de alcance contractual |
| GET | `/assets/in-scope-count` | Conteo de activos en contrato por grupo |
| GET | `/assets/{asset_id}` | Detalle completo de un activo |
| GET | `/assets/{asset_id}/locations` | Historial de ubicaciones |
| GET | `/assets/{asset_id}/change-history` | Historial de cambios (con fechas opcionales) |
| GET | `/assets/{asset_id}/price-plans` | Planes de precio asignados |

---

### 📊 `/meters` – Medidores de impresión
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/meters/raw` | Todas las lecturas raw paginadas |
| GET | `/meters/raw/today` | Lecturas raw del día de hoy |
| GET | `/meters/raw/range?start_date=&end_date=` | Lecturas raw en intervalo |
| GET | `/meters/raw/latest` | Última lectura por activo/medidor |
| GET | `/meters/raw/asset/{asset_id}` | Lecturas raw de un activo |
| GET | `/meters/raw/serial/{serial_number}` | Lecturas raw por número de serie |
| GET | `/meters/billable` | Lecturas facturables paginadas |
| GET | `/meters/billable/today` | Facturables del día |
| GET | `/meters/billable/range?start_date=&end_date=` | Facturables en intervalo |
| GET | `/meters/billable/asset/{asset_id}` | Facturables de un activo |
| GET | `/meters/billable/asset-count` | Conteo de activos facturables |

**Nombres de medidores comunes:**
`Total Impressions`, `Color Impressions`, `Black Impressions`, `Color Printed Impressions`, `Black Printed Impressions`, `Embedded Fax Images Sent`, etc.

---

### 🎫 `/tickets` – Tickets de servicio
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/tickets/` | Todos los tickets |
| GET | `/tickets/today` | Tickets abiertos hoy |
| GET | `/tickets/range?start_date=&end_date=` | Por fecha de apertura |
| GET | `/tickets/closed/range?start_date=&end_date=` | Por fecha de cierre |
| GET | `/tickets/modified/range?start_date=&end_date=` | Por fecha de modificación |
| GET | `/tickets/activity/range?start_date=&end_date=` | Por última actividad |
| GET | `/tickets/asset/{asset_id}` | Tickets de un activo (con fechas opcionales) |
| GET | `/tickets/{ticket_id}` | Detalle de ticket |
| GET | `/tickets/{ticket_id}/activities` | Historial de actividades |
| GET | `/tickets/{ticket_id}/assignments` | Asignaciones de técnicos |

---

### 🖨️ `/consumables` – Consumibles (tóner, tambores…)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/consumables/` | Estado de consumibles de toda la flota |
| GET | `/consumables/asset/{asset_id}` | Consumibles de un activo específico |
| GET | `/consumables/low?threshold=20` | Activos con nivel bajo (≤ umbral %) |
| GET | `/consumables/ohb?asset_id=` | Inventario On-Hand Buffer |
| GET | `/consumables/orders` | Órdenes de suministro (con fechas opcionales) |
| GET | `/consumables/orders/{order_id}` | Detalle de orden |
| GET | `/consumables/catalog` | Catálogo de suministros |

---

### 📦 `/shipments` – Envíos de suministros
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/shipments/` | Todos los envíos |
| GET | `/shipments/today` | Envíos despachados hoy |
| GET | `/shipments/range?start_date=&end_date=` | Por fecha de despacho |
| GET | `/shipments/received/range?start_date=&end_date=` | Por fecha de recepción |
| GET | `/shipments/modified/range?start_date=&end_date=` | Por fecha de modificación |
| GET | `/shipments/{shipment_id}` | Detalle de envío |
| GET | `/shipments/carriers/list` | Catálogo de transportistas |

---

### ⚙️ `/services` – Servicios contratados
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/services/` | Catálogo de servicios MPS |
| GET | `/services/statuses` | Estados de servicio disponibles |
| GET | `/services/exit-statuses` | Estados de cierre |
| GET | `/services/late-reasons` | Razones de atraso |
| GET | `/services/entitlements/{serial}/{mac}` | Servicios SA-API del dispositivo |

---

### 🚨 `/incidents` – Incidencias SA-API (por dispositivo)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/incidents/{serial}/{mac}?start_date=&end_date=` | Incidencias en intervalo (máx 90 días) |
| GET | `/incidents/{serial}/{mac}/today` | Incidencias del día |
| GET | `/incidents/{serial}/{mac}/last-week` | Últimos 7 días |
| GET | `/incidents/{serial}/{mac}/last-month` | Últimos 30 días |
| GET | `/incidents/{serial}/{mac}/open` | Solo abiertas (últimos 90 días) |
| POST | `/incidents/{serial}/{mac}` | Crear nueva incidencia |
| POST | `/incidents/{serial}/{mac}/meters` | Enviar lecturas de medidores |

#### Parámetros de filtro para incidencias
- `incident_type`: `Breakfix` | `Supply` | `Both`
- `status`: `Open` | `Closed` | `Both`
- `sandbox`: `true` para entorno de pruebas

---

## Estructura del proyecto

```
xerox_mps_api/
├── main.py            # App FastAPI + routers
├── config.py          # Credenciales y URLs
├── soap_client.py     # Cliente SOAP (Zeep) + helpers de filtros
├── sa_client.py       # Cliente SA-API REST con gestión de tokens
├── requirements.txt
├── README.md
└── routers/
    ├── auth.py        # Tokens SA-API
    ├── assets.py      # Activos MPS
    ├── meters.py      # Medidores raw y facturables
    ├── tickets.py     # Tickets de servicio
    ├── consumables.py # Consumibles y órdenes
    ├── shipments.py   # Envíos
    ├── services.py    # Servicios SOAP + SA-API
    └── incidents.py   # Incidencias SA-API + envío de medidores
```

---

## Notas importantes

- **Gestor de paquetes**: Este proyecto usa [uv](https://github.com/astral-sh/uv) para gestión rápida de dependencias y entorno Python. Ejecuta `uv sync` para instalar todas las dependencias definidas en `pyproject.toml`.
- **Paginación**: todos los endpoints soportan `page` y `page_size` (máx 1000 por página).
- **Fechas**: formato `YYYY-MM-DD`; la SA-API usa UTC.
- **Rango SA-API**: máximo 90 días por consulta en `/incidents`.
- **Tokens automáticos**: el `SAAPIClient` renueva automáticamente el AccessToken (vigencia 180 s).
- **SOAP**: los filtros de fecha usan `DateRangeFilterParameter` con `xs:dateTime`.
