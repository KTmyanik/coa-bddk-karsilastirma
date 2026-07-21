"""Karsilastirma akisinin isim onarimini uyguladigini dogrular."""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bddk_loader import load_bddk_accounts  # noqa: E402
from comparator import CoaComparator  # noqa: E402
from config_loader import load_config  # noqa: E402
from sql_loader import load_coa_from_sql  # noqa: E402


def main() -> None:
    config = load_config(ROOT / "config.json")
    accounts = load_bddk_accounts(config.bddk_cache_file, config.bddk_url, refresh=False)
    records, _ = load_coa_from_sql(config)

    comparator = CoaComparator(accounts)
    results = comparator.compare_all(records)
    by_code = {result.code: result for result in results}

    for code in ["154", "160", "18200", "22006", "222011", "30808", "32010", "821031"]:
        result = by_code.get(code)
        if result is None:
            print(f"{code}: SONUCTA YOK")
            continue
        print(f"{code} [{result.status}] benzerlik={result.similarity}")
        print(f"  BDDK: {result.bddk_name}")
        print(f"  SQL : {result.sql_name}")


if __name__ == "__main__":
    main()
