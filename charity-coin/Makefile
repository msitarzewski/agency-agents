.PHONY: install build test dev clean deploy-contracts db-migrate db-push lint format help \
       build-contracts build-api build-web test-contracts test-contracts-gas coverage \
       dev-infra dev-stop dev-clean dev-monitoring db-generate db-seed db-backup db-restore \
       deploy-contracts-dry deploy-api deploy-web deploy-staging deploy-production \
       docker-build docker-push security-audit security-scan logs logs-api logs-web \
       health-check

# Default target
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Setup
# =============================================================================

install: ## Install all dependencies (Node + Foundry)
	npm ci
	cd contracts && forge install

setup: ## Full project setup (install + infra + migrate + seed)
	./scripts/setup.sh

# =============================================================================
# Build
# =============================================================================

build: ## Build all packages
	npx turbo run build
	cd contracts && forge build

build-contracts: ## Build smart contracts only
	cd contracts && forge build --sizes

build-api: ## Build API only
	npx turbo run build --filter=charity-coin-api

build-web: ## Build frontend only
	npx turbo run build --filter=charity-coin-web

# =============================================================================
# Test
# =============================================================================

test: ## Run all tests
	cd contracts && forge test -vvv
	npx turbo run lint

test-contracts: ## Run smart contract tests
	cd contracts && forge test -vvv

test-contracts-gas: ## Run contract tests with gas report
	cd contracts && forge test -vvv --gas-report

coverage: ## Run contract test coverage
	cd contracts && forge coverage --report summary

# =============================================================================
# Development
# =============================================================================

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

dev-monitoring: ## Start infrastructure with monitoring stack
	docker compose --profile monitoring up -d
	@echo "PostgreSQL:  localhost:5432"
	@echo "Redis:       localhost:6379"
	@echo "Prometheus:  localhost:9090"
	@echo "Grafana:     localhost:3030  (admin/admin)"

# =============================================================================
# Database
# =============================================================================

db-migrate: ## Run database migrations
	cd apps/api && npx drizzle-kit migrate

db-generate: ## Generate migration files from schema changes
	cd apps/api && npx drizzle-kit generate

db-push: ## Push schema directly (dev only)
	cd apps/api && npx drizzle-kit push

db-seed: ## Seed the database with sample data
	cd apps/api && npx tsx src/db/seed.ts

db-backup: ## Backup the database to infra/postgres/backups/
	@mkdir -p infra/postgres/backups
	docker exec charity-coin-postgres pg_dump -U charity charity_coin | gzip > infra/postgres/backups/backup-$$(date +%Y%m%d-%H%M%S).sql.gz
	@echo "Backup saved to infra/postgres/backups/"

db-restore: ## Restore database from latest backup (usage: make db-restore FILE=backup.sql.gz)
	@test -n "$(FILE)" || (echo "Error: FILE not set. Usage: make db-restore FILE=backup-20240101-120000.sql.gz" && exit 1)
	gunzip -c infra/postgres/backups/$(FILE) | docker exec -i charity-coin-postgres psql -U charity charity_coin

# =============================================================================
# Deploy - Smart Contracts
# =============================================================================

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

# =============================================================================
# Deploy - Application (Docker-based)
# =============================================================================

docker-build: ## Build Docker images for API and Web
	docker compose -f docker-compose.prod.yml build api web

docker-push: ## Push Docker images to registry
	@test -n "$(REGISTRY)" || (echo "Error: REGISTRY not set (e.g., ghcr.io/org/charity-coin)" && exit 1)
	docker tag charity-coin-api $(REGISTRY)/api:latest
	docker tag charity-coin-web $(REGISTRY)/web:latest
	docker push $(REGISTRY)/api:latest
	docker push $(REGISTRY)/web:latest

deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	docker compose -f docker-compose.prod.yml --env-file .env.staging up -d --build
	@sleep 5
	$(MAKE) health-check

deploy-production: ## Deploy to production environment (with confirmation)
	@echo "WARNING: You are about to deploy to PRODUCTION."
	@read -p "Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ] || exit 1
	docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
	@sleep 10
	$(MAKE) health-check

# =============================================================================
# Quality & Security
# =============================================================================

lint: ## Run all linters
	npx turbo run lint
	cd contracts && forge fmt --check

format: ## Format all code
	npx prettier --write "**/*.{ts,tsx,js,jsx,json,md}"
	cd contracts && forge fmt

security-audit: ## Run npm dependency audit
	npm audit --audit-level=moderate
	@echo ""
	@echo "Run 'npm audit fix' to auto-fix issues, or 'npm audit --json' for detailed output."

security-scan: ## Run Trivy security scan on Docker images
	@command -v trivy >/dev/null 2>&1 || (echo "Error: trivy not installed. Install from https://trivy.dev" && exit 1)
	trivy fs --severity HIGH,CRITICAL apps/api/
	trivy fs --severity HIGH,CRITICAL apps/web/

# =============================================================================
# Operations & Monitoring
# =============================================================================

logs: ## Show logs from all Docker services
	docker compose -f docker-compose.prod.yml logs -f --tail=100

logs-api: ## Show API logs
	docker compose -f docker-compose.prod.yml logs -f --tail=100 api

logs-web: ## Show Web logs
	docker compose -f docker-compose.prod.yml logs -f --tail=100 web

health-check: ## Check health of all services
	@echo "Checking service health..."
	@echo "---"
	@curl -sf http://localhost:3001/health && echo " API: healthy" || echo " API: unhealthy"
	@curl -sf http://localhost:3000/ > /dev/null && echo " Web: healthy" || echo " Web: unhealthy"
	@docker exec charity-coin-postgres pg_isready -U charity -q && echo " PostgreSQL: healthy" || echo " PostgreSQL: unhealthy"
	@docker exec charity-coin-redis redis-cli ping > /dev/null && echo " Redis: healthy" || echo " Redis: unhealthy"

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean all build artifacts
	npx turbo run clean
	cd contracts && forge clean
	rm -rf node_modules/.cache

clean-all: clean ## Clean everything including node_modules and Docker volumes
	rm -rf node_modules
	rm -rf apps/api/node_modules apps/web/node_modules
	rm -rf apps/api/dist apps/web/.next
	docker compose down -v 2>/dev/null || true
