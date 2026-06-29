# COA - BDDK Karsilastirma

Excel'deki hesap planini MS SQL tablosuna basar, sorguyu dis dosyadan okur ve BDDK Tekduzen Hesap Plani ile karsilastirir.

## 1) SQL kurulumu

SSMS'te sirayla calistirin:

1. `sql/01_create_table.sql`
2. `sql/02_insert_data.sql`

Daha once unique index ile tablo olusturduysaniz ve duplicate key hatasi aldiysaniz:

1. `sql/01b_fix_duplicate_index.sql`
2. `sql/02_insert_data.sql`

Not: Kaynak Excel'de 96 hesap kodu farkli isimlerle tekrar ediyor (192 satir).
Bu normal banka COA durumu oldugu icin tabloda unique index yoktur.
Tekrar eden kodlar: `data/duplicate_ledgercodes.csv`

Veriyi yeniden uretmek icin:

```powershell
python tools/generate_insert_sql.py
```

## 2) Config

`config.json` icinde SQL baglanti bilgilerini duzenleyin:

```json
{
  "sql_server": "localhost",
  "database": "CoaCompare",
  "trusted_connection": true
}
```

## 3) Sorgu dosyasi (degistirilebilir)

Uygulama her calistirmada su dosyayi okur:

`queries/coa_query.sql`

Ornek varsayilan sorgu:

```sql
SELECT Ledgercode, Ledgername
FROM dbo.CoaLedger
ORDER BY Ledgercode;
```

Canli ortam icin dosyayi su sekilde degistirmeniz yeterli:

```sql
SELECT Ledgercode, Ledgername
FROM boa.acc.coa;
```

Sorgu sonucunda en az su kolonlar olmali: `Ledgercode`, `Ledgername`
(Kolon adlari config.json'dan da degistirilebilir.)

## 4) Uygulamayi calistirma

```powershell
cd C:\Users\mesut\Projects\coa-bddk-karsilastirma
python -m pip install -r requirements.txt
python src\main.py
```

## 5) EXE uretme

```powershell
build.bat
```

Uretilen dosya: `dist\CoaBddkCompare.exe`

EXE ile birlikte ayni klasorde su dosyalar kalmali:

- `config.json`
- `queries\coa_query.sql`
- `data\bddk_reference.json`

## Durum kodlari

- `TAM_ESLESME`: Kod ve ad BDDK ile uyumlu
- `KISMEN_ESLESME`: Kod eslesti, ad kismen uyumlu
- `KOD_ESLESTI_ISIM_FARKLI`: Kod eslesti, ad farkli
- `KOD_UZANTISI`: Banka alt hesap kodu, BDDK ust hesabi ile eslesti
- `KOD_BULUNAMADI`: BDDK'da karsilik yok
