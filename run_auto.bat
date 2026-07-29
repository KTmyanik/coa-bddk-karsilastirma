@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================
echo   COA - BDDK Otomatik Karsilastirma
echo ============================================
echo.

set "PY=python"
where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [HATA] Python bulunamadi.
        goto :fail
    )
    set "PY=py -3"
)

if not exist "src\auto_compare.py" (
    echo [HATA] src\auto_compare.py bulunamadi.
    goto :fail
)
if not exist "config.json" (
    echo [HATA] config.json bulunamadi.
    goto :fail
)
if not exist "connection.json" (
    echo [HATA] connection.json bulunamadi.
    goto :fail
)

echo [1/2] Bagimliliklar ^(offline once^)...
if exist "vendor\wheels\*.whl" (
    %PY% -m pip install --no-index --find-links="vendor\wheels" --user pyodbc pypdf >nul 2>&1
)

%PY% -c "import pyodbc, pypdf" >nul 2>&1
if errorlevel 1 (
    echo [HATA] pyodbc veya pypdf eksik.
    echo        Once run.bat veya install_offline.bat calistirin.
    echo        vendor\wheels icinde pyodbc*-cp311-*-win_amd64.whl olmali.
    goto :fail
)
echo       pyodbc / pypdf hazir.
echo.

echo [2/2] Karsilastirma + Excel cikti...
echo.
%PY% src\auto_compare.py
set "APP_EXIT=%ERRORLEVEL%"
echo.

if not "%APP_EXIT%"=="0" (
    echo [HATA] Islem basarisiz. Kod: %APP_EXIT%
    echo        config.json icinde export_file yolunu kontrol edin.
    goto :fail
)

echo Islem tamamlandi, pencere kapanıyor.
timeout /t 2 /nobreak >nul
endlocal
exit /b 0

:fail
echo.
echo --- Cozum onerileri ---
echo 1. config.json -^> export_file yolunu duzenleyin
echo 2. connection.json SQL ayarlarini kontrol edin
echo 3. Offline kurulum: install_offline.bat
echo 4. Manuel:  %PY% src\auto_compare.py
echo.
REM Task Scheduler'da pause takilmasin diye sadece konsolda bekle
if "%COA_AUTO_NO_PAUSE%"=="1" (
    endlocal
    exit /b 1
)
pause
endlocal
exit /b 1
