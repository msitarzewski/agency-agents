.PHONY: install build test dev clean deploy-contracts db-migrate db-push lint format help

# Default target
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

install: ## Install all dependencies (Node + Foundry)
	npm ci
	cd contracts && forge install

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

build: ## Build all packages
	npx turbo run build
	cd contracts && forge build

build-contracts: ## Build smart contracts only
	cd contracts && forge build --sizes

build-api: ## Build API only
	npx turbo run build --filter=charity-coin-api

build-web: ## Build frontend only
	npx turbo run build --filter=charity-coin-web

# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

test: ## Run all tests
	cd contracts && forge test -vvv
	npx turbo run lint

test-contracts: ## Run smart contract tests
	cd contracts && forge test -vvv

test-contracts-gas: ## Run contract tests with gas report
	cd contracts && forge test -vvv --gas-report

coverage: ## Run contract test coverage
	cd contracts && forge coverage --report summary

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

dev: ## Start local dev environment (DB + Redis + apps)
	docker compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 3
	npx turbo run dev

dev-infra: ## Start only infrastructure (DB + Redis)
	docker compose up -d
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis:      localhost:6379"

dev-stop: ## Stop local dev environment
	docker compose down

dev-clean: ## Stop and remove all dev data
	docker compose down -v

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

db-migrate: ## Run database migrations
	cd apps/api && npx drizzle-kit migrate

db-generate: ## Generate migration files from schema changes
	cd apps/api && npx drizzle-kit generate

db-push: ## Push schema directly (dev only)
	cd apps/api && npx drizzle-kit push

# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------

deploy-contracts: ## Deploy contracts to Base (requires DEPLOYER_PRIVATE_KEY)
	@test -n "$(BASE_RPC_URL)" || (echo "Error: BASE_RPC_URL not set" && exit 1)
	@test -n "$(DEPLOYER_PRIVATE_KEY)" || (echo "Error: DEPLOYER_PRIVATE_KEY not set" && exit 1)
	cd contracts && forge script script/Deploy.s.sol:Deploy \
		--rpc-url $(BASE_RPC_URL) \
		--private-key $(DEPLOYER_PRIVATE_KEY) \
		--broadcast \
		--verify \
		-vvvv

deploy-contracts-dry: ## Dry-run contract deployment (no broadcast)
	cd contracts && forge script script/Deploy.s.sol:Deploy \
		--rpc-url $(BASE_RPC_URL) \
		-vvvv

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

lint: ## Run all linters
	npx turbo run lint
	cd contracts && forge fmt --check

format: ## Format all code
	npx prettier --write "**/*.{ts,tsx,js,jsx,json,md}"
	cd contracts && forge fmt

clean: ## Clean all build artifacts
	npx turbo run clean
	cd contracts && forge clean
	rm -rf node_modules/.cache
