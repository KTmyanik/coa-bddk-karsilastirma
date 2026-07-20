@echo off
REM myanik / kurumsal PC: internet olmadan pypdf kur
cd /d "%~dp0"
py -3 -m pip install --no-index --find-links="%~dp0vendor\wheels" pypdf
if errorlevel 1 (
  python -m pip install --no-index --find-links="%~dp0vendor\wheels" pypdf
)
echo.
py -3 -c "import pypdf; print('OK pypdf', pypdf.__version__)" 2>nul || python -c "import pypdf; print('OK pypdf', pypdf.__version__)"
pause
