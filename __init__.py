# -*- coding: utf-8 -*-
##############################################################################
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)



def pre_init_hook(cr):
    """Pre-init hook — deactivate orphaned dynamic views before XML loading.

    EN: Other modules (e.g. solt_api_connector) create dynamic inherited views
        at runtime that inject filters with group_by referencing custom fields
        like x_state_sync into the product.template search view. When those
        modules are partially uninstalled or the custom field is removed, the
        orphaned view stays in the database. Since meli_oerp also inherits from
        the same parent view, Odoo re-validates the entire composed view tree
        during upgrade and crashes with ParseError on the missing field.

        This hook deactivates (not deletes) those orphaned views BEFORE
        meli_oerp's XML data is loaded, preventing the validation crash.
        The owning module can reactivate them if reinstalled.

    ES: Otros módulos (ej: solt_api_connector) crean vistas heredadas dinámicas
        en tiempo de ejecución que inyectan filtros con group_by referenciando
        campos personalizados como x_state_sync en la vista de búsqueda de
        product.template. Cuando esos módulos se desinstalan parcialmente o el
        campo personalizado se elimina, la vista huérfana permanece en la BD.
        Como meli_oerp también hereda de la misma vista padre, Odoo re-valida
        todo el árbol de vistas compuestas durante la actualización y falla con
        ParseError por el campo faltante.

        Este hook desactiva (no elimina) esas vistas huérfanas ANTES de que se
        carguen los datos XML de meli_oerp, previniendo el crash de validación.
        El módulo propietario puede reactivarlas si se reinstala.
    """
    _logger.info(
        "MELI pre_init_hook: checking for orphaned dynamic views "
        "that could block upgrade..."
    )

    # --- Find dynamic search views from solt_api_connector referencing x_state_sync ---
    # --- Buscar vistas de búsqueda dinámicas de solt_api_connector que referencien x_state_sync ---
    # EN: We deactivate views by name pattern ('api.connector') rather than
    #     checking if the field exists in ir_model_fields, because Odoo 19's
    #     strict view validator may reject the field even when it exists in the
    #     DB (registry timing issue during module graph loading).
    # ES: Desactivamos vistas por patrón de nombre ('api.connector') en lugar de
    #     verificar si el campo existe en ir_model_fields, porque el validador
    #     estricto de vistas de Odoo 19 puede rechazar el campo incluso cuando
    #     existe en la BD (problema de timing del registro durante la carga).
    cr.execute("""
        SELECT v.id, v.name, v.model
        FROM ir_ui_view v
        WHERE v.active = true
          AND v.arch_db::text LIKE '%%x_state_sync%%'
          AND v.type = 'search'
          AND v.name LIKE '%%api.connector%%'
    """)
    orphaned_views = cr.fetchall()

    if orphaned_views:
        view_ids = [row[0] for row in orphaned_views]
        for vid, vname, vmodel in orphaned_views:
            _logger.warning(
                "MELI pre_init_hook: deactivating orphaned view id=%s "
                "name='%s' model='%s' (references x_state_sync but field "
                "does not exist on the model)",
                vid, vname, vmodel,
            )
        cr.execute(
            "UPDATE ir_ui_view SET active = false WHERE id IN %s",
            (tuple(view_ids),),
        )
        _logger.info(
            "MELI pre_init_hook: deactivated %d orphaned view(s). "
            "Upgrade can proceed safely.",
            len(view_ids),
        )
    else:
        _logger.info(
            "MELI pre_init_hook: no orphaned dynamic views found. "
            "Proceeding normally."
        )


def post_init_hook(env_or_cr, registry=None):
    """
    Increase 'Product Price' decimal precision to 6 digits.
    This allows storing prices with higher precision to avoid rounding
    errors when calculating inverse taxes (e.g., 21% IVA).

    Compatible with:
    - Odoo 14-16: receives (cr, registry)
    - Odoo 17-19: receives (env) directly
    """
    # Check if we received env directly (Odoo 17+) or cr (Odoo 14-16)
    if hasattr(env_or_cr, 'cr'):
        # Odoo 17+: first argument is already the Environment
        env = env_or_cr
    else:
        # Odoo 14-16: first argument is cursor, need to create Environment
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})

    # Find and update existing 'Product Price' precision
    precision = env['decimal.precision'].search([('name', '=', 'Product Price')], limit=1)
    if precision:
        if precision.digits < 6:
            _logger.info("MELI: Updating 'Product Price' decimal precision from %d to 6 digits", precision.digits)
            precision.write({'digits': 6})
    else:
        _logger.info("MELI: Creating 'Product Price' decimal precision with 6 digits")
        env['decimal.precision'].create({
            'name': 'Product Price',
            'digits': 6
        })


from . import models
from . import controllers
from . import wizard
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
