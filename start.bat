@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%code"
set "FRONTEND_DIR=%ROOT%Frontend"

set "PYTHON_EXE=%BACKEND_DIR%\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=%BACKEND_DIR%\venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Could not find a backend virtual environment.
    echo Expected python at:
    echo   %BACKEND_DIR%\.venv\Scripts\python.exe
    echo   %BACKEND_DIR%\venv\Scripts\python.exe
    echo Create a venv inside the backend folder and install dependencies.
    goto :end
)

echo Starting ProcureWise Application...
echo Backend Python: %PYTHON_EXE%
echo.

echo Starting Backend Server on port 8001...
start "ProcureWise Backend" /D "%BACKEND_DIR%" "%PYTHON_EXE%" -m uvicorn app_entegris:app --reload --host 0.0.0.0 --port 8001

timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "ProcureWise Frontend" /D "%FRONTEND_DIR%" npm run dev

timeout /t 5 /nobreak >nul

echo Opening browser at http://localhost:3000 ...
start http://localhost:3000

echo.
echo Backend running on  http://localhost:8001
echo Frontend running on http://localhost:3000
echo Servers keep running in their own windows. You can close this window.
pause

:end
endlocal

