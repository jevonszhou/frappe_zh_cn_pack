from frappe_translation.assets import ensure_static_assets
from frappe_translation.translation_pack import install_translation_pack


def sync_translation_app():
	ensure_static_assets()
	install_translation_pack()
	ensure_desktop_icon_logo()


def after_install():
	sync_translation_app()


def after_migrate():
	sync_translation_app()


def after_build():
	sync_translation_app()


def ensure_desktop_icon_logo():
	"""Ensure the Desktop Icon for Frappe Translation exists and has the correct logo_url.

	Frappe's `create_desktop_icons_from_installed_apps` only creates the Desktop Icon
	record if it doesn't already exist, so it never repairs a missing/stale `logo_url`.
	This syncs `logo_url` (and `link`) with the `add_to_apps_screen` hook on every
	install/migrate so the logo renders correctly on the desktop.
	"""
	import frappe
	from frappe.desk.doctype.desktop_icon.desktop_icon import clear_desktop_icons_cache

	app_name = "frappe_translation"
	app_details = frappe.get_hooks("add_to_apps_screen", app_name=app_name)
	if not app_details:
		return

	logo_url = app_details[0].get("logo")
	route = app_details[0].get("route")
	app_title = (
		frappe.get_hooks("app_title", app_name=app_name)
		and frappe.get_hooks("app_title", app_name=app_name)[0]
	) or app_name

	if not logo_url:
		return

	existing_icons = frappe.get_all(
		"Desktop Icon",
		filters={"icon_type": "App", "app": app_name},
		pluck="name",
	)

	if existing_icons:
		for icon_name in existing_icons:
			icon = frappe.get_doc("Desktop Icon", icon_name)
			changed = False
			if icon.logo_url != logo_url:
				icon.logo_url = logo_url
				changed = True
			if route and icon.link != route:
				icon.link = route
				changed = True
			if changed:
				icon.save(ignore_permissions=True)
	else:
		# Create the Desktop Icon record if Frappe hasn't created one yet.
		if not frappe.db.exists(
			"Desktop Icon", {"label": app_title, "icon_type": "App"}
		):
			icon = frappe.new_doc("Desktop Icon")
			icon.label = app_title
			icon.link_type = "External"
			icon.icon_type = "App"
			icon.app = app_name
			icon.link = route
			icon.logo_url = logo_url
			icon.save(ignore_permissions=True)

	clear_desktop_icons_cache()
