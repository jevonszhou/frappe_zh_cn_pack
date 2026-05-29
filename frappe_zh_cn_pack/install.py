from frappe_zh_cn_pack.translation_pack import install_translation_pack


def after_install():
	install_translation_pack()


def after_migrate():
	install_translation_pack()


def after_build():
	install_translation_pack()
