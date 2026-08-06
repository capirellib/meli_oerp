# -*- coding: utf-8 -*-
"""Pre-migration script for meli_oerp 19.0.26.51

EN: Deactivates ALL dynamic views created by solt_api_connector before
    meli_oerp's XML data files are loaded.

    BUG FIX: Previous versions used '\\_' in LIKE which PostgreSQL
    interprets as literal backslash + wildcard (without ESCAPE clause).
    Now uses plain '_' which is a single-char wildcard — perfectly fine
    since it still matches 'solt_api_connector' view names.

ES: Desactiva TODAS las vistas dinámicas creadas por solt_api_connector
    antes de que se carguen los archivos XML de meli_oerp.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info(
        "MELI pre-migrate 19.0.26.51: deactivating solt_api_connector "
        "dynamic views..."
    )

    # EN: Two naming patterns used by solt_api_connector:
    #   Form:   'solt_api_connector{id}.{model}.form.view'
    #   Search: '{model}.{id}.api.connector.search.view'
    #   List:   '{model}.{id}.api.connector.list.view'
    # NOTE: '_' in LIKE is a single-char wildcard — matches any character
    #       including literal underscore. No ESCAPE needed.
    # ES: Dos patrones de nombres usados por solt_api_connector.
    #     '_' en LIKE es un comodín de un carácter.
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
            _logger.warning(
                "MELI pre-migrate: deactivating view id=%s "
                "name='%s' model='%s' type='%s'",
                vid, vname, vmodel, vtype,
            )
        cr.execute(
            "UPDATE ir_ui_view SET active = false WHERE id IN %s",
            (tuple(view_ids),),
        )
        _logger.info(
            "MELI pre-migrate: deactivated %d view(s).", len(view_ids),
        )
    else:
        _logger.info("MELI pre-migrate: no dynamic views found.")
