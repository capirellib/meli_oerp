# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

def migrate(cr, version):
    if not version:
        return
    _logger.info("MELI pre-migrate 19.0.26.49: deactivating dynamic views...")
    cr.execute("""
        SELECT v.id, v.name, v.model, v.type
        FROM ir_ui_view v
        WHERE v.active = true
          AND (
              v.name LIKE '%%solt_api_connector%%'
              OR v.name LIKE '%%api.connector%%'
          )
    """)
    views = cr.fetchall()
    if views:
        view_ids = [row[0] for row in views]
        for vid, vname, vmodel, vtype in views:
            _logger.warning("MELI pre-migrate: deactivating id=%s name='%s'", vid, vname)
        cr.execute("UPDATE ir_ui_view SET active = false WHERE id IN %s", (tuple(view_ids),))
        _logger.info("MELI pre-migrate: deactivated %d view(s).", len(view_ids))
