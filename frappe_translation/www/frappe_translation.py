import frappe


def get_context(context):
	context.title = "Frappe Translation"
	context.app_name = "frappe_translation"
	context.app_title = "Frappe Translation"
	context.app_description = (
		"A custom app to integrate optimized language translations for Frappe apps."
	)
	context.logo_url = "/assets/frappe_translation/images/logo.svg"
	context.css_url = "/assets/frappe_translation/css/frappe_translation.css"
	context.js_url = "/assets/frappe_translation/js/frappe_translation.bundle.js"
	context.assets_base = "/assets/frappe_translation"
	context.no_cache = 1
	return context
