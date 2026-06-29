from __future__ import annotations

import json
import re
import ssl
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class BddkAccount:
    code: str
    name: str


ACCOUNT_LINE_RE = re.compile(r"^(\d+)\s+(.+?)\s*$")


def parse_bddk_text(text: str) -> list[BddkAccount]:
    if "II. Tekdüzen hesap planı izahnamesi" in text:
        text = text.split("II. Tekdüzen hesap planı izahnamesi", maxsplit=1)[0]

    accounts: list[BddkAccount] = []
    seen: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("I."):
            continue
        match = ACCOUNT_LINE_RE.match(line)
        if not match:
            continue

        code = match.group(1)
        name = match.group(2).strip()
        if code in seen:
            continue
        seen.add(code)
        accounts.append(BddkAccount(code=code, name=name))

    return accounts


def load_bddk_cache(cache_file: Path) -> list[BddkAccount]:
    payload = json.loads(cache_file.read_text(encoding="utf-8"))
    return [BddkAccount(code=item["code"], name=item["name"]) for item in payload]


def save_bddk_cache(cache_file: Path, accounts: Iterable[BddkAccount]) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    payload = [{"code": account.code, "name": account.name} for account in accounts]
    cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_bddk_from_url(url: str) -> list[BddkAccount]:
    request = urllib.request.Request(url, headers={"User-Agent": "CoaBddkCompare/1.0"})
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(request, timeout=90, context=context) as response:
        content_type = response.headers.get("Content-Type", "")
        raw = response.read()

    if "html" in content_type.lower():
        text = raw.decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return parse_bddk_text(text)

    return parse_bddk_text(raw.decode("utf-8", errors="ignore"))


def load_bddk_accounts(cache_file: Path, url: str, refresh: bool = False) -> list[BddkAccount]:
    if cache_file.exists() and not refresh:
        return load_bddk_cache(cache_file)

    try:
        accounts = fetch_bddk_from_url(url)
        if accounts:
            save_bddk_cache(cache_file, accounts)
            return accounts
    except Exception:
        if cache_file.exists():
            return load_bddk_cache(cache_file)
        raise

    if cache_file.exists():
        return load_bddk_cache(cache_file)

    raise RuntimeError("BDDK hesap plani yuklenemedi.")
