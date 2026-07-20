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

echo [2/4] Bagimliliklar kuruluyor...
REM Once offline wheel'lerden dene (kurumsal ag / SSL sorunu icin)
if exist "vendor\wheels\*.whl" (
    echo       Offline wheel klasoru bulundu, yerel kurulum deneniyor...
    %PY% -m pip install --no-index --find-links="vendor\wheels" pypdf
    if errorlevel 1 (
        echo       Yerel pypdf kurulumu basarisiz, internet denenecek...
    ) else (
        echo       pypdf yerel wheel'den kuruldu.
    )
)

REM pyodbc zaten kurulu olabilir; yoksa internet/trusted-host ile dene
%PY% -c "import pyodbc" >nul 2>&1
if errorlevel 1 (
    echo       pyodbc kuruluyor...
    %PY% -m pip install pyodbc --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org
    if errorlevel 1 (
        echo [HATA] pyodbc kurulamadi.
        goto :fail
    )
) else (
    echo       pyodbc hazir.
)

%PY% -c "import pypdf" >nul 2>&1
if errorlevel 1 (
    echo       pypdf internetten deneniyor...
    %PY% -m pip install pypdf --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org
    if errorlevel 1 (
        echo [HATA] pypdf kurulamadi.
        echo        vendor\wheels icinde pypdf*.whl olmali.
        echo        veya baska bilgisayardan wheel kopyalayin.
        goto :fail
    )
) else (
    echo       pypdf hazir.
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
echo 4. pypdf icin vendor\wheels klasorunu projeyle birlikte kopyalayin
echo 5. Manuel test:  %PY% src\main.py
echo.

:end
pause
endlocal
