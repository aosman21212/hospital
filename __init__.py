from . import models
import base64
import os


def _refresh_menu_icon(env):
    """Force-refresh the cached web_icon_data for the Hospital root menu
    so the new logo.png is shown in Odoo's app-switcher after install/upgrade."""
    icon_path = os.path.join(
        os.path.dirname(__file__),
        'static', 'description', 'icon.png',
    )
    if not os.path.exists(icon_path):
        return
    with open(icon_path, 'rb') as f:
        icon_b64 = base64.b64encode(f.read()).decode()

    menu = env['ir.ui.menu'].search(
        [('name', '=', 'Hospital'), ('parent_id', '=', False)],
        limit=1,
    )
    if menu:
        menu.write({'web_icon_data': icon_b64})
