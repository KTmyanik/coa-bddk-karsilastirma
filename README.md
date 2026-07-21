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

## 2) Baglanti ayarlari

SQL baglantisi **`connection.json`** dosyasindan okunur. Uygulama her acilista bu dosyayi yeniden yukler.

Varsayilan:

```json
{
  "sql_server": "PASIFIK",
  "database": "TDUTIL",
  "trusted_connection": true,
  "username": "",
  "password": "",
  "command_timeout_seconds": 120
}
```

Baska bilgisayarda sadece `connection.json` duzenlemeniz yeterli.
Windows Authentication disinda kullanici adi/sifre icin:

```json
{
  "sql_server": "SUNUCU",
  "database": "TDUTIL",
  "trusted_connection": false,
  "username": "kullanici",
  "password": "sifre",
  "command_timeout_seconds": 120
}
```

Uygulama icinden **Baglanti Ac** butonu ile de duzenleyebilirsiniz.

BDDK dokumani PDF ise (DokumanGetir/1334 gibi) uygulama `pypdf` ile metni cikarir.
Cache dosyasini yeniden uretmek icin:

```powershell
python tools/refresh_bddk_cache.py
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
run.bat
```

veya:

```powershell
python -m pip install -r requirements.txt
python src\main.py
```

### Baska bilgisayarda / kurumsal agda calistirma

PyPI'ye erisim yoksa (SSL / timeout), proje icindeki offline wheel kullanilir:

- `vendor\wheels\pypdf-*.whl`

`run.bat` once yerel wheel'den kurar, internete ihtiyac duymaz.

Elle kurulum:

```powershell
py -m pip install --no-index --find-links=vendor\wheels pypdf
```

1. Tum proje klasorunu kopyalayin (en az: `src\`, `data\`, `queries\`, `vendor\`, `config.json`, `connection.json`, `requirements.txt`, `run.bat`)
2. Python 3.10+ kurulu olmali
3. `connection.json` icinde `sql_server` ve `database` degerlerini o bilgisayara gore duzenleyin
4. **ODBC Driver 17 for SQL Server** kurulu olmali
5. `run.bat` calistirin
6. SQL testi icin: `test_connection.bat`

Gelistirme / EXE icin ek paketler:

```powershell
python -m pip install -r requirements-dev.txt
```

## 5) EXE uretme

```powershell
build.bat
```

Uretilen dosya: `dist\CoaBddkCompare.exe`

EXE ile birlikte ayni klasorde su dosyalar kalmali:

- `config.json`
- `connection.json`
- `queries\coa_query.sql`
- `data\bddk_reference.json`

## Durum kodlari

- `TAM_ESLESME`: Kod ve ad BDDK ile uyumlu
- `KISMEN_ESLESME`: Kod eslesti, ad kismen uyumlu
- `KOD_ESLESTI_ISIM_FARKLI`: Kod eslesti, ad farkli
- `SADECE_BDDK`: Sadece BDDK/PDF tarafinda var
- `SADECE_COA`: Sadece sorgu/COA tarafinda var

Siralama: BDDK (PDF) dokumanindaki sira korunur. COA'da olup PDF'te olmayan kodlar,
ust hesap hiyerarsisine gore uygun yere yerlestirilir.

PDF parse: cok satira bolunmus hesap adlari birlestirilir; kod ile ad ayri satirdaysa
eslestirilir; PDF'nin kod icine bastigi bosluklar temizlenir.