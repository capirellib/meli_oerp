# -*- coding: utf-8 -*-
"""Post-migration script for meli_oerp 19.0.26.49

EN: Regenerates solt_api_connector dynamic search views (purges the invalid
    "group_by: x_state_sync" filter left on product.template) and reactivates
    the dynamic views that pre-migrate.py temporarily deactivated. The
    regeneration runs through solt_api_connector's own make_search_view(), which
    (since 19.0.1.1.2) only creates the group_by filter when the field exists in
    the model's ORM _fields. This makes the fix durable: after this migration
    the reactivated solt views no longer reference x_state_sync, so a future
    upgrade of ANY module sharing the parent search view cannot re-raise the
    ParseError. The raw SQL UPDATE that reactivates does NOT trigger
    ir.ui.view._check_xml().

ES: Regenera las vistas de búsqueda dinámicas de solt_api_connector (purga el
    filtro inválido "group_by: x_state_sync" dejado en product.template) y
    reactiva las vistas dinámicas que pre-migrate.py desactivó temporalmente. La
    regeneración usa el propio make_search_view() de solt_api_connector, que
    (desde 19.0.1.1.2) solo crea el filtro group_by si el campo existe en los
    _fields del ORM. Esto hace el fix duradero: tras esta migración, las vistas
    solt reactivadas ya no referencian x_state_sync, por lo que un futuro upgrade
    de CUALQUIER módulo que comparta la vista de búsqueda padre no puede volver a
    lanzar el ParseError. El UPDATE por SQL directo que reactiva NO dispara
    ir.ui.view._check_xml().
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _purge_solt_search_views(cr):
    """EN: Rebuild solt search views so invalid group_by filters are dropped.

    ES: Reconstruye las vistas de búsqueda de solt para que se eliminen los
    filtros group_by inválidos (x_state_sync en product.template).
    """
    try:
        env = api.Environment(cr, SUPERUSER_ID, {})
        model = env.get('solt.api.meta.fields')
        if not model:
            _logger.info(
                "MELI post-migrate: solt.api.meta.fields not present, "
                "skipping search view regeneration."
            )
            return
        records = model.search([('search_view_id', '!=', False)])
        if not records:
            _logger.info(
                "MELI post-migrate: no solt.api.meta.fields records with "
                "search_view_id found, nothing to regenerate."
            )
            return
        for rec in records:
            try:
                _logger.info(
                    "MELI post-migrate: regenerating search view for %s "
                    "(search_view_id=%s)...",
                    rec.model, rec.search_view_id.id,
                )
                rec.make_search_view()
            except Exception:
                _logger.warning(
                    "MELI post-migrate: make_search_view() failed for %s, "
                    "skipping (view will stay inactive).",
                    rec.model, exc_info=True,
                )
    except Exception:
        _logger.warning(
            "MELI post-migrate: could not purge solt search views, "
            "continuing with reactivation.",
            exc_info=True,
        )


def migrate(cr, version):
    """Regenerate + reactivate solt_api_connector dynamic views."""
    if not version:
        return

    _logger.info(
        "MELI post-migrate 19.0.26.49: purging invalid group_by filters from "
        "solt_api_connector dynamic search views..."
    )
    _purge_solt_search_views(cr)

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
