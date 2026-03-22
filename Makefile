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

.PHONY: help website-serve scrape-website scrape-website-serve download-website download-website-serve download-artifacts scrape-only seed-demo-data generate-website serve-only preview clean-cache clean-artifacts clean-all build-client test test-file test-snapshots test-snapshots-diff test-update-snapshots test-e2e test-e2e-file test-e2e-debug test-e2e-headed test-e2e-show-trace e2e-install open-coverage check-coverage test-client test-client-fast test-client-watch open-coverage-client test-visual visual-install .check-venv .check-gh
.PHONY: test-client-file

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

# ==============================================================================
# Meta / Help
# ==============================================================================

help:
	@echo "Spider Shop Historical Analysis - Makefile Commands"
	@echo ""
	@echo "Website Workflows:"
	@echo "  make website-serve          Generate website from existing data + serve"
	@echo "  make scrape-website         Run new scrape + generate website"
	@echo "  make scrape-website-serve   Run new scrape + generate website + serve"
	@echo "  make download-website       Download from GitHub + generate website"
	@echo "  make download-website-serve Download from GitHub + generate website + serve"
	@echo ""
	@echo "Data Management:"
	@echo "  make download-artifacts     Download latest data from GitHub Actions"
	@echo "  make scrape-only            Run scraper only (no website generation)"
	@echo "  make seed-demo-data         Write realistic local demo CSVs to tmp/local-testing/"
	@echo "  make generate-website       Generate website from existing CSV files or seed demo data if absent"
	@echo "  make serve-only             Serve existing website (no regeneration)"
	@echo "  make preview                Generate website + serve (alias for website-serve)"
	@echo "  make build-client           Build client-side TS/Svelte assets (auto-run by generate-website)"
	@echo ""
	@echo "Testing:"
	@echo "  make test                   Run pytest with coverage"
	@echo "  make test-file FILE=<path>  Run specific test file (no coverage)"
	@echo "  make test-snapshots         Run snapshot tests only"
	@echo "  make test-snapshots-diff    Show detailed diffs for snapshot tests"
	@echo "  make test-update-snapshots  Update all snapshots (review diffs first!)"
	@echo "  make e2e-install            Install Playwright Chromium browser"
	@echo "  make test-e2e               Run Playwright smoke tests (explicit)"
	@echo "  make test-e2e-file TEST=... Run specific e2e test file or function"
	@echo "  make test-e2e-debug         Run e2e with Playwright Inspector (PWDEBUG)"
	@echo "  make test-e2e-headed        Run e2e with visible browser window"
	@echo "  make test-e2e-show-trace    Open trace viewer for last e2e run"
	@echo "  make open-coverage          Open Python coverage report in browser"
	@echo "  make check-coverage         Print coverage summary (exits non-zero if below threshold)"
	@echo "  make check-coverage MODULE=<path>  Check coverage for a specific module"
	@echo "  make test-client            Run Vitest unit tests with coverage for client/src/ (enforces 80% threshold)"
	@echo "  make test-client-fast       Run Vitest unit tests without coverage (fast iteration, no threshold)"
	@echo "  make test-client-file FILE=<path>  Run a specific client Vitest file (no coverage)"
	@echo "  make test-client-watch      Run Vitest unit tests in watch mode (interactive, no coverage)"
	@echo "  make open-coverage-client   Open client coverage report in browser"
	@echo "  make visual-install         Install Playwright browser for visual tests (one-time setup)"
	@echo "  make test-visual            Run browser-backed visual contract tests (Vitest Browser Mode)"
	@echo ""
	@echo "Examples:"
	@echo "  make test-file FILE=tests/website_module/test_csv.py"
	@echo "  make test-file FILE=tests/scrape_module/test_breeder_matrix.py"
	@echo "  make test-e2e-file TEST=tests/e2e/test_snapshot_filters.py"
	@echo "  make test-e2e-file TEST=tests/e2e/test_snapshot_filters.py::test_price_slider_exists_and_initializes_correctly"
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

test-client-file:
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Please specify a client test file: make test-client-file FILE=src/path/to/test.ts"; \
		exit 1; \
	fi
	@if [ ! -f "client/$(FILE)" ]; then \
		echo "❌ Client test file not found: client/$(FILE)"; \
		exit 1; \
	fi
	@echo "🧪 Running client test file: $(FILE)"
	cd client && npm test -- --reporter=verbose $(FILE)

