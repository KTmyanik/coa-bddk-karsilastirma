"""BDDK referans cache'ini config.json'daki URL'den yeniden olusturur."""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bddk_loader import load_bddk_accounts  # noqa: E402
from config_loader import load_config  # noqa: E402


def main() -> None:
    config = load_config(ROOT / "config.json")
    print(f"URL: {config.bddk_url}")
    print(f"Cache: {config.bddk_cache_file}")
    accounts = load_bddk_accounts(config.bddk_cache_file, config.bddk_url, refresh=True)
    print(f"OK: {len(accounts)} hesap yazildi")
    if accounts:
        print(f"Ilk: {accounts[0].code} {accounts[0].name}")
        print(f"Son: {accounts[-1].code} {accounts[-1].name}")


if __name__ == "__main__":
    main()
