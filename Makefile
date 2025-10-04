# =============================================================================
# DRP Project Makefile
# =============================================================================
# This Makefile provides convenient commands for building, running, and managing
# the DRP project using Docker and other development tools

.PHONY: help build run dev test clean logs shell lint format security scan

# =============================================================================
# Variables
# =============================================================================
DOCKER_COMPOSE := docker-compose -f scripts/docker-compose.yml
DOCKER := docker
PYTHON := python3
PIP := pip3

# Service names
MAIN_SERVICE := drp-node
DEV_SERVICE := drp-dev
TEST_SERVICE := drp-test
AI_SERVICE := drp-ai-elder

# =============================================================================
# Help
# =============================================================================
help: ## Show this help message
	@echo "DRP (Decentralized Rights Protocol) - Available Commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ 🏗️  Building

build: ## Build all Docker images
	@echo "🏗️  Building DRP Docker images..."
	$(DOCKER_COMPOSE) build --parallel

build-dev: ## Build development image
	@echo "🏗️  Building development image..."
	$(DOCKER) build --target development -t drp-dev .

build-prod: ## Build production image
	@echo "🏗️  Building production image..."
	$(DOCKER) build --target runtime -t drp-prod .

##@ 🚀  Running

run: ## Start the main DRP network
	@echo "🚀 Starting DRP network..."
	$(DOCKER_COMPOSE) up -d $(MAIN_SERVICE) drp-validator-1 drp-validator-2

run-full: ## Start the complete DRP network with all services
	@echo "🚀 Starting complete DRP network..."
	$(DOCKER_COMPOSE) up -d

dev: ## Start development environment
	@echo "🚀 Starting development environment..."
	$(DOCKER_COMPOSE) --profile development up -d $(DEV_SERVICE)

test: ## Run tests in Docker
	@echo "🧪 Running tests..."
	$(DOCKER_COMPOSE) --profile testing run --rm $(TEST_SERVICE)

test-local: ## Run tests locally
	@echo "🧪 Running tests locally..."
	$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=html

ai-elder: ## Start AI Elder service
	@echo "🤖 Starting AI Elder service..."
	$(DOCKER_COMPOSE) up -d $(AI_SERVICE)

monitoring: ## Start monitoring stack (Prometheus + Grafana)
	@echo "📊 Starting monitoring stack..."
	$(DOCKER_COMPOSE) --profile monitoring up -d

##@ 🔧  Development

shell: ## Open shell in main container
	@echo "🐚 Opening shell in main container..."
	$(DOCKER_COMPOSE) exec $(MAIN_SERVICE) /bin/bash

shell-dev: ## Open shell in development container
	@echo "🐚 Opening shell in development container..."
	$(DOCKER_COMPOSE) exec $(DEV_SERVICE) /bin/bash

logs: ## Show logs from all services
	@echo "📋 Showing logs..."
	$(DOCKER_COMPOSE) logs -f

logs-main: ## Show logs from main service
	@echo "📋 Showing main service logs..."
	$(DOCKER_COMPOSE) logs -f $(MAIN_SERVICE)

logs-ai: ## Show logs from AI Elder service
	@echo "📋 Showing AI Elder logs..."
	$(DOCKER_COMPOSE) logs -f $(AI_SERVICE)

##@ 🧹  Code Quality

lint: ## Run linting
	@echo "🔍 Running linting..."
	$(DOCKER_COMPOSE) exec $(DEV_SERVICE) flake8 src/ tests/

format: ## Format code
	@echo "✨ Formatting code..."
	$(DOCKER_COMPOSE) exec $(DEV_SERVICE) black src/ tests/
	$(DOCKER_COMPOSE) exec $(DEV_SERVICE) isort src/ tests/

lint-local: ## Run linting locally
	@echo "🔍 Running linting locally..."
	flake8 src/ tests/

format-local: ## Format code locally
	@echo "✨ Formatting code locally..."
	black src/ tests/
	isort src/ tests/

