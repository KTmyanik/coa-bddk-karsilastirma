from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    sql_server: str
    database: str
    trusted_connection: bool
    username: str
    password: str
    query_file: Path
    code_column: str
    name_column: str
    bddk_url: str
    bddk_cache_file: Path
    command_timeout_seconds: int


def project_root() -> Path:
    if getattr(__import__("sys"), "frozen", False):
        return Path(__import__("sys").executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return project_root() / path


def load_config(config_path: Path | None = None) -> AppConfig:
    path = config_path or (project_root() / "config.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    return AppConfig(
        sql_server=payload["sql_server"],
        database=payload["database"],
        trusted_connection=bool(payload.get("trusted_connection", True)),
        username=payload.get("username", ""),
        password=payload.get("password", ""),
        query_file=resolve_project_path(payload["query_file"]),
        code_column=payload.get("code_column", "Ledgercode"),
        name_column=payload.get("name_column", "Ledgername"),
        bddk_url=payload.get("bddk_url", "https://www.bddk.org.tr/Mevzuat/DokumanGetir/1043"),
        bddk_cache_file=resolve_project_path(payload.get("bddk_cache_file", "data/bddk_reference.json")),
        command_timeout_seconds=int(payload.get("command_timeout_seconds", 120)),
    )


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper()
    text = text.replace("İ", "I").replace("İ", "I")
    text = re.sub(r"[^A-Z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_code(value: str | int | float) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return re.sub(r"\s+", "", text)


def code_variants(code: str) -> list[str]:
    code = normalize_code(code)
    if not code:
        return []

    variants = {code, code.lstrip("0") or "0"}
    for width in (3, 4, 5, 6, 7, 8, 9):
        variants.add(code.zfill(width))
        variants.add(code.lstrip("0").zfill(width))

    return sorted(variants, key=len, reverse=True)
