"""
Cliente HTTP para la SA-API REST de Xerox.
Maneja la autenticación con tokens y su renovación automática.
"""
import httpx
from datetime import datetime, timedelta
from config import SA_API_KEY, SA_API_BASE


class SAAPIClient:
    """Cliente SA-API con gestión automática de tokens."""

    _access_token: str | None = None
    _refresh_token: str | None = None
    _token_expires_at: datetime = datetime.min

    # ── Token management ───────────────────────────────────────────────────────

    def create_token(self) -> dict:
        """POST /Token  →  obtiene un nuevo par Access/Refresh token."""
        resp = httpx.post(
            f"{SA_API_BASE}/Token",
            json={"ValidateKey": SA_API_KEY},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._store_tokens(data)
        return data

    def refresh_token(self) -> dict:
        """GET /Token?ValidateKey={RefreshToken}  →  renueva tokens."""
        resp = httpx.get(
            f"{SA_API_BASE}/Token",
            params={"ValidateKey": self._refresh_token},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._store_tokens(data)
        return data

    def delete_token(self) -> bool:
        """DELETE /Token  →  invalida el token actual."""
        if not self._access_token:
            return False
        resp = httpx.delete(
            f"{SA_API_BASE}/Token",
            params={"ValidateKey": self._access_token},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )
        self._access_token = None
        self._refresh_token = None
        return resp.status_code == 204

    def _store_tokens(self, data: dict):
        self._access_token = data.get("AccessToken")
        self._refresh_token = data.get("RefreshToken")
        timeout_secs = data.get("AccessTimeout", 180)
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=timeout_secs - 10)

    def _ensure_token(self):
        if not self._access_token or datetime.utcnow() >= self._token_expires_at:
            if self._refresh_token:
                try:
                    self.refresh_token()
                    return
                except Exception:
                    pass
            self.create_token()

    # ── Generic request ────────────────────────────────────────────────────────

    def _headers(self, serial: str, mac: str) -> dict:
        self._ensure_token()
        return {
            "Content-Type":        "application/json",
            "Accept":              "application/json",
            "AccessToken":         self._access_token,
            "DeviceSerialNumber":  serial,
            "DeviceMACAddress":    mac,
        }

    # ── SA-API endpoints ───────────────────────────────────────────────────────

    def get_services(self, serial: str, mac: str) -> dict:
        """GET /Services  →  servicios asociados al dispositivo."""
        resp = httpx.get(
            f"{SA_API_BASE}/Services",
            headers=self._headers(serial, mac),
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()

    def get_incidents(
        self,
        serial: str,
        mac: str,
        start_date: str,
        end_date: str,
        incident_type: str = "Both",
        status: str = "Both",
        sandbox: bool = False,
    ) -> dict:
        """GET /Incidents  →  incidencias Break-Fix y Supplies en el rango dado."""
        base = f"{SA_API_BASE}/Sandbox" if sandbox else SA_API_BASE
        resp = httpx.get(
            f"{base}/Incidents",
            headers=self._headers(serial, mac),
            params={
                "StartDate": start_date,
                "EndDate":   end_date,
                "Type":      incident_type,
                "Status":    status,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()

    def create_incident(
        self,
        serial: str,
        mac: str,
        service_id: str,
        summary: str,
        requester_name: str,
        requester_phone: str,
        requester_email: str,
        sandbox: bool = False,
    ) -> dict:
        """POST /Incident  →  abre una nueva incidencia."""
        base = f"{SA_API_BASE}/Sandbox" if sandbox else SA_API_BASE
        resp = httpx.post(
            f"{base}/Incident",
            headers=self._headers(serial, mac),
            json={
                "IncidentSummary": summary,
                "ServiceID":       service_id,
                "RequesterName":   requester_name,
                "RequesterPhone":  requester_phone,
                "RequesterEmail":  requester_email,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()

    def update_meters(
        self,
        serial: str,
        mac: str,
        meters: list,
        meter_read_date: str | None = None,
        sandbox: bool = False,
    ) -> bool:
        """POST /Meters  →  actualiza lecturas de medidores para el dispositivo."""
        base = f"{SA_API_BASE}/Sandbox" if sandbox else SA_API_BASE
        payload = {"Meters": meters}
        if meter_read_date:
            payload["MeterReadDate"] = meter_read_date
        resp = httpx.post(
            f"{base}/Meters",
            headers=self._headers(serial, mac),
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.status_code == 204


# Instancia singleton reutilizable
sa_client = SAAPIClient()
