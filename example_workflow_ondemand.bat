@echo off
setlocal ENABLEDELAYEDEXPANSION

echo ===================================
echo Minecraft to Scrap Mechanic Converter
echo Fast On-Demand Workflow
echo ===================================
echo.

REM Configuration
set "SCHEMATIC_FILE=6901.schematic"
set "ASSETS_DIR=.\MyResourcePack\assets"
set "OUTPUT_DIR=.\assembled_blueprints"
set "BLUEPRINT_NAME=MyBuilding"

REM Step 1: Convert schematic to JSON
echo Step 1: Converting schematic to JSON...

if exist "%SCHEMATIC_FILE%" (
    python schematic_to_json.py "%SCHEMATIC_FILE%"
    if errorlevel 1 goto :error

    REM Replace .schematic with .json (".schematic" is 10 chars)
    set "JSON_FILE=%SCHEMATIC_FILE:~0,-10%.json"
    echo ✓ Created !JSON_FILE!
) else (
    echo ✗ Schematic file not found: %SCHEMATIC_FILE%
    echo   Using existing JSON file if available...
    set "JSON_FILE=%SCHEMATIC_FILE:~0,-10%.json"
)
echo.

REM Step 2: Verify assets directory
echo Step 2: Checking assets directory...

if not exist "%ASSETS_DIR%" (
    echo ✗ Assets directory not found: %ASSETS_DIR%
    echo   Please extract a Minecraft resource pack to this location.
    goto :error
)
echo ✓ Assets directory found
echo.

REM Step 3: Assemble with on-demand generation
echo Step 3: Assembling schematic with on-demand block generation...

if not exist "%JSON_FILE%" (
    echo ✗ JSON file not found: %JSON_FILE%
    goto :error
)

python schematic_assembler.py "%JSON_FILE%" ^
    --assets "%ASSETS_DIR%" ^
    --generate-on-demand ^
    --output "%OUTPUT_DIR%" ^
    --name "%BLUEPRINT_NAME%"
if errorlevel 1 goto :error

echo.
echo ===================================
echo Conversion complete!
echo ===================================
echo.
echo Your blueprint is ready to use in Scrap Mechanic!
echo.
echo To install:
echo 1. Open File Explorer and navigate to:
echo    %%AppData%%\Axolot Games\Scrap Mechanic\User\User_^<numbers^>\Blueprints
echo.
echo 2. Copy the UUID folder from:
echo    %OUTPUT_DIR%
echo.
echo 3. Launch Scrap Mechanic and find '%BLUEPRINT_NAME%' in your blueprints
echo.
echo Note: This workflow uses on-demand block generation, which is much faster
echo than pre-generating all blocks. Blocks are generated as needed and cached.
echo.

goto :eof

:error
echo.
echo Script aborted due to an error.
exit /b 1
