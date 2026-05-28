mport json
import frappe

def move_app_last(app="frappe_zh_cn_pack"):
    apps = frappe.get_installed_apps()
    if app in apps:
        apps = [a for a in apps if a != app] + [app]
        frappe.db.set_global("installed_apps", json.dumps(apps))
        frappe.clear_cache()
    return apps
