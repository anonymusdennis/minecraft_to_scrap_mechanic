@echo off
setlocal ENABLEDELAYEDEXPANSION

REM ===================================
REM Quick Schematic to Blueprint Converter
REM Usage: schematic_to_blue.bat <schematic_file>
REM ===================================

if "%~1"=="" (
    echo Usage: schematic_to_blue.bat ^<schematic_file^>
    echo Example: schematic_to_blue.bat 6901.schematic
    exit /b 1
)

set "SCHEMATIC_FILE=%~1"
set "ASSETS_DIR=.\MyResourcePack\assets"
set "OUTPUT_DIR=.\assembled_blueprints"

REM Extract filename without extension for blueprint name
set "BLUEPRINT_NAME=%~n1"

echo ===================================
echo Converting: %SCHEMATIC_FILE%
echo ===================================
echo.

REM Check if schematic file exists
if not exist "%SCHEMATIC_FILE%" (
    echo Error: Schematic file not found: %SCHEMATIC_FILE%
    exit /b 1
)

REM Check if assets directory exists
if not exist "%ASSETS_DIR%" (
    echo Error: Assets directory not found: %ASSETS_DIR%
    echo Please extract a Minecraft resource pack to %ASSETS_DIR%
    exit /b 1
)

REM Step 1: Convert schematic to JSON
echo [1/2] Converting schematic to JSON...
python schematic_to_json.py "%SCHEMATIC_FILE%"
if errorlevel 1 (
    echo Error: Failed to convert schematic to JSON
    exit /b 1
)

set "JSON_FILE=%SCHEMATIC_FILE:~0,-10%.json"
echo ✓ Created %JSON_FILE%
echo.

REM Step 2: Assemble blueprint with on-demand generation
echo [2/2] Assembling blueprint with on-demand generation...
REM Add --split flag for large builds (uncomment if needed)
python schematic_assembler.py "%JSON_FILE%" ^
    --assets "%ASSETS_DIR%" ^
    --generate-on-demand ^
    --output "%OUTPUT_DIR%" ^
    --name "%BLUEPRINT_NAME%" 
REM    --split ^
REM    --max-voxels-per-chunk 100000

if errorlevel 1 (
    echo Error: Failed to assemble blueprint
    exit /b 1
)

echo.
echo ===================================
echo Success!
echo ===================================
echo.
echo Blueprint saved to: %OUTPUT_DIR%
echo Blueprint name: %BLUEPRINT_NAME%
echo.
echo To install in Scrap Mechanic:
echo 1. Copy the UUID folder from %OUTPUT_DIR% to:
echo    %%AppData%%\Axolot Games\Scrap Mechanic\User\User_^<numbers^>\Blueprints
echo.
echo 2. Launch Scrap Mechanic and find '%BLUEPRINT_NAME%' in your blueprints
echo.
echo NOTE: For very large builds, edit this script to uncomment --split flag
echo       This will automatically divide the blueprint into manageable chunks
echo.
