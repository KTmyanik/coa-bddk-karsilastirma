@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo === Git durum ===
git status
echo.

echo === Degisiklikler ekleniyor ===
git add -A
git status
echo.

echo === Commit ===
git commit -m "Update BDDK source to DokumanGetir/1334 with PDF parse and refresh on compare"
if errorlevel 1 (
  echo Commit atlandi veya basarisiz. (Degisiklik yoksa normaldir.)
)

echo.
echo === Push ===
git push -u origin main
if errorlevel 1 (
  echo.
  echo Push basarisiz. Remote kontrol:
  git remote -v
  echo.
  echo Gerekirse:
  echo   git remote add origin https://github.com/KULLANICI/coa-bddk-karsilastirma.git
  echo   git push -u origin main
)

echo.
pause
