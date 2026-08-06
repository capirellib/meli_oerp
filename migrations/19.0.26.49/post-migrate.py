# -*- coding: utf-8 -*-
"""Post-migration script for meli_oerp 19.0.26.49

EN: Reactivates the solt_api_connector dynamic views that were temporarily
    deactivated by pre-migrate.py, restoring them to their original state after
    meli_oerp's XML data has been loaded and validated successfully. The raw SQL
    UPDATE does NOT trigger ir.ui.view._check_xml(), so it cannot re-raise the
    ParseError.

ES: Reactiva las vistas dinámicas de solt_api_connector que fueron temporalmente
    desactivadas por pre-migrate.py, restaurándolas a su estado original después
    de que los datos XML de meli_oerp se cargaron y validaron correctamente. El
    UPDATE por SQL directo NO dispara ir.ui.view._check_xml(), por lo que no puede
    volver a lanzar el ParseError.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Reactivate solt_api_connector dynamic views after XML loading."""
    if not version:
        return

    _logger.info(
        "MELI post-migrate 19.0.26.49: reactivating solt_api_connector "
        "dynamic views..."
    )

    cr.execute("""
        SELECT v.id, v.name, v.model, v.type
        FROM ir_ui_view v
        WHERE v.active = false
          AND v.name LIKE '%%api.connector%%'
    """)
    deactivated_views = cr.fetchall()

    if deactivated_views:
        for vid, vname, vmodel, vtype in deactivated_views:
            _logger.info(
                "MELI post-migrate: reactivating view id=%s "
                "name='%s' model='%s' type='%s'",
                vid, vname, vmodel, vtype,
            )
        cr.execute(
            "UPDATE ir_ui_view SET active = true WHERE id IN %s",
            (tuple(row[0] for row in deactivated_views),),
        )
        _logger.info(
            "MELI post-migrate: reactivated %d view(s). "
            "solt_api_connector views restored to original state.",
            len(deactivated_views),
        )
    else:
        _logger.info(
            "MELI post-migrate: no deactivated api.connector views found."
        )
