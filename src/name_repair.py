"""PDF'ten gelen hesap adlarindaki bosluk hatalarini sozluk tabanli duzeltir.

PDF metin cikariminda iki tip hata olusur:
- Kelime yanlis bolunmus: "DAY ANAN" -> "DAYANAN", "FİNANS AL" -> "FİNANSAL"
- Bosluk yanlis yere kaymis: "KÂ R/ZARARA" -> "KÂR/ZARARA"
- Kelimeler yanlis birlesmis: "AYBEKLENEN" -> "AY BEKLENEN", "ÜÇAYA" -> "ÜÇ AYA"

Sozluk, bankanin SQL COA verisindeki (dogru yazilmis) kelimelerden kurulur.
Bir duzeltme ancak sonucu tamamen sozlukteki kelimelerden olusuyorsa uygulanir.
"""
from __future__ import annotations

import re
from typing import Iterable

from bddk_loader import BddkAccount
from config_loader import normalize_text

_MIN_VOCAB_SIZE = 50
_MIN_SPLIT_TOKEN_LEN = 5

# Kisa ama gercek baglac/kisaltmalar; bunlari "kirik parca" sayma
_CONNECTORS = {
    "VE",
    "ILE",
    "DE",
    "DA",
    "KI",
    "MI",
    "MU",
    "YA",
    "YE",
    "TE",
    "TA",
    "NE",
    "NI",
    "NU",
    "UC",
    "AY",
    "TP",
    "YP",
    "II",
    "III",
    "IV",
}


def build_vocab(names: Iterable[str]) -> set[str]:
    vocab: set[str] = set()
    for name in names:
        for part in normalize_text(name).split():
            if len(part) >= 2:
                vocab.add(part)
    return vocab


def _parts(token: str) -> list[str]:
    return normalize_text(token).split()


def _part_known(part: str, vocab: set[str]) -> bool:
    if len(part) < 2:
        return True
    if part.isdigit():
        return True
    return part in vocab


def _is_punct_only(token: str) -> bool:
    return bool(token) and not any(ch.isalnum() for ch in token)


def _ends_or_starts_with_punct(left: str, right: str) -> bool:
    if not left or not right:
        return False
    punct = set("-,.–—/")
    return left[-1] in punct or right[0] in punct


def _is_short_fragment(token: str) -> bool:
    """PDF'in kiriktigi kisa parca mi? (AL, KA, KÂ, R/..., B, DU)."""
    if not token or _is_punct_only(token) or "." in token:
        return False
    parts = _parts(token)
    if len(parts) == 1 and 1 <= len(parts[0]) <= 2 and not parts[0].isdigit():
        return parts[0] not in _CONNECTORS
    # "R/ZARARA" gibi: slash oncesi cok kisa
    if "/" in token:
        left = token.split("/", 1)[0]
        folded = re.sub(r"\s+", "", normalize_text(left))
        if 1 <= len(folded) <= 2:
            return True
    return False


def _needs_repair(token: str, vocab: set[str]) -> bool:
    parts = _parts(token)
    if not parts:
        return False
    if any(not _part_known(part, vocab) for part in parts):
        return True
    # Tek harfli serseri parca ("KÂR/ZARAR A YANSITILAN" icindeki "A" gibi).
    # Noktali kisaltmalari (T.P., Y.İ.Y.) ve sayilari elleme.
    if all(len(part) < 2 for part in parts):
        if "." in token:
            return False
        if all(part.isdigit() for part in parts):
            return False
        return True
    return False


def _seq_strictly_known(token: str, vocab: set[str]) -> bool:
    """Birlestirme sonucu icin siki kontrol: tum parcalar >=2 karakter ve sozlukte."""
    parts = _parts(token)
    if not parts:
        return False
    for part in parts:
        if len(part) < 2:
            return False
        if not part.isdigit() and part not in vocab:
            return False
    return True


def _try_split(token: str, vocab: set[str]) -> tuple[str, str] | None:
    if len(token) < _MIN_SPLIT_TOKEN_LEN:
        return None
    for index in range(2, len(token) - 1):
        left, right = token[:index], token[index:]
        if _seq_strictly_known(left, vocab) and _seq_strictly_known(right, vocab):
            return left, right
    return None


def _try_merge_pair(left: str, right: str, vocab: set[str]) -> str | None:
    if _is_punct_only(left) or _is_punct_only(right):
        return None
    if _ends_or_starts_with_punct(left, right):
        return None
    merged = left + right
    if _seq_strictly_known(merged, vocab):
        return merged
    return None


def repair_name(name: str, vocab: set[str]) -> str:
    tokens = name.split()
    result: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None
        prev_token = result[-1] if result else None

        # 0) Firsatci birlestirme: "FİNANS AL", "KÂ R/ZARARA"
        #    Parcalar tek basina "gecerli" gorunse bile kisa kirik parca varsa birlestir.
        if next_token is not None and (
            _is_short_fragment(token) or _is_short_fragment(next_token)
        ):
            merged = _try_merge_pair(token, next_token, vocab)
            if merged is not None:
                result.append(merged)
                index += 2
                continue

        if not _needs_repair(token, vocab):
            result.append(token)
            index += 1
            continue

        # 1) Sonraki ile birlestir: "DAY ANAN" -> "DAYANAN"
        if next_token is not None:
            merged = _try_merge_pair(token, next_token, vocab)
            if merged is not None:
                result.append(merged)
                index += 2
                continue

        # 2) Onceki ile birlestir: "İŞLEMLERİ NDEN" -> "İŞLEMLERİNDEN"
        if prev_token is not None:
            merged = _try_merge_pair(prev_token, token, vocab)
            if merged is not None:
                result[-1] = merged
                index += 1
                continue

        # 3) Sonraki ile birlestir + dogru yerden bol:
        #    "ZARA RAYANSITILMASI" -> "ZARARA YANSITILMASI"
        if next_token is not None and not _ends_or_starts_with_punct(token, next_token):
            split = _try_split(token + next_token, vocab)
            if split:
                result.extend(split)
                index += 2
                continue

        # 4) Onceki ile birlestir + dogru yerden bol
        if prev_token is not None and not _ends_or_starts_with_punct(prev_token, token):
            split = _try_split(prev_token + token, vocab)
            if split:
                result[-1] = split[0]
                result.append(split[1])
                index += 1
                continue

        # 5) Tek tokeni bol: "AYBEKLENEN" -> "AY BEKLENEN"
        split = _try_split(token, vocab)
        if split:
            result.extend(split)
            index += 1
            continue

        result.append(token)
        index += 1

    return " ".join(result)


def repair_accounts(
    accounts: Iterable[BddkAccount],
    vocab_names: Iterable[str],
) -> list[BddkAccount]:
    vocab = build_vocab(vocab_names)
    account_list = list(accounts)
    if len(vocab) < _MIN_VOCAB_SIZE:
        return account_list
    return [
        BddkAccount(code=account.code, name=repair_name(account.name, vocab))
        for account in account_list
    ]
