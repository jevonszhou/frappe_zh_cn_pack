from __future__ import annotations

import argparse
import ast
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
LOCALE = BASE / "locale"
DEFAULT_LOCALE = "zh"


@dataclass(frozen=True)
class TranslationEntry:
	app: str
	msgid: str
	msgstr: str
	context: str | None


def main() -> int:
	if hasattr(sys.stdout, "reconfigure"):
		sys.stdout.reconfigure(encoding="utf-8")

	parser = argparse.ArgumentParser(description="Audit separated zh translation catalogs.")
	parser.add_argument("--locale", default=DEFAULT_LOCALE)
	parser.add_argument("--fail-on-conflict", action="store_true")
	parser.add_argument("--max-conflicts", type=int, default=20)
	args = parser.parse_args()

	legacy_file = LOCALE / f"{args.locale}.po"
	if legacy_file.exists():
		print(f"ERROR: remove global merged catalog: {legacy_file}")
		return 1

	entries = list(read_all_entries(args.locale))
	conflicts = get_conflicts(entries)

	print(f"apps={len({entry.app for entry in entries})}")
	print(f"entries={len(entries)}")
	print(f"conflicts={len(conflicts)}")

	for index, ((msgid, context), translations) in enumerate(conflicts.items()):
		if index >= args.max_conflicts:
			remaining = len(conflicts) - args.max_conflicts
			print(f"... {remaining} more conflicts omitted")
			break

		context_label = context or ""
		print(f"\nmsgid={msgid!r} context={context_label!r}")
		for msgstr, apps in sorted(translations.items()):
			print(f"  {', '.join(sorted(apps))}: {msgstr!r}")

	return 1 if args.fail_on_conflict and conflicts else 0


def read_all_entries(locale: str) -> list[TranslationEntry]:
	entries: list[TranslationEntry] = []
	for app_dir in sorted(path for path in LOCALE.iterdir() if path.is_dir()):
		po_path = app_dir / f"{locale}.po"
		csv_path = app_dir / f"{locale}.csv"

		if po_path.exists():
			entries.extend(read_po_entries(app_dir.name, po_path))
		elif csv_path.exists():
			entries.extend(read_csv_entries(app_dir.name, csv_path))

	return entries


def read_po_entries(app: str, path: Path) -> list[TranslationEntry]:
	entries: list[TranslationEntry] = []
	current = {"msgctxt": None, "msgid": "", "msgstr": "", "fuzzy": False}
	active_field: str | None = None

	def flush() -> None:
		if current["msgid"] and current["msgstr"] and not current["fuzzy"]:
			entries.append(
				TranslationEntry(
					app=app,
					msgid=str(current["msgid"]),
					msgstr=str(current["msgstr"]),
					context=current["msgctxt"],
				)
			)

	def reset() -> None:
		nonlocal active_field
		current["msgctxt"] = None
		current["msgid"] = ""
		current["msgstr"] = ""
		current["fuzzy"] = False
		active_field = None

	for raw_line in path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()

		if not line:
			flush()
			reset()
			continue

		if line.startswith("#,") and "fuzzy" in line:
			current["fuzzy"] = True
			continue

		if line.startswith("#"):
			continue

		if line.startswith("msgctxt "):
			active_field = "msgctxt"
			current["msgctxt"] = parse_po_string(line.removeprefix("msgctxt "))
			continue

		if line.startswith("msgid "):
			active_field = "msgid"
			current["msgid"] = parse_po_string(line.removeprefix("msgid "))
			continue

		if line.startswith("msgstr "):
			active_field = "msgstr"
			current["msgstr"] = parse_po_string(line.removeprefix("msgstr "))
			continue

		if line.startswith('"') and active_field:
			current[active_field] = str(current[active_field] or "") + parse_po_string(line)

	flush()
	return entries


def read_csv_entries(app: str, path: Path) -> list[TranslationEntry]:
	entries: list[TranslationEntry] = []
	with path.open("r", encoding="utf-8-sig", newline="") as source_file:
		for row in csv.reader(source_file):
			if len(row) < 2:
				continue

			msgid = row[0].replace("\\n", "\n").strip()
			msgstr = row[1].replace("\\n", "\n").strip()
			context = row[2].strip() if len(row) >= 3 and row[2].strip() else None

			if msgid and msgstr:
				entries.append(TranslationEntry(app=app, msgid=msgid, msgstr=msgstr, context=context))

	return entries


def parse_po_string(value: str) -> str:
	return ast.literal_eval(value)


def get_conflicts(entries: list[TranslationEntry]) -> dict[tuple[str, str | None], dict[str, set[str]]]:
	by_source: dict[tuple[str, str | None], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

	for entry in entries:
		by_source[(entry.msgid, entry.context)][entry.msgstr].add(entry.app)

	return {key: value for key, value in by_source.items() if len(value) > 1}


if __name__ == "__main__":
	raise SystemExit(main())
