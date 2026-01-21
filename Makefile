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

.PHONY: help website website-serve scrape-website scrape-website-serve download-website download-website-serve download-artifacts scrape-only generate-website clean-cache clean-artifacts clean-all test coverage .check-venv .check-gh

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
	@echo "  make website                Generate website from existing data"
	@echo "  make website-serve          Generate website from existing data + serve"
	@echo "  make scrape-website         Run new scrape + generate website"
	@echo "  make scrape-website-serve   Run new scrape + generate website + serve"
	@echo "  make download-website       Download from GitHub + generate website"
	@echo "  make download-website-serve Download from GitHub + generate website + serve"
	@echo ""
	@echo "Data Management:"
	@echo "  make download-artifacts     Download latest data from GitHub Actions"
	@echo "  make scrape-only            Run scraper only (no website generation)"
	@echo "  make generate-website       Generate website from existing CSV files"
	@echo ""
	@echo "Testing:"
	@echo "  make test                   Run pytest with coverage"
	@echo "  make coverage               View coverage report in browser"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean-cache            Clear Python bytecode cache (.pyc, __pycache__)"
	@echo "  make clean-artifacts        Remove downloaded artifacts and generated website"
	@echo "  make clean-all              Clean everything including test cache and coverage"
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

scrape-only: .check-venv clean-cache
	@echo "🕷️  Running scraper locally..."
	@mkdir -p $(TESTING_DIR)
	@source $(VENV)/bin/activate && cd $(TESTING_DIR) && \
		touch analysis_summary.md && \
		export GITHUB_STEP_SUMMARY="$$PWD/analysis_summary.md" && \
		python ../../src/scrape_spidershop_spiderlings.py
	@echo "✅ Scrape complete. CSV files saved to $(TESTING_DIR)/"

generate-website: .check-venv clean-cache
	@echo "🌐 Generating website..."
	@if [ ! -f "$(TESTING_DIR)/spidershop_spiderlings_scrape.csv" ]; then \
		echo "❌ CSV files not found in $(TESTING_DIR)/"; \
		echo "Run 'make download-artifacts' or 'make scrape-only' first"; \
		exit 1; \
	fi
	source $(VENV)/bin/activate && python scripts/test_website_locally.py
	@echo "✅ Website generated in $(TESTING_DIR)/website/"

website: generate-website
	@echo "✅ Website ready at $(TESTING_DIR)/website/"

website-serve: generate-website
	@echo "🌐 Starting local server..."
	source $(VENV)/bin/activate && python scripts/test_website_locally.py --serve

scrape-website: scrape-only generate-website
	@echo "✅ Scrape complete and website generated"

scrape-website-serve: scrape-website
	@echo "🌐 Starting local server..."
	source $(VENV)/bin/activate && python scripts/test_website_locally.py --serve

download-website: download-artifacts generate-website
	@echo "✅ Download complete and website generated"

download-website-serve: download-website
	@echo "🌐 Starting local server..."
	source $(VENV)/bin/activate && python scripts/test_website_locally.py --serve

test: .check-venv
	source $(VENV)/bin/activate && pytest --cov=src --cov-report=html --cov-report=term-missing --cov-report=json

coverage:
	@echo "Opening coverage report in browser..."
	open tmp/coverage/html/index.html

clean-cache:
	@echo "🧹 Cleaning Python bytecode cache..."
	@find . -path ./.venv -prune -o -type f -name "*.pyc" -exec rm -f {} + 2>/dev/null || true
	@find . -path ./.venv -prune -o -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cache cleared"

clean-artifacts:
	@echo "🧹 Cleaning artifacts and generated website..."
	rm -rf tmp/local-testing/

clean-all: clean-artifacts
	@echo "🧹 Cleaning test cache and coverage..."
	rm -rf .pytest_cache/ tmp/coverage/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"
