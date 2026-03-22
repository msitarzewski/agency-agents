@echo off
title Charity Coin Launcher
color 0A

echo ============================================
echo   Charity Coin - One-Click Launcher
echo ============================================
echo.

:: -------------------------------------------------------------------
:: Check Node.js
:: -------------------------------------------------------------------
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERROR] Node.js is not installed.
    echo.
    echo Please install it first:
    echo   1. Go to https://nodejs.org
    echo   2. Download the LTS version
    echo   3. Run the installer (click Next through everything)
    echo   4. Restart your computer
    echo   5. Double-click this file again
    echo.
    pause
    exit /b 1
)
echo [OK] Node.js found

:: -------------------------------------------------------------------
:: Check Docker
:: -------------------------------------------------------------------
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERROR] Docker is not installed.
    echo.
    echo Please install it first:
    echo   1. Go to https://docs.docker.com/desktop/install/windows-install/
    echo   2. Download and install Docker Desktop
    echo   3. Open Docker Desktop and wait for it to start
    echo   4. Double-click this file again
    echo.
    pause
    exit /b 1
)

docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0E
    echo [WARNING] Docker is installed but not running.
    echo Starting Docker Desktop... please wait...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Waiting 30 seconds for Docker to start...
    timeout /t 30 /nobreak >nul
    docker info >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        color 0C
        echo [ERROR] Docker still not ready. Please open Docker Desktop manually,
        echo         wait until the whale icon in your taskbar stops animating,
        echo         then double-click this file again.
        echo.
        pause
        exit /b 1
    )
)
echo [OK] Docker is running

:: -------------------------------------------------------------------
:: Set up environment files (only if they don't exist)
:: -------------------------------------------------------------------
echo.
echo [SETUP] Preparing environment files...

if not exist ".env" (
    copy ".env.example" ".env" >nul 2>&1
    echo   Created .env
) else (
    echo   .env already exists - skipping
)

if not exist "apps\api\.env" (
    :: Create a working API env file with correct DB credentials
    (
        echo PORT=3001
        echo DATABASE_URL=postgresql://charity:charity@localhost:5432/charity_coin
        echo REDIS_URL=redis://localhost:6379
        echo BASE_RPC_URL=https://mainnet.base.org
        echo ADMIN_API_KEY=local-dev-key
        echo CONVERSION_ENGINE_ADDRESS=0x0000000000000000000000000000000000000000
        echo FEE_ROUTER_ADDRESS=0x0000000000000000000000000000000000000000
        echo CAUSE_TOKEN_FACTORY_ADDRESS=0x0000000000000000000000000000000000000000
        echo CHA_TOKEN_ADDRESS=0x0000000000000000000000000000000000000000
        echo INDEXER_START_BLOCK=0
    ) > "apps\api\.env"
    echo   Created apps\api\.env
) else (
    echo   apps\api\.env already exists - skipping
)

if not exist "apps\web\.env.local" (
    (
        echo NEXT_PUBLIC_API_URL=http://localhost:3001/api
        echo NEXT_PUBLIC_BASE_RPC_URL=https://mainnet.base.org
        echo NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=
    ) > "apps\web\.env.local"
    echo   Created apps\web\.env.local
) else (
    echo   apps\web\.env.local already exists - skipping
)

:: -------------------------------------------------------------------
:: Install dependencies
:: -------------------------------------------------------------------
echo.
echo [INSTALL] Installing dependencies (this may take a minute)...
call npm install
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERROR] npm install failed. Check the errors above.
    pause
    exit /b 1
)
echo [OK] Dependencies installed

:: -------------------------------------------------------------------
:: Start database and Redis
:: -------------------------------------------------------------------
echo.
echo [DOCKER] Starting PostgreSQL and Redis...
docker compose up -d postgres redis
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERROR] Failed to start Docker services.
    echo Make sure Docker Desktop is running.
    pause
    exit /b 1
)

echo Waiting for database to be ready...
timeout /t 8 /nobreak >nul
echo [OK] Database and Redis started

:: -------------------------------------------------------------------
:: Set up database schema and seed data
:: -------------------------------------------------------------------
echo.
echo [DATABASE] Setting up database schema...
cd apps\api
call npx drizzle-kit push 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Database schema push had issues - may already be set up
)

echo [DATABASE] Seeding sample data...
call npx tsx src/db/seed.ts 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Seeding had issues - data may already exist
)
cd ..\..

:: -------------------------------------------------------------------
:: Launch the app
:: -------------------------------------------------------------------
echo.
echo ============================================
echo   STARTING CHARITY COIN
echo ============================================
echo.
echo   Web App:    http://localhost:3000
echo   API:        http://localhost:3001
echo.
echo   Opening your browser in 10 seconds...
echo   (Keep this window open to keep the app running)
echo   (Press Ctrl+C to stop)
echo.

:: Open browser after a delay
start "" cmd /c "timeout /t 10 /nobreak >nul && start http://localhost:3000"

:: Start the dev servers (this keeps running)
call npx turbo run dev
