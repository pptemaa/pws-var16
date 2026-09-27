@echo off
set PYTHONPATH=src
if "%1"=="repl" (
    python src\repl.py
) else if "%1"=="server" (
    python src\server.py %2 %3
) else if "%1"=="client" (
    python src\client.py %2 %3
) else if "%1"=="test" (
    python -m unittest discover -s tests -v
) else if "%1"=="lint" (
    python -m flake8 --max-line-length=80 src tests
) else (
    echo Usage: run.bat repl^|server^|client^|test^|lint
)
