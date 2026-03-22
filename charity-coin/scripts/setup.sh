#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Charity Coin - Local Development Setup
# =============================================================================
# This script sets up everything you need to run the project locally.
# Usage: ./scripts/setup.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "============================================"
echo "  Charity Coin - Local Setup"
echo "============================================"
echo ""

# ---------------------------------------------------------------------------
# 1. Check prerequisites
# ---------------------------------------------------------------------------
echo "[1/7] Checking prerequisites..."

missing=()

if ! command -v node &> /dev/null; then
  missing+=("node (https://nodejs.org)")
else
  NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
  if [ "$NODE_VERSION" -lt 18 ]; then
    echo "  WARNING: Node.js >= 18 required, found $(node -v)"
    missing+=("node >= 18")
  else
    echo "  Node.js $(node -v)"
  fi
fi

if ! command -v npm &> /dev/null; then
  missing+=("npm")
else
  echo "  npm $(npm -v)"
fi

if ! command -v docker &> /dev/null; then
  missing+=("docker (https://docs.docker.com/get-docker/)")
else
  echo "  Docker $(docker --version | grep -oP '\d+\.\d+\.\d+')"
fi

if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
  missing+=("docker compose")
else
  echo "  Docker Compose available"
fi

# Foundry is optional for frontend/API dev
if command -v forge &> /dev/null; then
  echo "  Foundry (forge) $(forge --version 2>/dev/null | head -1 | grep -oP '\d+\.\d+\.\d+' || echo 'installed')"
elif [ -f "$HOME/.foundry/bin/forge" ]; then
  echo "  Foundry (forge) found at ~/.foundry/bin/forge"
  export PATH="$HOME/.foundry/bin:$PATH"
else
  echo "  Foundry not found (optional - needed for smart contract development)"
  echo "  Install: curl -L https://foundry.paradigm.xyz | bash && foundryup"
fi

if [ ${#missing[@]} -gt 0 ]; then
  echo ""
  echo "ERROR: Missing required tools:"
  for tool in "${missing[@]}"; do
    echo "  - $tool"
  done
  exit 1
fi

echo ""

# ---------------------------------------------------------------------------
# 2. Install Node dependencies
# ---------------------------------------------------------------------------
echo "[2/7] Installing Node.js dependencies..."
npm install
echo ""

# ---------------------------------------------------------------------------
# 3. Install Foundry dependencies (if forge available)
# ---------------------------------------------------------------------------
if command -v forge &> /dev/null || [ -f "$HOME/.foundry/bin/forge" ]; then
  echo "[3/7] Installing Foundry dependencies..."
  cd contracts
  forge install --no-git 2>/dev/null || forge install 2>/dev/null || echo "  Foundry deps already installed"
  cd "$PROJECT_DIR"
else
  echo "[3/7] Skipping Foundry dependencies (forge not installed)"
fi
echo ""

# ---------------------------------------------------------------------------
# 4. Set up environment files
# ---------------------------------------------------------------------------
echo "[4/7] Setting up environment files..."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "  Created .env from .env.example"
else
  echo "  .env already exists, skipping"
fi

if [ ! -f apps/api/.env ]; then
  cat > apps/api/.env << 'APIENV'
PORT=3001
DATABASE_URL=postgresql://charity:charity@localhost:5432/charity_coin
REDIS_URL=redis://localhost:6379
BASE_RPC_URL=https://mainnet.base.org
ADMIN_API_KEY=dev-admin-key-change-in-production
CONVERSION_ENGINE_ADDRESS=0x0000000000000000000000000000000000000001
FEE_ROUTER_ADDRESS=0x0000000000000000000000000000000000000002
CAUSE_TOKEN_FACTORY_ADDRESS=0x0000000000000000000000000000000000000003
CHA_TOKEN_ADDRESS=0x0000000000000000000000000000000000000004
INDEXER_START_BLOCK=0
ALLOWED_ORIGINS=http://localhost:3000
APIENV
  echo "  Created apps/api/.env with local dev defaults"
else
  echo "  apps/api/.env already exists, skipping"
fi

if [ ! -f apps/web/.env.local ]; then
  cat > apps/web/.env.local << 'WEBENV'
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=
NEXT_PUBLIC_API_URL=http://localhost:3001/api
NEXT_PUBLIC_BASE_RPC_URL=https://mainnet.base.org
WEBENV
  echo "  Created apps/web/.env.local with local dev defaults"
else
  echo "  apps/web/.env.local already exists, skipping"
fi

echo ""

# ---------------------------------------------------------------------------
# 5. Start infrastructure (PostgreSQL + Redis)
# ---------------------------------------------------------------------------
echo "[5/7] Starting infrastructure (PostgreSQL + Redis)..."
docker compose up -d postgres redis

echo "  Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
  if docker exec charity-coin-postgres pg_isready -U charity -q 2>/dev/null; then
    echo "  PostgreSQL is ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "  WARNING: PostgreSQL did not become ready in time"
  fi
  sleep 1
done

echo "  Waiting for Redis to be ready..."
for i in {1..15}; do
  if docker exec charity-coin-redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "  Redis is ready"
    break
  fi
  sleep 1
done

echo ""

# ---------------------------------------------------------------------------
# 6. Push database schema
# ---------------------------------------------------------------------------
echo "[6/7] Pushing database schema..."
cd apps/api
npx drizzle-kit push 2>&1 | tail -5
cd "$PROJECT_DIR"
echo ""

# ---------------------------------------------------------------------------
# 7. Seed the database
# ---------------------------------------------------------------------------
echo "[7/7] Seeding database with sample data..."
cd apps/api
npx tsx src/db/seed.ts 2>&1 || echo "  Seed script not found or failed (will be created later)"
cd "$PROJECT_DIR"

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "  To start developing:"
echo ""
echo "    make dev          # Start all services (API + Web + Infra)"
echo ""
echo "  Or start individually:"
echo ""
echo "    make dev-infra    # Start PostgreSQL + Redis only"
echo "    cd apps/api && npm run dev    # Start API (port 3001)"
echo "    cd apps/web && npm run dev    # Start Web (port 3000)"
echo ""
echo "  Smart contracts:"
echo ""
echo "    cd contracts"
echo "    forge build       # Compile contracts"
echo "    forge test        # Run tests"
echo ""
echo "  Useful commands:"
echo ""
echo "    make help         # Show all available commands"
echo "    make test         # Run all tests"
echo "    make db-seed      # Re-seed the database"
echo "    make dev-stop     # Stop infrastructure"
echo ""
