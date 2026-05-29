from __future__ import annotations

try:
	from .audit_zh_sources import main
except ImportError:
	from audit_zh_sources import main

print("merge_zh.py is deprecated: translations now stay separated per app.")

raise SystemExit(main())
