"""GUI acmadan karsilastirir, config'teki yola Excel/CSV yazar ve cikar."""
from __future__ import annotations

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    APP_ROOT = Path(sys.executable).resolve().parent
else:
    APP_ROOT = Path(__file__).resolve().parents[1]

SRC_DIR = APP_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bddk_loader import load_bddk_accounts  # noqa: E402
from comparator import CoaComparator  # noqa: E402
from config_loader import load_config, project_root  # noqa: E402
from export_util import export_results_csv  # noqa: E402
from sql_loader import load_coa_from_sql  # noqa: E402


def _summary(results) -> str:
    counts: dict[str, int] = {}
    for row in results:
        counts[row.status] = counts.get(row.status, 0) + 1
    return " | ".join(f"{key}: {value}" for key, value in sorted(counts.items()))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    config_path = project_root() / "config.json"
    print("Config:", config_path)

    config = load_config(config_path)
    if not config.export_file:
        print(
            "[HATA] config.json icinde 'export_file' tanimli degil.\n"
            'Ornek: "export_file": "C:\\\\Users\\\\mesut\\\\Desktop\\\\coa_bddk_karsilastirma.csv"'
        )
        return 1

    print("SQL sorgusu calistiriliyor...")
    records, _ = load_coa_from_sql(config)
    print(f"  {len(records)} COA kaydi")

    print("BDDK hesap plani indiriliyor...")
    bddk_accounts = load_bddk_accounts(
        config.bddk_cache_file,
        config.bddk_url,
        refresh=True,
    )
    print(f"  {len(bddk_accounts)} BDDK hesabi")

    print("Karsilastirma yapiliyor...")
    results = CoaComparator(bddk_accounts).compare_all(records)
    print(f"  {len(results)} kod | {_summary(results)}")

    print("Excel/CSV yaziliyor...")
    target = export_results_csv(results, config.export_file)
    print(f"OK: {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[HATA] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
