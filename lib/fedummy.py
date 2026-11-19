# -*- coding: utf-8 -*-
"""FEDummy de WSFEv1 sin zeep.

El chequeo de disponibilidad armaba un `zeep.Client` nuevo en cada llamada, y
zeep baja el WSDL (77 KB) cada vez que se construye: dos conexiones TLS por
chequeo. FEDummy no lleva autenticación ni parámetros, así que alcanza con
mandar el sobre SOAP fijo: una sola conexión y nada que cachear.

Sin imports de Odoo, para poder testear sin server.
"""
import re

SOAP_ACTION = "http://ar.gov.afip.dif.FEV1/FEDummy"

ENVELOPE = (
    b'<?xml version="1.0" encoding="utf-8"?>'
    b'<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
    b'<soap:Body><FEDummy xmlns="http://ar.gov.afip.dif.FEV1/"/></soap:Body>'
    b'</soap:Envelope>'
)

HEADERS = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPAction": '"%s"' % SOAP_ACTION,
}

_SERVERS = (b"AppServer", b"DbServer", b"AuthServer")


def endpoint_from_wsdl_url(url):
    """Saca el `?WSDL` de la URL configurada: el POST va al endpoint pelado."""
    return (url or "").split("?", 1)[0]


def parse_response(content):
    """Devuelve (app, db, auth) de una respuesta de FEDummy.

    Devuelve None si `content` no es una respuesta de FEDummy (por ejemplo una
    página de mantenimiento con HTTP 200): el llamador decide qué hacer.
    """
    if not content:
        return None
    if isinstance(content, str):
        content = content.encode("utf-8", "replace")
    values = []
    for tag in _SERVERS:
        m = re.search(rb"<(?:\w+:)?" + tag + rb">\s*([^<]*?)\s*</(?:\w+:)?" + tag + rb">", content)
        if not m:
            return None
        values.append(m.group(1).decode("ascii", "replace"))
    return tuple(values)


def is_ok(servers):
    """True si los tres servidores informan OK."""
    return bool(servers) and all(s == "OK" for s in servers)


def call(session, url, timeout):
    """POST de FEDummy. Devuelve (status_code, content). Propaga errores de red."""
    response = session.post(
        endpoint_from_wsdl_url(url), data=ENVELOPE, headers=HEADERS, timeout=timeout,
    )
    return response.status_code, response.content