# ==============================================================================
# Client Build
# ==============================================================================

# Build client-side TypeScript/Svelte assets.
# Called automatically by generate-website (and all targets that depend on it).
build-client:
	@echo "🔨 Building client-side assets..."
	cd client && npm ci && npm run build
	@echo "✅ Client assets built to templates/scripts/dist/"

# ==============================================================================
# Website Workflows
# ==============================================================================

website-serve: generate-website serve-only

# Thin alias for website-serve; used during interactive DevTools MCP inspection.
preview: website-serve

scrape-website: scrape-only generate-website
	@echo "✅ Scrape complete and website generated"

scrape-website-serve: scrape-website serve-only

download-website: download-artifacts generate-website
	@echo "✅ Download complete and website generated"

download-website-serve: download-website serve-only

# ==============================================================================
# Data Management
# ==============================================================================

download-artifacts: .check-venv .check-gh
	@echo "📥 Downloading artifacts from GitHub Actions..."
	@mkdir -p $(TESTING_DIR)
	@echo "Resolving workflow run ID..."
	@LATEST_RUN=$$(./scripts/resolve_workflow_run.sh scrape.yml); \
	if [ -z "$$LATEST_RUN" ]; then \
		echo "❌ Failed to resolve workflow run ID"; \
		exit 1; \
	fi; \
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
		export PYTHONPATH="$$PWD/../../src:$$PYTHONPATH" && \
		python -m scrape
	@echo "✅ Scrape complete. CSV files saved to $(TESTING_DIR)/"

seed-demo-data: build-client .check-venv clean-cache
	@echo "🧪 Writing realistic local demo data..."
	@mkdir -p $(TESTING_DIR)
	source $(VENV)/bin/activate && python scripts/test_website_locally.py --seed-demo-data --overwrite-demo-data --data-only
	@echo "✅ Demo data written to $(TESTING_DIR)/"

generate-website: build-client .check-venv clean-cache
	@echo "🌐 Generating website..."
	source $(VENV)/bin/activate && python scripts/test_website_locally.py --seed-demo-data
	@echo "✅ Website generated in $(TESTING_DIR)/website/"

serve-only: .check-venv
	@echo "🌐 Starting local server..."
	source $(VENV)/bin/activate && python scripts/test_website_locally.py --serve

# ==============================================================================
# Testing
# ==============================================================================

test: .check-venv
	source $(VENV)/bin/activate && pytest --cov=src --cov-report=html --cov-report=term-missing --cov-report=json

test-file: .check-venv
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Please specify a test file: make test-file FILE=tests/path/to/test.py"; \
		exit 1; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "❌ Test file not found: $(FILE)"; \
		exit 1; \
	fi
	@echo "Running test file: $(FILE)"
	source $(VENV)/bin/activate && pytest $(FILE) -v

test-snapshots: .check-venv
	@echo "Running snapshot tests only..."
	source $(VENV)/bin/activate && pytest -k snapshot -v

test-snapshots-diff: .check-venv
	@echo "Running snapshot tests with detailed diff output..."
	source $(VENV)/bin/activate && pytest -k snapshot -vv

test-update-snapshots: .check-venv
	@echo "⚠️  Updating all snapshots. Ensure you've reviewed changes first!"
	source $(VENV)/bin/activate && pytest --snapshot-update

e2e-install: .check-venv
	@echo "📦 Installing Playwright Chromium browser..."
	source $(VENV)/bin/activate && python -m playwright install chromium
	@echo "✅ Playwright Chromium installed"

test-e2e: .check-venv e2e-install
	@echo "🧪 Running Playwright e2e smoke tests..."
	@mkdir -p $(TESTING_DIR)
	source $(VENV)/bin/activate && cd $(TESTING_DIR) && \
		export PYTHONPATH="$$PWD/../../src:$$PWD/../../tests:$$PYTHONPATH" && \
		export PYTEST_ADDOPTS="--basetemp=.pytest_tmp $$PYTEST_ADDOPTS" && \
		RUN_E2E=1 pytest ../../tests/e2e -m e2e -v

