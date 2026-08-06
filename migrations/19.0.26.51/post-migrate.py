# -*- coding: utf-8 -*-
"""Post-migration script for meli_oerp 19.0.26.51

EN: Reactivates solt_api_connector dynamic views after successful XML loading.
ES: Reactiva vistas dinámicas de solt_api_connector después de carga XML exitosa.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info(
        "MELI post-migrate 19.0.26.51: reactivating solt_api_connector "
        "dynamic views..."
    )

    cr.execute("""
        SELECT v.id, v.name, v.model, v.type
        FROM ir_ui_view v
        WHERE v.active = false
          AND (
              v.name LIKE '%%solt_api_connector%%'
              OR v.name LIKE '%%api.connector%%'
          )
    """)
    views = cr.fetchall()

    if views:
        view_ids = [row[0] for row in views]
        for vid, vname, vmodel, vtype in views:
            _logger.info(
                "MELI post-migrate: reactivating view id=%s "
                "name='%s' model='%s' type='%s'",
                vid, vname, vmodel, vtype,
            )
        cr.execute(
            "UPDATE ir_ui_view SET active = true WHERE id IN %s",
            (tuple(view_ids),),
        )
        _logger.info(
            "MELI post-migrate: reactivated %d view(s).", len(view_ids),
        )
    else:
        _logger.info("MELI post-migrate: no views to reactivate.")
