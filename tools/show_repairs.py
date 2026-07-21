"""Onarimin degistirdigi tum adlari once/sonra olarak listeler."""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bddk_loader import _extract_pdf_text, parse_bddk_text  # noqa: E402
from config_loader import load_config  # noqa: E402
from name_repair import repair_accounts  # noqa: E402
from sql_loader import load_coa_from_sql  # noqa: E402

raw = (ROOT / "data" / "bddk_1334.pdf").read_bytes()
accounts = parse_bddk_text(_extract_pdf_text(raw))

config = load_config(ROOT / "config.json")
records, _ = load_coa_from_sql(config)
repaired = repair_accounts(accounts, [record.name for record in records])

for before, after in zip(accounts, repaired):
    if before.name != after.name:
        print(f"{before.code}")
        print(f"  ONCE : {before.name}")
        print(f"  SONRA: {after.name}")
