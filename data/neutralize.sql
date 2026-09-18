-- afip_webservice_monitor: ejecutado por `odoo neutralize` (staging/test).
-- En una base neutralizada no se monitorea AFIP: se apaga el cron y el banner.
-- El codigo ademas chequea `database.is_neutralized` en runtime, asi que esto
-- es solo un refuerzo (evita el trafico del cron contra AFIP desde staging).
UPDATE ir_cron
   SET active = false
 WHERE id IN (SELECT res_id FROM ir_model_data
               WHERE module = 'afip_webservice_monitor' AND model = 'ir.cron');

UPDATE ir_config_parameter
   SET value = 'False'
 WHERE key = 'afip_webservice_monitor.show_banner';
