# Spider Shop Historical Analysis - Makefile
# 
# This Makefile provides convenient shortcuts for testing and development.
# 
# Platform Support:
#   - macOS: make is pre-installed (or prompts auto-install of Command Line Tools)
#   - Linux: Usually pre-installed (or: sudo apt install make)
#   - Windows: Use Git Bash (from Git for Windows), WSL, or Chocolatey (choco install make)
#   - Alternative: Run Python commands directly (see docs/LOCAL_TESTING.md)
# 
# Virtual Environment:
#   All commands automatically activate the .venv virtual environment
#   Ensure .venv exists and has dependencies installed first

.PHONY: help test-website test-website-serve clean-artifacts clean-all .check-venv

# Shell configuration
SHELL := /bin/bash
.ONESHELL:

# Paths
VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip

help:
	@echo "Spider Shop Historical Analysis - Makefile Commands"
	@echo ""
	@echo "Testing:"
	@echo "  make test-website        Download artifacts and generate website locally"
	@echo "  make test-website-serve  Download artifacts, generate website, and start local server"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean-artifacts     Remove downloaded artifacts and generated website"
	@echo "  make clean-all           Clean everything including test cache and coverage"
	@echo ""
	@echo "Other:"
	@echo "  make test                Run pytest with coverage"
	@echo "  make coverage            View coverage report in browser"
	@echo ""
	@echo "⚠️  Note: These commands automatically use the virtual environment (.venv)"

.check-venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"; \
		exit 1; \
	fi

test-website: .check-venv
	@echo "📥 Downloading artifacts and generating website..."
	source $(VENV)/bin/activate && python test_website_locally.py

test-website-serve: .check-venv
	@echo "📥 Downloading artifacts, generating website, and starting server..."
	source $(VENV)/bin/activate && python test_website_locally.py --serve

test: .check-venv
	source $(VENV)/bin/activate && pytest --cov=src --cov-report=html --cov-report=term-missing --cov-report=json

coverage:
	@echo "Opening coverage report in browser..."
	open htmlcov/index.html

clean-artifacts:
	@echo "🧹 Cleaning artifacts and generated website..."
	rm -rf tmp/local-testing/

clean-all: clean-artifacts
	@echo "🧹 Cleaning test cache and coverage..."
	rm -rf .pytest_cache/ htmlcov/ .coverage coverage.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"
