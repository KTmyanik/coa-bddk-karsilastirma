"""Karsilastirma sonucunu Excel uyumlu CSV olarak yazar."""
from __future__ import annotations

import csv
from pathlib import Path

from comparator import CompareResult

CSV_HEADERS = [
    "Kod",
    "BddkKodu",
    "SorguKodu",
    "BddkAdi",
    "SorguHesapAdi",
    "Durum",
    "Eslesme_Durum",
    "Benzerlik",
    "Aciklama",
]


def export_results_csv(results: list[CompareResult], target: Path) -> Path:
    target = Path(target)
    if target.suffix.lower() not in {".csv", ".txt"}:
        # Klasor verilmisse varsayilan dosya adi kullan
        if target.exists() and target.is_dir():
            target = target / "coa_bddk_karsilastirma.csv"
        elif not target.suffix:
            target = target.with_suffix(".csv")

    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(CSV_HEADERS)
        for row in results:
            writer.writerow(
                [
                    row.code,
                    row.bddk_code,
                    row.sql_code,
                    row.bddk_name,
                    row.sql_name,
                    row.status,
                    row.match_status,
                    f"{row.similarity:.4f}" if row.similarity else "",
                    row.detail,
                ]
            )
    return target
