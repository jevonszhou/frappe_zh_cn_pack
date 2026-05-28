from pathlib import Path
import csv
from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po, write_po

BASE = Path(__file__).resolve().parents[1]
LOCALE = BASE / "locale"
OUT = LOCALE / "zh.po"

PO_SOURCES = [
    ("frappe", LOCALE / "frappe" / "zh.po"),
    ("erpnext", LOCALE / "erpnext" / "zh.po"),
    ("hrms", LOCALE / "hrms" / "zh.po"),
    ("crm", LOCALE / "crm" / "zh.po"),
    ("insights", LOCALE / "insights" / "zh.po"),
]

CSV_SOURCES = [
    ("education", LOCALE / "education" / "zh.csv"),
]

merged = {}

for source_app, path in PO_SOURCES:
    if not path.exists():
        print(f"skip missing {path}")
        continue

    with path.open("rb") as f:
        catalog = read_po(f, locale="zh")

    for msg in catalog:
        if not msg.id or not msg.string:
            continue
        if "fuzzy" in msg.flags:
            continue

        key = (msg.id, msg.context)
        merged[key] = {
            "string": msg.string,
            "context": msg.context,
            "source_app": source_app,
        }

for source_app, path in CSV_SOURCES:
    if not path.exists():
        print(f"skip missing {path}")
        continue

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if len(row) < 2:
                continue

            msgid = row[0].replace("\\n", "\n").strip()
            msgstr = row[1].replace("\\n", "\n").strip()
            context = row[2].strip() if len(row) >= 3 and row[2].strip() else None

            if not msgid or not msgstr:
                continue

            key = (msgid, context)
            merged[key] = {
                "string": msgstr,
                "context": context,
                "source_app": source_app,
            }

result = Catalog(
    locale="zh",
    domain="messages",
    project="Frappe zh-CN Translation Pack",
    fuzzy=False,
)

for msgid, context in sorted(merged.keys(), key=lambda x: (str(x[0]), str(x[1] or ""))):
    item = merged[(msgid, context)]
    result.add(
        msgid,
        string=item["string"],
        context=context,
        auto_comments=[f"source-app: {item['source_app']}"],
    )

with OUT.open("wb") as f:
    write_po(f, result, sort_output=True, width=None)

print(f"written {OUT}, entries={len(merged)}")