test-e2e-file: .check-venv e2e-install
	@if [ -z "$(TEST)" ]; then \
		echo "❌ Please specify a test: make test-e2e-file TEST=tests/e2e/test_file.py"; \
		echo "   Or a specific function: make test-e2e-file TEST=tests/e2e/test_file.py::test_function"; \
		exit 1; \
	fi
	@echo "🧪 Running e2e test: $(TEST)"
	@mkdir -p $(TESTING_DIR)
	source $(VENV)/bin/activate && cd $(TESTING_DIR) && \
		export PYTHONPATH="$$PWD/../../src:$$PWD/../../tests:$$PYTHONPATH" && \
		export PYTEST_ADDOPTS="--basetemp=.pytest_tmp $$PYTEST_ADDOPTS" && \
		RUN_E2E=1 pytest ../../$(TEST) -v

test-e2e-debug: .check-venv e2e-install
	@echo "🐛 Running e2e tests with Playwright Inspector (interactive debugger)..."
	@echo "   Use the Inspector UI to step through actions, pause, and inspect locators"
	@mkdir -p $(TESTING_DIR)
	source $(VENV)/bin/activate && cd $(TESTING_DIR) && \
		export PYTHONPATH="$$PWD/../../src:$$PWD/../../tests:$$PYTHONPATH" && \
		export PYTEST_ADDOPTS="--basetemp=.pytest_tmp $$PYTEST_ADDOPTS" && \
		PWDEBUG=1 RUN_E2E=1 pytest ../../tests/e2e -m e2e -v -s

test-e2e-headed: .check-venv e2e-install
	@echo "👀 Running e2e tests with visible browser..."
	@mkdir -p $(TESTING_DIR)
	source $(VENV)/bin/activate && cd $(TESTING_DIR) && \
		export PYTHONPATH="$$PWD/../../src:$$PWD/../../tests:$$PYTHONPATH" && \
		export PYTEST_ADDOPTS="--basetemp=.pytest_tmp $$PYTEST_ADDOPTS" && \
		PWHEADED=1 RUN_E2E=1 pytest ../../tests/e2e -m e2e -v -s

test-e2e-show-trace: .check-venv e2e-install
	@if [ ! -f tmp/e2e-trace.zip ]; then \
		echo "❌ No trace file found at tmp/e2e-trace.zip"; \
		echo "   Trace files are only saved when e2e tests fail"; \
		echo "   Run 'make test-e2e' to generate a trace"; \
		exit 1; \
	fi
	@echo "🔍 Opening trace viewer..."
	source $(VENV)/bin/activate && playwright show-trace tmp/e2e-trace.zip

open-coverage:
	@echo "Opening coverage report in browser..."
	open tmp/coverage/html/index.html

check-coverage: .check-venv
	@if [ -n "$(MODULE)" ]; then \
		$(PYTHON) scripts/check_coverage.py --module=$(MODULE); \
	else \
		$(PYTHON) scripts/check_coverage.py; \
	fi

# Run Vitest unit tests with coverage for client/src/.
# Mirrors `make test` (which always includes coverage) but kept separate to
# avoid adding a Node dependency to the Python-only edit cycle.
test-client:
	@echo "🧪 Running Vitest tests..."
	cd client && npm run coverage
	@echo "✅ Vitest tests passed"

# Run Vitest unit tests without coverage — fast local iteration loop.
# Use this during active component development; run `make test-client` before committing.
test-client-fast:
	@echo "🧪 Running Vitest tests (no coverage)..."
	cd client && npm test -- --reporter=dot
	@echo "✅ Vitest tests passed"

# Run Vitest unit tests in watch mode — interactive development.
# Re-runs affected tests on every file save. Requires an interactive terminal.
test-client-watch:
	cd client && npm run test:watch

# Open Vitest coverage report in browser (run `make test-client` first).
open-coverage-client:
	@echo "Opening client coverage report in browser..."
	open client/coverage/index.html

# Install Playwright Chromium browser for browser-backed visual tests (one-time setup).
# Uses the Node playwright package installed in client/node_modules, not the
# Python playwright used by make test-e2e.
visual-install:
	@echo "📦 Installing Playwright browser for visual tests..."
	cd client && node node_modules/playwright/cli.js install chromium
	@echo "✅ Playwright browser ready for visual tests"

# Run browser-backed visual contract tests in a real Chromium instance.
# These tests verify computed styles (getComputedStyle) and CSS custom-property
# resolution — things that happy-dom cannot simulate.
test-visual: visual-install
	@echo "🔍 Running browser-backed visual contract tests..."
	cd client && npm run test:visual
	@echo "✅ Visual tests passed"

# ==============================================================================
# Cleanup
# ==============================================================================

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
