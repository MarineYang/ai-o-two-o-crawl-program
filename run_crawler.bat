@echo off


if "%1"=="" (
    echo Please provide a store name.
    exit /b
)

cd /d %~dp0

python main.py "%1"

pause
