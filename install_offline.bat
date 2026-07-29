@echo off
REM Kurumsal / Task Scheduler sunucusu: internet olmadan pyodbc + pypdf kur
setlocal EnableExtensions
cd /d "%~dp0"

set "PY=python"
where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [HATA] Python bulunamadi.
        pause
        exit /b 1
    )
    set "PY=py -3"
)

echo Python:
%PY% --version
echo.
echo Offline wheel'lerden kurulum: vendor\wheels
echo.

%PY% -m pip install --no-index --find-links="%~dp0vendor\wheels" --user pyodbc pypdf
if errorlevel 1 (
    echo [HATA] Yerel kurulum basarisiz.
    echo        vendor\wheels icinde su dosyalar olmali:
    echo          - pypdf-*-py3-none-any.whl
    echo          - pyodbc-*-cp311-cp311-win_amd64.whl  ^(Python 3.11 icin^)
    pause
    exit /b 1
)

echo.
%PY% -c "import pyodbc, pypdf; print('OK pyodbc', pyodbc.version); print('OK pypdf', pypdf.__version__)"
if errorlevel 1 (
    echo [HATA] Import basarisiz.
    pause
    exit /b 1
)

echo.
echo Kurulum tamam.
pause
endlocal
