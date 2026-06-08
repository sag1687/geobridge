# -*- coding: utf-8 -*-
"""HTTP client for the Verto Online JSON API."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request


DEFAULT_API_URL = "https://igmi.esercito.difesa.it/porta-magna/wps/volapi"

DEFAULT_SRS = [
    {"epsg": 4265, "descrizione": "Monte Mario"},
    {"epsg": 3003, "descrizione": "Monte Mario / Italy zone 1"},
    {"epsg": 3004, "descrizione": "Monte Mario / Italy zone 2"},
    {"epsg": 4806, "descrizione": "Monte Mario (Rome)"},
    {"epsg": 4230, "descrizione": "ED50"},
    {"epsg": 23032, "descrizione": "ED50 / UTM zone 32N"},
    {"epsg": 23033, "descrizione": "ED50 / UTM zone 33N"},
    {"epsg": 23034, "descrizione": "ED50 / UTM zone 34N"},
    {"epsg": 4670, "descrizione": "IGM95"},
    {"epsg": 3064, "descrizione": "IGM95 / UTM zone 32N"},
    {"epsg": 3065, "descrizione": "IGM95 / UTM zone 33N"},
    {"epsg": 9716, "descrizione": "IGM95 / UTM zone 34N"},
    {"epsg": 3035, "descrizione": "ETRS89 / ETRS-LAEA"},
    {"epsg": 3034, "descrizione": "ETRS89 / ETRS-LCC"},
    {"epsg": 6706, "descrizione": "RDN2008 2D geo"},
    {"epsg": 6707, "descrizione": "RDN2008 / TM32"},
    {"epsg": 6708, "descrizione": "RDN2008 / TM33"},
    {"epsg": 6709, "descrizione": "RDN2008 / TM34"},
    {"epsg": 7794, "descrizione": "RDN2008 / Italy Zone EN"},
    {"epsg": 6876, "descrizione": "RDN2008 / Zone 12"},
]


class VertoApiError(RuntimeError):
    """Raised when the remote Verto API reports or causes an error."""


def normalize_srs_list(values):
    normalized = []
    for item in values or []:
        try:
            epsg = int(item["epsg"])
        except (KeyError, TypeError, ValueError):
            continue
        normalized.append(
            {
                "epsg": epsg,
                "descrizione": str(item.get("descrizione", "EPSG:%s" % epsg)).strip(),
            }
        )
    return normalized


class VertoClient:
    """Minimal JSON client for Verto Online.

    The API currently requires ``utente`` and ``chiave`` in conversion calls,
    even though the public manual says they are ignored for now.
    """

    def __init__(self, api_url=DEFAULT_API_URL, timeout=30, user="qgis", key="qgis"):
        self.api_url = api_url
        self.timeout = timeout
        self.user = user or "qgis"
        self.key = key or "qgis"

    def info(self):
        data = self._post_json({"richiesta": "info"})
        srs = normalize_srs_list(data.get("srsSupportati"))
        return {
            "maxCoord": int(data.get("maxCoord") or 32000),
            "srsSupportati": srs or list(DEFAULT_SRS),
        }

    def convert(self, in_epsg, out_epsg, coordinates):
        payload = {
            "richiesta": "conversione",
            "utente": self.user,
            "chiave": self.key,
            "inEpsg": int(in_epsg),
            "outEpsg": int(out_epsg),
            "coordinate": [
                {"e": float(coord["e"]), "n": float(coord["n"])}
                for coord in coordinates
            ],
        }
        data = self._post_json(payload)
        if data.get("stato") != "successo":
            message = data.get("messaggio") or "Conversione Verto non riuscita"
            where = data.get("dove")
            if where:
                message = "%s: %s" % (where, message)
            raise VertoApiError(message)
        converted = data.get("coordinate")
        if not isinstance(converted, list):
            raise VertoApiError("Risposta API senza vettore 'coordinate'")
        if len(converted) != len(coordinates):
            raise VertoApiError(
                "Risposta API incoerente: %s coordinate ricevute, %s attese"
                % (len(converted), len(coordinates))
            )
        return [{"e": float(coord["e"]), "n": float(coord["n"])} for coord in converted]

    def convert_many(
        self, in_epsg, out_epsg, coordinates, max_per_request=32000, progress=None
    ):
        if max_per_request <= 0:
            max_per_request = 32000
        converted = []
        total = len(coordinates)
        for start in range(0, total, max_per_request):
            end = min(start + max_per_request, total)
            if progress:
                progress(
                    "Invio coordinate %s-%s di %s a Verto Online"
                    % (start + 1, end, total),
                    start,
                    total,
                )
            converted.extend(self.convert(in_epsg, out_epsg, coordinates[start:end]))
            if progress:
                progress(
                    "Ricevute coordinate %s-%s di %s" % (start + 1, end, total),
                    end,
                    total,
                )
        return converted

    def _post_json(self, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.api_url,
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "QGIS-VertoBridge-Italia/0.1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                text = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise VertoApiError(
                "Errore HTTP %s dal servizio Verto: %s" % (exc.code, detail)
            ) from exc
        except (urllib.error.URLError, socket.timeout) as exc:
            raise VertoApiError("Servizio Verto non raggiungibile: %s" % exc) from exc
        try:
            return json.loads(text)
        except ValueError as exc:
            raise VertoApiError("Risposta Verto non valida come JSON") from exc
