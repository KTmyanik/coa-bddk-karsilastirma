from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from bddk_loader import BddkAccount
from config_loader import normalize_for_exact, normalize_text
from name_repair import repair_accounts
from sql_loader import CoaRecord

# Benzerlik baremi (SequenceMatcher ratio):
# >= PARTIAL_THRESHOLD -> KISMEN_ESLESME
# <  PARTIAL_THRESHOLD -> KOD_ESLESTI_ISIM_FARKLI
# TAM_ESLESME sadece normalize_for_exact ile birebir (%100) esitlikte.
PARTIAL_THRESHOLD = 0.72


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
        # PDF sirasi korunur
        self._bddk_accounts = list(bddk_accounts)
        self._bddk_by_code: dict[str, str] = {
            account.code: account.name for account in bddk_accounts
        }
        self._pdf_order: list[str] = [account.code for account in bddk_accounts]

    def compare_all(self, records: list[CoaRecord]) -> list[CompareResult]:
        sql_by_code: dict[str, list[str]] = {}
        for record in records:
            names = sql_by_code.setdefault(record.code, [])
            if record.name not in names:
                names.append(record.name)

        # SQL'deki dogru yazilmis adlari sozluk olarak kullanip
        # PDF kaynakli bosluk hatalarini (DAY ANAN, AYBEKLENEN vb.) onar
        vocab_names = [name for names in sql_by_code.values() for name in names]
        repaired = repair_accounts(self._bddk_accounts, vocab_names)
        self._bddk_by_code = {account.code: account.name for account in repaired}

        ordered_codes = self._build_ordered_codes(set(sql_by_code.keys()))
        return [self._compare_code(code, sql_by_code) for code in ordered_codes]

    def _build_ordered_codes(self, sql_codes: set[str]) -> list[str]:
        """PDF sirasini baz al; COA-only kodlari hiyerarsik olarak uygun yere yerlestir."""
        ordered = list(self._pdf_order)
        present = set(ordered)

        coa_only = [code for code in sql_codes if code not in present]
        # Once kisa kodlar (ust hesap), sonra uzunlar
        coa_only.sort(key=lambda code: (len(code), code))

        for code in coa_only:
            index = self._find_insert_index(ordered, code)
            ordered.insert(index, code)
            present.add(code)

        return ordered

    def _find_insert_index(self, ordered: list[str], code: str) -> int:
        parent = ""
        parent_idx = -1
        for index, candidate in enumerate(ordered):
            if code.startswith(candidate) and len(candidate) > len(parent):
                parent = candidate
                parent_idx = index

        if parent_idx >= 0:
            index = parent_idx + 1
            while index < len(ordered):
                current = ordered[index]
                if not current.startswith(parent):
                    break
                if current.startswith(code):
                    return index
                if code.startswith(current):
                    index += 1
                    continue
                if self._hierarchy_key(current) < self._hierarchy_key(code):
                    index += 1
                    continue
                return index
            return index

        # Ust hesap PDF'te yoksa genel siraya yerlestir
        key = self._hierarchy_key(code)
        for index, current in enumerate(ordered):
            if self._hierarchy_key(current) > key:
                return index
        return len(ordered)

    @staticmethod
    def _hierarchy_key(code: str) -> tuple:
        # Sayisal hiyerarsi + orijinal string (esitlikte kararli)
        if code.isdigit():
            return (0, int(code), len(code), code)
        return (1, code, len(code), code)

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
        exact_bddk = normalize_for_exact(bddk_name)
        exact_sql = [normalize_for_exact(name) for name in sql_names]
        soft_bddk = normalize_text(bddk_name)
        soft_sql = [normalize_text(name) for name in sql_names]

        best_similarity = 0.0
        for soft_name in soft_sql:
            similarity = self._name_similarity(soft_bddk, soft_name)
            if similarity > best_similarity:
                best_similarity = similarity

        sql_name = " | ".join(sql_names)
        duplicate_note = ""
        if len(sql_names) > 1:
            duplicate_note = f" Sorguda {len(sql_names)} farkli hesap adi var."

        if not exact_bddk and not soft_bddk:
            status = "KOD_ESLESTI_ISIM_YOK"
            detail = f"{code} kodu her iki tarafta var, BDDK adi bos.{duplicate_note}"
        elif any(name == exact_bddk for name in exact_sql):
            # Noktalama dahil birebir eslesme (Turkce karakter katlamasi serbest)
            status = "TAM_ESLESME"
            detail = f"{code} kodu ve adi her iki tarafta uyumlu.{duplicate_note}"
            best_similarity = 1.0
        elif soft_bddk and any(name == soft_bddk for name in soft_sql):
            # Harfler ayni, noktalama / tire / virgul farkli
            status = "KISMEN_ESLESME"
            detail = (
                f"{code} kodu eslesti, harfler uyumlu fakat noktalama veya "
                f"yazim farki var.{duplicate_note}"
            )
            best_similarity = 1.0
        elif any(
            name.startswith(soft_bddk) or soft_bddk.startswith(name)
            for name in soft_sql
            if name and soft_bddk
        ):
            status = "KISMEN_ESLESME"
            detail = f"{code} kodu eslesti, ad kismen uyumlu.{duplicate_note}"
        elif best_similarity >= PARTIAL_THRESHOLD:
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
    def _name_similarity(bddk_name: str, sql_name: str) -> float:
        return SequenceMatcher(None, bddk_name, sql_name).ratio()
