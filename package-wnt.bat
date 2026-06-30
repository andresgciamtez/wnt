@echo off
setlocal

set "REPO=%~dp0"
set "PLUGIN_DIR=%REPO%wnt"
set "CONDA_BAT=%USERPROFILE%\miniconda3\condabin\conda.bat"
set "CONDA_ACTIVATE=%USERPROFILE%\miniconda3\Scripts\activate.bat"

if /I not "%CONDA_DEFAULT_ENV%"=="wnt" (
  if exist "%CONDA_BAT%" (
    call "%CONDA_BAT%" activate wnt
  ) else if exist "%CONDA_ACTIVATE%" (
    call "%CONDA_ACTIVATE%" wnt
  ) else (
    echo Could not find conda.bat. Open an Anaconda Prompt or update CONDA_BAT in this script.
    exit /b 1
  )
  if errorlevel 1 exit /b %errorlevel%
)

if not defined CONDA_PREFIX (
  echo CONDA_PREFIX is not defined. Activate the wnt conda environment first.
  exit /b 1
)

set "CONDAENV=%CONDA_PREFIX%"
set "PYTHONHOME="
set "PATH=%CONDAENV%;%CONDAENV%\Library\bin;%CONDAENV%\Scripts;C:\Program Files\7-Zip;%PATH%"

where pb_tool >nul 2>nul
if errorlevel 1 (
  echo pb_tool.exe not found in the wnt conda environment.
  exit /b 1
)

where 7z >nul 2>nul
if errorlevel 1 (
  echo 7z.exe not found in PATH. Install 7-Zip or update this script with its location.
  exit /b 1
)

cd /d "%PLUGIN_DIR%"
if errorlevel 1 exit /b %errorlevel%

pb_tool validate
if errorlevel 1 exit /b %errorlevel%

pb_tool deploy -y
if errorlevel 1 exit /b %errorlevel%

pb_tool zip -q
if errorlevel 1 exit /b %errorlevel%

echo.
echo Package created: %PLUGIN_DIR%\wnt.zip
endlocal
