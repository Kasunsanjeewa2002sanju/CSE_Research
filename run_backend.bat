@echo off
REM ============================================================================
REM CSE Research & Live Engine - Unified Backend Launcher
REM ============================================================================
cd /d "%~dp0cse_research"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" run_backend.py %*
