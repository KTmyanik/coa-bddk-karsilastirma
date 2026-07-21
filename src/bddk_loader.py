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


IZAHNAME_SPLIT_RE = re.compile(
    r"II\.?\s*Tekd[uü]zen\s+hesap\s+plan[ıi]\s+izahnamesi",
    re.IGNORECASE,
)
# Kod tek basina veya ad ile ayni satirda; kod icinde PDF kaynakli bosluk olabilir: "151 005"
CODE_LINE_RE = re.compile(r"^(\d+(?:\s+\d+)*)(?:\s+(.*))?$")
HEADER_MARKERS = (
    "TEKDÜZEN HESAP",
    "TEKDUZEN HESAP",
    "KATILIM ESASINA GÖRE",
    "KATILIM ESASINA GORE",
    "PLANI VE İZAHNAMESİ",
    "PLANI VE IZAHNAMESI",
)
HEADER_TAIL_RE = re.compile(
    r"\s*(KATILIM ESASINA G[OÖ]RE.*|TEKD[UÜ]ZEN HESAP.*|PLANI VE [İI]ZAHNAMES[İI])\s*$",
    re.IGNORECASE,
)


def _normalize_code(raw_code: str) -> str:
    return re.sub(r"\s+", "", raw_code.strip())


def _normalize_name(name: str) -> str:
    name = re.sub(r"[ \t]+", " ", name).strip()
    name = HEADER_TAIL_RE.sub("", name).strip()
    tokens = name.split(" ")
    if len(tokens) <= 1:
        return name

    short_words = {
        "VE",
        "ILE",
        "İLE",
        "YA",
        "TE",
        "MI",
        "MU",
        "T.P",
        "T.P.",
        "Y.P",
        "Y.P.",
        "TP",
        "YP",
        "-",
        "–",
    }
    merged: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if index + 1 < len(tokens):
            nxt = tokens[index + 1]
            should_merge = False
            if (
                1 <= len(token) <= 2
                and token.upper() not in short_words
                and not token.endswith((".", "-", "–", ","))
                and nxt.upper() not in short_words
                and not nxt.startswith(("(", "-", "–"))
                and re.fullmatch(r"[A-Za-zÀ-žİıŞşĞğÜüÖöÇçÂâ]+", token)
            ):
                should_merge = True
            elif re.search(r"/[A-Za-zİıŞşĞğÜüÖöÇç]$", token) and nxt:
                should_merge = True
            if should_merge:
                merged.append(token + nxt)
                index += 2
                continue
        merged.append(token)
        index += 1
    return " ".join(merged)


def _is_header_line(line: str) -> bool:
    upper = line.upper()
    if line.startswith("I."):
        return True
    if any(marker in upper for marker in HEADER_MARKERS):
        return True
    if "YÖNETMELİK" in upper and len(line) > 80:
        return True
    if "YONETMELIK" in upper and len(line) > 80:
        return True
    return False


def _split_code_and_rest(line: str) -> tuple[str | None, str]:
    """Return (code, rest). code=None means continuation / non-account line."""
    match = CODE_LINE_RE.match(line)
    if not match:
        return None, line

    code = _normalize_code(match.group(1))
    rest = (match.group(2) or "").strip()

    # Asiri uzun sayisal cop satirlari ele
    if not code or len(code) > 14:
        return None, line
    return code, rest


def parse_bddk_text(text: str) -> list[BddkAccount]:
    split = IZAHNAME_SPLIT_RE.split(text, maxsplit=1)
    if len(split) > 1:
        text = split[0]

    accounts: list[BddkAccount] = []
    seen: set[str] = set()
    pending_code: str | None = None
    pending_name_parts: list[str] = []

    def flush() -> None:
        nonlocal pending_code, pending_name_parts
        if not pending_code:
            pending_name_parts = []
            return
        name = _normalize_name(" ".join(pending_name_parts))
        if name and pending_code not in seen:
            seen.add(pending_code)
            accounts.append(BddkAccount(code=pending_code, name=name))
        pending_code = None
        pending_name_parts = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _is_header_line(line):
            continue

        code, rest = _split_code_and_rest(line)

        if code is None:
            # Devam satiri: onceki hesabin adina ekle
            if pending_code is not None:
                pending_name_parts.append(rest)
            continue

        # Yeni hesap kodu geldi -> onceki hesabi kapat
        flush()
        pending_code = code
        if rest:
            pending_name_parts.append(rest)
        # rest bos ise sonraki satirlarda ad gelecek

    flush()
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

    is_pdf = "pdf" in content_type or "pdf" in disposition or raw[:4] == b"%PDF"
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
