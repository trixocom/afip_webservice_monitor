# -*- coding: utf-8 -*-
"""Tests de `lib/fedummy.py` — sin red y sin Odoo."""
import unittest
from unittest import mock

from ..lib import fedummy

OK = (
    b'<?xml version="1.0" encoding="utf-8"?><soap:Envelope '
    b'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>'
    b'<FEDummyResponse xmlns="http://ar.gov.afip.dif.FEV1/"><FEDummyResult>'
    b'<AppServer>OK</AppServer><DbServer>OK</DbServer><AuthServer>OK</AuthServer>'
    b'</FEDummyResult></FEDummyResponse></soap:Body></soap:Envelope>'
)


class TestFedummy(unittest.TestCase):

    def test_respuesta_ok(self):
        servers = fedummy.parse_response(OK)
        self.assertEqual(servers, ("OK", "OK", "OK"))
        self.assertTrue(fedummy.is_ok(servers))

    def test_un_servidor_caido(self):
        servers = fedummy.parse_response(OK.replace(b"<DbServer>OK", b"<DbServer>NO"))
        self.assertEqual(servers, ("OK", "NO", "OK"))
        self.assertFalse(fedummy.is_ok(servers))

    def test_pagina_de_mantenimiento_no_es_fedummy(self):
        self.assertIsNone(fedummy.parse_response(b"<html><body>Mantenimiento</body></html>"))
        self.assertIsNone(fedummy.parse_response(b""))
        self.assertIsNone(fedummy.parse_response(None))
        self.assertFalse(fedummy.is_ok(None))

    def test_respuesta_como_texto_y_con_prefijo(self):
        texto = OK.decode("utf-8").replace("<AppServer>", "<a:AppServer>").replace(
            "</AppServer>", "</a:AppServer>")
        self.assertEqual(fedummy.parse_response(texto), ("OK", "OK", "OK"))

    def test_endpoint_sin_wsdl(self):
        self.assertEqual(
            fedummy.endpoint_from_wsdl_url("https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL"),
            "https://servicios1.afip.gov.ar/wsfev1/service.asmx",
        )
        self.assertEqual(fedummy.endpoint_from_wsdl_url("https://x/y.asmx"), "https://x/y.asmx")

    def test_call_manda_un_solo_post_al_endpoint(self):
        session = mock.Mock()
        session.post.return_value = mock.Mock(status_code=200, content=OK)
        status, content = fedummy.call(session, "https://x/wsfev1/service.asmx?WSDL", 7)
        self.assertEqual((status, content), (200, OK))
        session.post.assert_called_once()
        args, kwargs = session.post.call_args
        self.assertEqual(args[0], "https://x/wsfev1/service.asmx")
        self.assertEqual(kwargs["timeout"], 7)
        self.assertIn("FEDummy", kwargs["headers"]["SOAPAction"])
        self.assertIn(b"<FEDummy ", kwargs["data"])
        session.get.assert_not_called()
