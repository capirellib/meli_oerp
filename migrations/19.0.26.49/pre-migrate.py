# -*- coding: utf-8 -*-
"""Pre-migration script for meli_oerp 19.0.26.49

EN: Deactivates ALL dynamic views created by solt_api_connector (name pattern
    'api.connector') BEFORE meli_oerp's XML data files are loaded. solt_api_connector
    creates dynamic inherited views (form, search, list) on multiple models
    (product.template, sale.order, res.partner, etc.) that reference custom x_
    fields (x_state_sync, x_external_id, x_store_external_id, x_date_last_sync,
    x_exclud_from_sync). When those fields are missing from the model's ORM
    _fields, Odoo 19's strict validator rejects them while re-validating the
    composed view shared with meli_oerp, raising:
        ParseError: Unknown field "x_state_sync" in "group_by".
    This script deactivates (not deletes) those views so that meli_oerp's XML
    can be loaded without ParseError. The views are reactivated by the
    post-migrate.py script.

ES: Desactiva TODAS las vistas dinámicas creadas por solt_api_connector (patrón
    de nombre 'api.connector') ANTES de que se carguen los archivos XML de
    meli_oerp. solt_api_connector crea vistas heredadas dinámicas (form, search,
    list) en múltiples modelos (product.template, sale.order, res.partner, etc.)
    que referencian campos personalizados x_ (x_state_sync, x_external_id, etc.).
    Cuando esos campos faltan en los _fields del ORM, el validador estricto de
    Odoo 19 los rechaza al re-validar la vista compuesta compartida con
    meli_oerp, lanzando:
        ParseError: Campo desconocido "x_state_sync" en "group_by".
    Este script desactiva (no elimina) esas vistas para que el XML de meli_oerp
    pueda cargarse sin ParseError. post-migrate.py las reactiva después.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Deactivate ALL solt_api_connector dynamic views before XML loading.

    EN: Targets views by name pattern 'api.connector', the naming convention used
        by solt_api_connector's make_views().
    ES: Apunta a vistas por patrón de nombre 'api.connector', la convención de
        nombres usada por make_views() de solt_api_connector.
    """
    if not version:
        return

    _logger.info(
        "MELI pre-migrate 19.0.26.49: checking for solt_api_connector "
        "dynamic views that could block upgrade..."
    )

    cr.execute("""
        SELECT v.id, v.name, v.model, v.type
        FROM ir_ui_view v
        WHERE v.active = true
          AND v.name LIKE '%%api.connector%%'
    """)
    conflicting_views = cr.fetchall()

    if conflicting_views:
        for vid, vname, vmodel, vtype in conflicting_views:
            _logger.warning(
                "MELI pre-migrate: deactivating dynamic view id=%s "
                "name='%s' model='%s' type='%s'",
                vid, vname, vmodel, vtype,
            )
        cr.execute(
            "UPDATE ir_ui_view SET active = false WHERE id IN %s",
            (tuple(row[0] for row in conflicting_views),),
        )
        _logger.info(
            "MELI pre-migrate: deactivated %d dynamic view(s). "
            "Upgrade can proceed safely. Reactivated by post-migrate 19.0.26.49.",
            len(conflicting_views),
        )
    else:
        _logger.info(
            "MELI pre-migrate: no conflicting dynamic views found. "
            "Proceeding normally."
        )
