# Offline wheel paketleri - kurumsal agda / Task Scheduler sunucusunda PyPI yoksa kullanilir.

Gerekli dosyalar (ornek):

- `pypdf-*-py3-none-any.whl`  (tum Python surumleri)
- `pyodbc-*-cp311-cp311-win_amd64.whl`  (Python 3.11, 64-bit Windows)
- `pyodbc-*-cp310-cp310-win_amd64.whl`  (Python 3.10)
- `pyodbc-*-cp312-cp312-win_amd64.whl`  (Python 3.12)

Kurulum:

```bat
install_offline.bat
```

veya `run.bat` / `run_auto.bat` otomatik olarak bu klasorden kurmayi dener.

Not: `pyodbc` binary pakettir; sunucudaki Python surumu (3.10/3.11/3.12) ile wheel eslesmelidir.
Ayrica sunucuda **ODBC Driver 17 for SQL Server** kurulu olmali.