##@ 🔒  Security

security-scan: ## Run security scan
	@echo "🔒 Running security scan..."
	$(DOCKER) run --rm -v $(PWD):/app securecodewarrior/docker-security-scan:latest /app

audit: ## Run security audit on dependencies
	@echo "🔒 Running security audit..."
	$(DOCKER_COMPOSE) exec $(DEV_SERVICE) pip audit

##@ 🧪  Testing

test-unit: ## Run unit tests
	@echo "🧪 Running unit tests..."
	$(DOCKER_COMPOSE) exec $(DEV_SERVICE) python -m pytest tests/unit/ -v

test-integration: ## Run integration tests
	@echo "🧪 Running integration tests..."
	$(DOCKER_COMPOSE) exec $(DEV_SERVICE) python -m pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	$(DOCKER_COMPOSE) exec $(DEV_SERVICE) python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

##@ 📊  Monitoring

stats: ## Show container statistics
	@echo "📊 Showing container statistics..."
	$(DOCKER) stats $(shell $(DOCKER_COMPOSE) ps -q)

health: ## Check health of all services
	@echo "🏥 Checking service health..."
	@$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "Health check URLs:"
	@echo "  Main Node: http://localhost:8000/health"
	@echo "  Validator 1: http://localhost:8001/health"
	@echo "  Validator 2: http://localhost:8002/health"
	@echo "  AI Elder: http://localhost:8003/health"

##@ 🧹  Cleanup

clean: ## Stop and remove all containers
	@echo "🧹 Cleaning up containers..."
	$(DOCKER_COMPOSE) down -v --remove-orphans

clean-images: ## Remove Docker images
	@echo "🧹 Removing Docker images..."
	$(DOCKER) rmi $(shell $(DOCKER) images "drp*" -q) 2>/dev/null || true

clean-volumes: ## Remove all volumes
	@echo "🧹 Removing volumes..."
	$(DOCKER_COMPOSE) down -v

clean-all: clean clean-images clean-volumes ## Clean everything (containers, images, volumes)
	@echo "🧹 Complete cleanup done!"

##@ 🔄  Utilities

restart: ## Restart all services
	@echo "🔄 Restarting services..."
	$(DOCKER_COMPOSE) restart

restart-main: ## Restart main service
	@echo "🔄 Restarting main service..."
	$(DOCKER_COMPOSE) restart $(MAIN_SERVICE)

update: ## Update dependencies and rebuild
	@echo "🔄 Updating dependencies..."
	$(PIP) install -r requirements.txt --upgrade
	$(MAKE) build

backup: ## Backup important data
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@$(DOCKER_COMPOSE) exec $(MAIN_SERVICE) tar -czf /tmp/drp-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz /app/data /app/logs
	@$(DOCKER) cp $(shell $(DOCKER_COMPOSE) ps -q $(MAIN_SERVICE)):/tmp/drp-backup-*.tar.gz backups/

##@ 🌐  Network

network-info: ## Show network information
	@echo "🌐 Network Information:"
	@echo "  Main Node: http://localhost:8000"
	@echo "  Validator 1: http://localhost:8001"
	@echo "  Validator 2: http://localhost:8002"
	@echo "  AI Elder: http://localhost:8003"
	@echo "  Development: http://localhost:8004"
	@echo "  Grafana: http://localhost:3000 (admin/drp123)"
	@echo "  Prometheus: http://localhost:9090"

##@ 📚  Documentation

docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@$(DOCKER_COMPOSE) exec $(DEV_SERVICE) python -m pdoc --html src --output-dir docs/api

##@ 🚀  Production

deploy-prod: ## Deploy to production
	@echo "🚀 Deploying to production..."
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d

scale: ## Scale validator nodes
	@echo "📈 Scaling validator nodes..."
	$(DOCKER_COMPOSE) up -d --scale drp-validator=3

# =============================================================================
# Default target
# =============================================================================
.DEFAULT_GOAL := help
