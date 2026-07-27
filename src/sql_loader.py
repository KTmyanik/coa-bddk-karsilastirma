from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pyodbc

from config_loader import AppConfig, normalize_code


@dataclass(frozen=True)
class CoaRecord:
    code: str
    name: str


def build_connection_string(config: AppConfig) -> str:
    parts = [
        "DRIVER={ODBC Driver 17 for SQL Server}",
        f"SERVER={config.sql_server}",
        f"DATABASE={config.database}",
    ]
    if config.trusted_connection:
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={config.username}")
        parts.append(f"PWD={config.password}")
    return ";".join(parts) + ";"


def read_query_text(query_file: Path) -> str:
    if not query_file.exists():
        raise FileNotFoundError(f"Sorgu dosyasi bulunamadi: {query_file}")
    return query_file.read_text(encoding="utf-8-sig").strip()


def load_coa_from_sql(config: AppConfig) -> tuple[list[CoaRecord], str]:
    query = read_query_text(config.query_file)
    if not query:
        raise ValueError(f"Sorgu dosyasi bos: {config.query_file}")

    connection = pyodbc.connect(
        build_connection_string(config),
        timeout=config.command_timeout_seconds,
    )
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
    finally:
        connection.close()

    code_index = _find_column_index(columns, config.code_column)
    name_index = _find_column_index(columns, config.name_column)

    records: list[CoaRecord] = []
    for row in rows:
        code = normalize_code(row[code_index])
        # Tablodaki hesap adini oldugu gibi al (Turkce karakter / noktalama degistirme)
        name = str(row[name_index] or "").strip()
        if not code:
            continue
        records.append(CoaRecord(code=code, name=name))

    return records, query


def _find_column_index(columns: list[str], expected: str) -> int:
    normalized_expected = expected.casefold()
    for index, column in enumerate(columns):
        if column.casefold() == normalized_expected:
            return index
    raise ValueError(
        f"Sorgu sonucunda '{expected}' kolonu bulunamadi. Donen kolonlar: {', '.join(columns)}"
    )
