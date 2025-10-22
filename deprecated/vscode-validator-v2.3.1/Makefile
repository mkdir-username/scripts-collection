.PHONY: help install build test lint format clean dev

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)SDUI Validator - Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	npm install
	@echo "$(GREEN)Dependencies installed$(NC)"

build: ## Build the project
	@echo "$(BLUE)Building project...$(NC)"
	chmod +x build.sh
	./build.sh
	@echo "$(GREEN)Build completed$(NC)"

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	npm test

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	npm run test:watch

test-coverage: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	npm run test:coverage

lint: ## Run linter
	@echo "$(BLUE)Running linter...$(NC)"
	npm run lint

lint-fix: ## Fix linting issues
	@echo "$(BLUE)Fixing linting issues...$(NC)"
	npm run lint:fix

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	npm run format

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code formatting...$(NC)"
	npm run format:check

typecheck: ## Run TypeScript type checker
	@echo "$(BLUE)Running type checker...$(NC)"
	npm run typecheck

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf dist coverage .jest-cache
	@echo "$(GREEN)Clean completed$(NC)"

dev: ## Start development mode
	@echo "$(BLUE)Starting development mode...$(NC)"
	npm run build:watch

precommit: ## Run all pre-commit checks
	@echo "$(BLUE)Running pre-commit checks...$(NC)"
	npm run precommit
	@echo "$(GREEN)All checks passed$(NC)"

setup: install build ## Complete setup (install + build)
	@echo "$(GREEN)Setup completed successfully$(NC)"

verify: lint typecheck test ## Verify code quality (lint + typecheck + test)
	@echo "$(GREEN)Verification completed$(NC)"

all: clean install build test ## Run all steps (clean, install, build, test)
	@echo "$(GREEN)All steps completed$(NC)"
