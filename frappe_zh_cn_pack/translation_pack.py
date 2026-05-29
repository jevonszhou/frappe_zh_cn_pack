from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "frappe_zh_cn_pack"
DEFAULT_LOCALE = "zh"
LOCALE_DIR = "locale"


@dataclass(frozen=True)
class TranslationSource:
	app: str
	locale: str
	path: Path
	file_format: str


def install_translation_pack(locale: str = DEFAULT_LOCALE, apps: list[str] | None = None) -> list[str]:
	"""Compile bundled per-app translations into Frappe's runtime asset catalogs."""
	outputs = []
	for output_path in compile_translation_assets(locale=locale, apps=apps):
		outputs.append(str(output_path))

	clear_translation_cache()
	return outputs


def compile_translation_assets(locale: str = DEFAULT_LOCALE, apps: list[str] | None = None) -> list[Path]:
	from babel.messages.mofile import write_mo
	from babel.messages.pofile import read_po

	target_dir = get_target_messages_dir(locale)
	target_dir.mkdir(parents=True, exist_ok=True)
	remove_legacy_merged_asset(locale=locale)

	outputs: list[Path] = []
	for source in discover_translation_sources(locale=locale, apps=apps):
		target_path = target_dir / f"{source.app}.mo"

		if source.file_format == "po":
			with source.path.open("rb") as source_file:
				catalog = read_po(source_file, locale=locale)
		elif source.file_format == "csv":
			catalog = read_csv_as_catalog(source)
		else:
			continue

		with target_path.open("wb") as target_file:
			write_mo(target_file, catalog)

		outputs.append(target_path)

	return outputs


def discover_translation_sources(
	locale: str = DEFAULT_LOCALE,
	apps: list[str] | None = None,
) -> list[TranslationSource]:
	source_root = get_source_locale_dir()
	app_filter = set(apps or [])
	sources: list[TranslationSource] = []

	if not source_root.exists():
		return sources

	for app_dir in sorted(path for path in source_root.iterdir() if path.is_dir()):
		app = app_dir.name
		if app_filter and app not in app_filter:
			continue

		po_path = app_dir / f"{locale}.po"
		csv_path = app_dir / f"{locale}.csv"

		if po_path.exists():
			sources.append(TranslationSource(app=app, locale=locale, path=po_path, file_format="po"))
		elif csv_path.exists():
			sources.append(TranslationSource(app=app, locale=locale, path=csv_path, file_format="csv"))

	return sources


def read_csv_as_catalog(source: TranslationSource):
	from babel.messages.catalog import Catalog

	catalog = Catalog(
		locale=source.locale,
		domain=source.app,
		project=f"{source.app} Chinese translations",
		fuzzy=False,
	)

	with source.path.open("r", encoding="utf-8-sig", newline="") as source_file:
		for row in csv.reader(source_file):
			if len(row) < 2:
				continue

			msgid = row[0].replace("\\n", "\n").strip()
			msgstr = row[1].replace("\\n", "\n").strip()
			context = row[2].strip() if len(row) >= 3 and row[2].strip() else None

			if msgid and msgstr:
				catalog.add(msgid, string=msgstr, context=context)

	return catalog


def remove_legacy_merged_asset(locale: str = DEFAULT_LOCALE) -> None:
	legacy_path = get_target_messages_dir(locale) / f"{APP_NAME}.mo"
	if legacy_path.exists():
		legacy_path.unlink()


def clear_translation_cache() -> None:
	try:
		from frappe.translate import clear_cache

		clear_cache()
	except Exception:
		try:
			import frappe

			frappe.clear_cache()
		except Exception:
			pass


def get_source_locale_dir() -> Path:
	import frappe

	return Path(frappe.get_app_path(APP_NAME, LOCALE_DIR))


def get_target_messages_dir(locale: str = DEFAULT_LOCALE) -> Path:
	from frappe.utils import get_bench_path

	return Path(get_bench_path()) / "sites" / "assets" / "locale" / locale / "LC_MESSAGES"
