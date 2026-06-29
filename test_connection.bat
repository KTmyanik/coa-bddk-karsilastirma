@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ODBC surucu kontrolu...
python -c "import pyodbc; drivers=[d for d in pyodbc.drivers() if 'SQL Server' in d]; print('Bulunan suruculer:', drivers or 'YOK'); exit(0 if drivers else 1)"
if errorlevel 1 (
    echo.
    echo [UYARI] SQL Server ODBC surucusu bulunamadi.
    echo Indirin: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
    echo.
)

echo.
echo Config:
type config.json
echo.
echo Baglanti:
type connection.json
echo.
echo SQL baglanti testi...
python -c "
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path('src')))
from config_loader import load_config
from sql_loader import load_coa_from_sql
cfg = load_config(Path('config.json'))
records, _ = load_coa_from_sql(cfg)
print(f'OK: {len(records)} kayit okundu')
"
if errorlevel 1 (
    echo [HATA] SQL baglantisi basarisiz. config.json degerlerini kontrol edin.
) else (
    echo [OK] SQL baglantisi calisiyor.
)

echo.
pause
