import json
import frappe

APP = "frappe_zh_cn_pack"

def ensure_app_last():
    apps = frappe.get_installed_apps()
    if APP in apps and apps[-1] != APP:
        apps = [app for app in apps if app != APP] + [APP]
        frappe.db.set_global("installed_apps", json.dumps(apps))
        frappe.db.commit()
        frappe.clear_cache()
    return apps

def after_install():
    ensure_app_last()

def after_migrate():
    ensure_app_last()
