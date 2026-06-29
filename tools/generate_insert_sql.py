"""coa.csv dosyasindan sql/02_insert_data.sql uretir."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "coa.csv"
OUT_PATH = ROOT / "sql" / "02_insert_data.sql"
BATCH_SIZE = 500


def escape(value: str) -> str:
    return value.replace("'", "''")


def main() -> None:
    df = pd.read_csv(CSV_PATH, dtype=str)
    lines = [
        "-- Otomatik uretildi: tools/generate_insert_sql.py",
        "SET NOCOUNT ON;",
        "GO",
        "TRUNCATE TABLE dbo.CoaLedger;",
        "GO",
    ]

    values: list[str] = []
    for _, row in df.iterrows():
        code = escape(str(row["Ledgercode"]).strip())
        name = escape(str(row["Ledgername"]).strip())
        values.append(f"('{code}', N'{name}')")
        if len(values) >= BATCH_SIZE:
            lines.append("INSERT INTO dbo.CoaLedger (Ledgercode, Ledgername) VALUES")
            lines.append(",\n".join(values) + ";")
            lines.append("GO")
            values = []

    if values:
        lines.append("INSERT INTO dbo.CoaLedger (Ledgercode, Ledgername) VALUES")
        lines.append(",\n".join(values) + ";")
        lines.append("GO")

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
