from __future__ import annotations

import json
import re
import ssl
import urllib.request
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class BddkAccount:
    code: str
    name: str


ACCOUNT_LINE_RE = re.compile(r"^(\d+)\s+(.+?)\s*$")
IZAHNAME_SPLIT_RE = re.compile(
    r"II\.?\s*Tekd[uü]zen\s+hesap\s+plan[ıi]\s+izahnamesi",
    re.IGNORECASE,
)


def parse_bddk_text(text: str) -> list[BddkAccount]:
    split = IZAHNAME_SPLIT_RE.split(text, maxsplit=1)
    if len(split) > 1:
        text = split[0]

    accounts: list[BddkAccount] = []
    seen: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("I."):
            continue
        if "TEKDÜZEN HESAP" in line.upper() or "TEKDUZEN HESAP" in line.upper():
            continue
        if "Yönetmelik" in line and len(line) > 80:
            continue

        match = ACCOUNT_LINE_RE.match(line)
        if not match:
            continue

        code = match.group(1)
        name = re.sub(r"\s+", " ", match.group(2).strip())
        if not name or code in seen:
            continue
        # PDF obj / garbage filtre
        if name.lower().endswith("obj") or name.startswith("/"):
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


def _extract_pdf_text(raw: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(raw))
    parts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text:
            parts.append(page_text)
    return "\n".join(parts)


def fetch_bddk_from_url(url: str) -> list[BddkAccount]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 CoaBddkCompare/1.0"},
    )
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(request, timeout=120, context=context) as response:
        content_type = (response.headers.get("Content-Type") or "").lower()
        disposition = (response.headers.get("Content-Disposition") or "").lower()
        raw = response.read()

    is_pdf = (
        "pdf" in content_type
        or "pdf" in disposition
        or raw[:4] == b"%PDF"
    )
    if is_pdf:
        text = _extract_pdf_text(raw)
        return parse_bddk_text(text)

    if "html" in content_type:
        text = raw.decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
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
