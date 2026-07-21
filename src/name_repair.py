"""PDF'ten gelen hesap adlarindaki bosluk hatalarini sozluk tabanli duzeltir.

PDF metin cikariminda iki tip hata olusur:
- Kelime yanlis bolunmus: "DAY ANAN" -> "DAYANAN", "YAP ILANDIRILAN" -> "YAPILANDIRILAN"
- Bosluk yanlis yere kaymis: "KÂR/ZARA RAYANSITILMASI" -> "KÂR/ZARARA YANSITILMASI"
- Kelimeler yanlis birlesmis: "AYBEKLENEN" -> "AY BEKLENEN", "ÜÇAYA" -> "ÜÇ AYA"

Sozluk, bankanin SQL COA verisindeki (dogru yazilmis) kelimelerden kurulur.
Bir duzeltme ancak sonucu tamamen sozlukteki kelimelerden olusuyorsa uygulanir.
"""
from __future__ import annotations

from typing import Iterable

from bddk_loader import BddkAccount
from config_loader import normalize_text

_MIN_VOCAB_SIZE = 50
_MIN_SPLIT_TOKEN_LEN = 5


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


def repair_name(name: str, vocab: set[str]) -> str:
    tokens = name.split()
    result: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if not _needs_repair(token, vocab):
            result.append(token)
            index += 1
            continue

        next_token = tokens[index + 1] if index + 1 < len(tokens) else None
        prev_token = result[-1] if result else None

        # 1) Sonraki ile birlestir: "DAY ANAN" -> "DAYANAN"
        if next_token is not None and _seq_strictly_known(token + next_token, vocab):
            result.append(token + next_token)
            index += 2
            continue

        # 2) Onceki ile birlestir: "İŞLEMLERİ NDEN" -> "İŞLEMLERİNDEN",
        #    "KÂR/ZARAR A" -> "KÂR/ZARARA"
        if prev_token is not None and _seq_strictly_known(prev_token + token, vocab):
            result[-1] = prev_token + token
            index += 1
            continue

        # 3) Sonraki ile birlestir + dogru yerden bol:
        #    "ZARA RAYANSITILMASI" -> "ZARARA YANSITILMASI"
        if next_token is not None:
            split = _try_split(token + next_token, vocab)
            if split:
                result.extend(split)
                index += 2
                continue

        # 4) Onceki ile birlestir + dogru yerden bol
        if prev_token is not None:
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
