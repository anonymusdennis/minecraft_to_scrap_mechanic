@echo off
setlocal ENABLEDELAYEDEXPANSION

echo ===================================
echo Minecraft to Scrap Mechanic Converter
echo ===================================
echo.

REM Configuration
set "SCHEMATIC_FILE=6901.schematic"
set "ASSETS_DIR=.\MyResourcePack\assets"
set "BLUEPRINTS_DIR=.\generated_blueprints"
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

REM Step 2: Generate block blueprints
echo Step 2: Generating block blueprints...

if not exist "%ASSETS_DIR%" (
    echo ✗ Assets directory not found: %ASSETS_DIR%
    echo   Please extract a Minecraft resource pack to this location.
    goto :error
)

echo   Generating main blueprints...
python main.py -i "%ASSETS_DIR%" -o "%BLUEPRINTS_DIR%"
if errorlevel 1 goto :error

echo   Generating essential blocks...
python generate_essential_blueprints.py "%ASSETS_DIR%" "%BLUEPRINTS_DIR%"
if errorlevel 1 goto :error

REM Count files in BLUEPRINTS_DIR
for /f %%A in ('dir /b "%BLUEPRINTS_DIR%" ^| find /v /c ""') do set "BLUEPRINT_COUNT=%%A"
echo ✓ Generated %BLUEPRINT_COUNT% blueprints
echo.

REM Step 3: Assemble the large blueprint
echo Step 3: Assembling schematic into large blueprint...

if not exist "%JSON_FILE%" (
    echo ✗ JSON file not found: %JSON_FILE%
    goto :error
)

python schematic_assembler.py "%JSON_FILE%" ^
    --blueprints "%BLUEPRINTS_DIR%" ^
    --output "%OUTPUT_DIR%" ^
    --name "%BLUEPRINT_NAME%"
    --hollow
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
echo    %%AppData%%\Axolot Games\Scrap Mechanic\User\User_<numbers>\Blueprints
echo.
echo 2. Copy the UUID folder from:
echo    %OUTPUT_DIR%
echo.
echo 3. Launch Scrap Mechanic and find '%BLUEPRINT_NAME%' in your blueprints
echo.

goto :eof

:error
echo.
echo Script aborted due to an error.
exit /b 1
