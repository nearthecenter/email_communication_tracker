@echo off
REM Batch script to run the email tracker using the onit-oauth environment

REM Find python in onit-oauth lib directory
set PYTHON=python3.12

REM Try to run with the python from PATH
%PYTHON% "%~dp0run_email_tracker.py" %*

REM If that fails, try with the full path
if errorlevel 1 (
    echo Trying to locate python in onit-oauth environment...
    if exist "%~dp0onit-oauth\bin\python" (
        "%~dp0onit-oauth\bin\python" "%~dp0run_email_tracker.py" %*
    ) else (
        echo Error: Could not find python interpreter
        exit /b 1
    )
)
