from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from bddk_loader import BddkAccount
from config_loader import normalize_text
from sql_loader import CoaRecord


@dataclass(frozen=True)
class CompareResult:
    code: str
    bddk_code: str
    sql_code: str
    bddk_name: str
    sql_name: str
    status: str
    detail: str
    similarity: float


class CoaComparator:
    def __init__(self, bddk_accounts: list[BddkAccount]) -> None:
        self._bddk_by_code: dict[str, str] = {
            account.code: account.name for account in bddk_accounts
        }

    def compare_all(self, records: list[CoaRecord]) -> list[CompareResult]:
        sql_by_code: dict[str, list[str]] = {}
        for record in records:
            names = sql_by_code.setdefault(record.code, [])
            if record.name not in names:
                names.append(record.name)

        all_codes = sorted(
            set(self._bddk_by_code.keys()) | set(sql_by_code.keys()),
            key=self._sort_key,
        )

        return [self._compare_code(code, sql_by_code) for code in all_codes]

    def _compare_code(self, code: str, sql_by_code: dict[str, list[str]]) -> CompareResult:
        in_bddk = code in self._bddk_by_code
        in_sql = code in sql_by_code

        bddk_code = code if in_bddk else ""
        sql_code = code if in_sql else ""
        bddk_name = self._bddk_by_code.get(code, "")
        sql_names = sql_by_code.get(code, [])
        sql_name = " | ".join(sql_names)

        if in_bddk and in_sql:
            return self._compare_both(code, bddk_name, sql_names)
        if in_bddk:
            return CompareResult(
                code=code,
                bddk_code=bddk_code,
                sql_code="",
                bddk_name=bddk_name,
                sql_name="",
                status="SADECE_BDDK",
                detail="Kod BDDK hesap planinda var, sorgu sonucunda yok.",
                similarity=0.0,
            )
        return CompareResult(
            code=code,
            bddk_code="",
            sql_code=sql_code,
            bddk_name="",
            sql_name=sql_name,
            status="SADECE_COA",
            detail="Kod sorgu sonucunda var, BDDK hesap planinda yok.",
            similarity=0.0,
        )

    def _compare_both(
        self,
        code: str,
        bddk_name: str,
        sql_names: list[str],
    ) -> CompareResult:
        normalized_bddk = normalize_text(bddk_name)
        normalized_sql = [normalize_text(name) for name in sql_names]

        best_similarity = 0.0
        best_sql_name = sql_names[0] if sql_names else ""
        for raw_name, normalized_name in zip(sql_names, normalized_sql, strict=False):
            similarity = self._name_similarity(normalized_bddk, normalized_name)
            if similarity > best_similarity:
                best_similarity = similarity
                best_sql_name = raw_name

        sql_name = " | ".join(sql_names)
        duplicate_note = ""
        if len(sql_names) > 1:
            duplicate_note = f" Sorguda {len(sql_names)} farkli hesap adi var."

        if not normalized_bddk:
            status = "KOD_ESLESTI_ISIM_YOK"
            detail = f"{code} kodu her iki tarafta var, BDDK adi bos.{duplicate_note}"
        elif any(name == normalized_bddk for name in normalized_sql):
            status = "TAM_ESLESME"
            detail = f"{code} kodu ve adi her iki tarafta uyumlu.{duplicate_note}"
        elif any(
            name.startswith(normalized_bddk) or normalized_bddk.startswith(name)
            for name in normalized_sql
        ):
            status = "KISMEN_ESLESME"
            detail = f"{code} kodu eslesti, ad kismen uyumlu.{duplicate_note}"
        elif best_similarity >= 0.72:
            status = "KISMEN_ESLESME"
            detail = (
                f"{code} kodu eslesti, ad benzerligi "
                f"%{int(best_similarity * 100)}.{duplicate_note}"
            )
        else:
            status = "KOD_ESLESTI_ISIM_FARKLI"
            detail = (
                f"{code} kodu eslesti, ad farkli. "
                f"Benzerlik %{int(best_similarity * 100)}.{duplicate_note}"
            )

        return CompareResult(
            code=code,
            bddk_code=code,
            sql_code=code,
            bddk_name=bddk_name,
            sql_name=sql_name,
            status=status,
            detail=detail.strip(),
            similarity=best_similarity,
        )

    @staticmethod
    def _sort_key(code: str) -> tuple[int, int | str, str]:
        if code.isdigit():
            return (0, int(code), code)
        return (1, code, code)

    @staticmethod
    def _name_similarity(bddk_name: str, sql_name: str) -> float:
        return SequenceMatcher(None, bddk_name, sql_name).ratio()
