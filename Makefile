# Spider Shop Historical Analysis - Makefile
# 
# This Makefile provides convenient shortcuts for testing and development.
# 
# Platform Support:
#   - macOS: make is pre-installed (or prompts auto-install of Command Line Tools)
#   - Linux: Usually pre-installed (or: sudo apt install make)
#   - Windows: Use Git Bash (from Git for Windows), WSL, or Chocolatey (choco install make)
#   - Alternative: Run Python commands directly (see docs/CONTRIBUTING.md)
# 
# Virtual Environment:
#   All commands automatically activate the .venv virtual environment
#   Ensure .venv exists and has dependencies installed first

.PHONY: help local-website local-website-serve remote-website remote-website-serve download-artifacts scrape-local generate-website clean-artifacts clean-all .check-venv

# Shell configuration
SHELL := /bin/bash
.ONESHELL:

# Paths
VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
TESTING_DIR := tmp/local-testing

# GitHub repository info
REPO_OWNER := christianacca
REPO_NAME := spidershop-historical-analysis

help:
	@echo "Spider Shop Historical Analysis - Makefile Commands"
	@echo ""
	@echo "Website Workflows:"
	@echo "  make local-website          Scrape locally + generate website"
	@echo "  make local-website-serve    Scrape locally + generate website + serve"
	@echo "  make remote-website         Download from GitHub Actions + generate website"
	@echo "  make remote-website-serve   Download from GitHub Actions + generate + serve"
	@echo ""
	@echo "Individual Steps:"
	@echo "  make scrape-local           Run scraper locally to generate CSV files"
	@echo "  make download-artifacts     Download latest artifacts from GitHub Actions"
	@echo "  make generate-website       Generate website from existing CSV files"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean-artifacts        Remove downloaded artifacts and generated website"
	@echo "  make clean-all              Clean everything including test cache and coverage"
	@echo ""
	@echo "Other:"
	@echo "  make test                   Run pytest with coverage"
	@echo "  make coverage               View coverage report in browser"
	@echo ""
	@echo "⚠️  Note: These commands automatically use the virtual environment (.venv)"

.check-venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"; \
		exit 1; \
	fi

.check-gh:
	@if ! command -v gh &> /dev/null; then \
		echo "❌ GitHub CLI (gh) is not installed."; \
		echo "Install it with: brew install gh"; \
		echo "Then authenticate with: gh auth login"; \
		exit 1; \
	fi
	@if ! gh auth status &> /dev/null; then \
		echo "❌ GitHub CLI is not authenticated."; \
		echo "Run: gh auth login"; \
		exit 1; \
	fi

download-artifacts: .check-venv .check-gh
	@echo "📥 Downloading artifacts from GitHub Actions..."
	@mkdir -p $(TESTING_DIR)
	@echo "Finding latest successful workflow run..."
	@RUN_ID=$$(gh api repos/$(REPO_OWNER)/$(REPO_NAME)/actions/workflows \
		--paginate \
		-q '.workflows[] | select(.name == "Spider Shop Spiderlings Scrape") | .id' | head -1); \
	if [ -z "$$RUN_ID" ]; then \
		echo "❌ Could not find workflow"; \
		exit 1; \
	fi; \
	LATEST_RUN=$$(gh api repos/$(REPO_OWNER)/$(REPO_NAME)/actions/workflows/$$RUN_ID/runs \
		-q '.workflow_runs[] | select(.conclusion == "success") | .id' | head -1); \
	if [ -z "$$LATEST_RUN" ]; then \
		echo "❌ No successful runs found"; \
		exit 1; \
	fi; \
	echo "✅ Found latest successful run: $$LATEST_RUN"; \
	echo "Downloading artifacts..."; \
	for artifact in spidershop-snapshot spidershop-history breeder-opportunity-table dealer-supply-risk-table analysis-summary; do \
		echo "  Downloading $$artifact..."; \
		./scripts/download_artifact.sh $(REPO_OWNER) $(REPO_NAME) $$artifact $(TESTING_DIR) $$LATEST_RUN || echo "  ⚠️  Skipped $$artifact"; \
	done
	@echo "✅ Download complete"

scrape-local: .check-venv
	@echo "🕷️  Running scraper locally..."
	@mkdir -p $(TESTING_DIR)
	@cd $(TESTING_DIR) && source ../$(VENV)/bin/activate && \
		python ../../src/scrape_spidershop_spiderlings.py
	@echo "✅ Scrape complete. CSV files saved to $(TESTING_DIR)/"

generate-website: .check-venv
	@echo "🌐 Generating website..."
	@if [ ! -f "$(TESTING_DIR)/spidershop_spiderlings_scrape.csv" ]; then \
		echo "❌ CSV files not found in $(TESTING_DIR)/"; \
		echo "Run 'make download-artifacts' or 'make scrape-local' first"; \
		exit 1; \
	fi
	source $(VENV)/bin/activate && python scripts/test_website_locally.py
	@echo "✅ Website generated in $(TESTING_DIR)/website/"

local-website: scrape-local generate-website
	@echo "✅ Local website ready"

local-website-serve: local-website
	@echo "🌐 Starting local server..."
	source $(VENV)/bin/activate && python scripts/test_website_locally.py --serve

remote-website: download-artifacts generate-website
	@echo "✅ Remote website ready"

remote-website-serve: remote-website
	@echo "🌐 Starting local server..."
	source $(VENV)/bin/activate && python scripts/test_website_locally.py --serve

test: .check-venv
	source $(VENV)/bin/activate && pytest --cov=src --cov-report=html --cov-report=term-missing --cov-report=json

coverage:
	@echo "Opening coverage report in browser..."
	open tmp/coverage/html/index.html

clean-artifacts:
	@echo "🧹 Cleaning artifacts and generated website..."
	rm -rf tmp/local-testing/

clean-all: clean-artifacts
	@echo "🧹 Cleaning test cache and coverage..."
	rm -rf .pytest_cache/ tmp/coverage/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"
