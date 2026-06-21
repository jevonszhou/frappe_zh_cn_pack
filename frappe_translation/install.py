from frappe_translation.translation_pack import install_translation_pack


def after_install():
	install_translation_pack()


def after_migrate():
	install_translation_pack()
