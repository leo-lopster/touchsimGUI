@echo off
setlocal enabledelayedexpansion

ECHO Welcome to TouchSim GUI!

REM Get the directory where this batch file is located
cd /d "%~dp0"

REM Find conda executable in common installation paths
set CONDA_EXE=
if exist "%ProgramFiles%\miniconda3\Scripts\conda.exe" (
    set CONDA_EXE=%ProgramFiles%\miniconda3\Scripts\conda.exe
) else if exist "%ProgramFiles%\anaconda3\Scripts\conda.exe" (
    set CONDA_EXE=%ProgramFiles%\anaconda3\Scripts\conda.exe
) else if exist "%UserProfile%\miniconda3\Scripts\conda.exe" (
    set CONDA_EXE=%UserProfile%\miniconda3\Scripts\conda.exe
) else if exist "%UserProfile%\anaconda3\Scripts\conda.exe" (
    set CONDA_EXE=%UserProfile%\anaconda3\Scripts\conda.exe
) else (
    REM Try to use conda from PATH
    for /f "delims=" %%i in ('where conda 2^>nul') do set CONDA_EXE=%%i
)

if "!CONDA_EXE!"=="" (
    ECHO Error: Conda not found. Please ensure Anaconda or Miniconda is installed.
    pause
    exit /b 1
)

ECHO Building Environment from environment.yml...
call "!CONDA_EXE!" env create -f environment.yml --yes

ECHO Activating tsgui environment...
call "!CONDA_EXE!" activate tsgui

ECHO Starting GUI...
python touchsim_gui.py

pause
endlocal