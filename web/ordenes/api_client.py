import requests
from django.conf import settings


class ApiError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def call(method, path, payload=None):
    url = settings.API_URL.rstrip("/") + path
    try:
        r = requests.request(method, url, json=payload, timeout=10)
    except requests.RequestException:
        raise ApiError("No se pudo conectar con la API. Intente de nuevo en unos segundos.")
    try:
        data = r.json()
    except ValueError:
        data = None
    if r.status_code >= 400:
        msg = (data or {}).get("error") if isinstance(data, dict) else None
        raise ApiError(msg or f"La API respondio con error {r.status_code}", r.status_code)
    return data
