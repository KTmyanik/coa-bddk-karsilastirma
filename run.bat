@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================
echo   COA - BDDK Karsilastirma
echo ============================================
echo.

REM Python bul
set "PY=python"
where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [HATA] Python bulunamadi.
        echo        https://www.python.org/downloads/ adresinden kurun.
        echo        Kurulumda "Add Python to PATH" secenegini isaretleyin.
        goto :fail
    )
    set "PY=py -3"
)

echo [1/4] Python:
%PY% --version
if errorlevel 1 goto :fail
echo.

echo [2/4] Bagimliliklar kuruluyor (pyodbc, pypdf)...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
    echo [HATA] pip install basarisiz oldu.
    goto :fail
)
echo.

echo [3/4] Dosya kontrolu...
if not exist "src\main.py" (
    echo [HATA] src\main.py bulunamadi. Proje klasoru eksik olabilir.
    goto :fail
)
if not exist "data\bddk_reference.json" (
    echo [HATA] data\bddk_reference.json bulunamadi.
    echo        GitHub'dan indirdiginiz klasorde data\ klasoru olmali.
    goto :fail
)
if not exist "queries\coa_query.sql" (
    echo [HATA] queries\coa_query.sql bulunamadi.
    goto :fail
)
if not exist "config.json" (
    echo [HATA] config.json bulunamadi.
    goto :fail
)
if not exist "connection.json" (
    echo [HATA] connection.json bulunamadi.
    echo        connection.example.json dosyasini kopyalayip duzenleyin.
    goto :fail
)
echo       Gerekli dosyalar tamam.
echo.

echo [4/4] Uygulama aciliyor...
echo       (Pencere acilmazsa asagidaki hata mesajina bakin)
echo.
%PY% src\main.py
set "APP_EXIT=%ERRORLEVEL%"
echo.

if not "%APP_EXIT%"=="0" (
    echo [HATA] Uygulama hata ile kapandi. Kod: %APP_EXIT%
    goto :fail
)

echo Uygulama normal sekilde kapandi.
goto :end

:fail
echo.
echo --- Cozum onerileri ---
echo 1. connection.json icinde sql_server ve database degerlerini duzenleyin
echo 2. queries\coa_query.sql dosyasindaki sorguyu kontrol edin
echo 3. SQL icin "ODBC Driver 17 for SQL Server" kurulu olmali
echo 4. Manuel test:  %PY% src\main.py
echo.

:end
pause
endlocal
