# -*- coding: utf-8 -*-
"""Reutilización del chequeo reciente antes de publicar (necesita Odoo)."""
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase

from ..lib import fedummy

STATUS = "odoo.addons.afip_webservice_monitor.models.afip_service_status"


class TestPostCheckTtl(TransactionCase):

    def setUp(self):
        super().setUp()
        self.service = self.env["afip.service.status"].create({
            "name": "Test WSFE",
            "service_type": "wsfe",
            "environment": "testing",
            "url": "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL",
            "is_available": True,
            "check_date": fields.Datetime.now(),
        })

    def test_chequeo_reciente_y_disponible_se_reutiliza(self):
        self.assertTrue(self.service._is_recent_ok(60))

    def test_chequeo_viejo_no_se_reutiliza(self):
        self.service.check_date = fields.Datetime.now() - timedelta(seconds=120)
        self.assertFalse(self.service._is_recent_ok(60))

    def test_resultado_caido_nunca_se_reutiliza(self):
        self.service.is_available = False
        self.assertFalse(self.service._is_recent_ok(60))

    def test_ttl_cero_desactiva_la_reutilizacion(self):
        self.assertFalse(self.service._is_recent_ok(0))

    def test_sin_fecha_de_chequeo(self):
        self.service.check_date = False
        self.assertFalse(self.service._is_recent_ok(60))

    def test_wsfe_usa_fedummy_directo_y_no_zeep(self):
        ok = (200, b"<AppServer>OK</AppServer><DbServer>OK</DbServer><AuthServer>OK</AuthServer>")
        with patch.object(fedummy, "call", return_value=ok) as call, \
                patch(STATUS + ".AfipServiceStatus._check_service_with_zeep") as zeep_check:
            result = self.service.check_service_status()
        self.assertTrue(result["available"])
        self.assertTrue(self.service.is_available)
        call.assert_called_once()
        zeep_check.assert_not_called()

    def test_respuesta_no_interpretable_cae_a_zeep(self):
        caido = {"available": False, "status_code": 0, "response_time": 0, "error": "x"}
        with patch.object(fedummy, "call", return_value=(200, b"<html>mantenimiento</html>")), \
                patch(STATUS + ".AfipServiceStatus._check_service_with_zeep",
                      return_value=caido) as zeep_check:
            result = self.service.check_service_status()
        zeep_check.assert_called_once()
        self.assertFalse(result["available"])
