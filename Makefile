.PHONY: help test test-unit test-widget test-all install install-browsers clean coverage lint

help: ## Show this help message
	@echo "AI-Buzz Tools - Available Commands"
	@echo ""
	@echo "Testing:"
	@echo "  make test              Run all tests (unit + widget integration)"
	@echo "  make test-unit         Run only unit tests"
	@echo "  make test-widget       Run only widget integration tests"
	@echo "  make coverage          Run tests with coverage report"
	@echo ""
	@echo "Setup:"
	@echo "  make install           Install Python dependencies"
	@echo "  make install-browsers  Install Playwright browsers"
	@echo ""
	@echo "Development:"
	@echo "  make lint              Run linting checks"
	@echo "  make clean             Clean generated files"
	@echo "  make server            Start development server"
	@echo ""

install: ## Install Python dependencies
	python -m pip install --upgrade pip
	pip install -r requirements.txt

install-browsers: ## Install Playwright browsers
	playwright install chromium
	playwright install-deps chromium

test-unit: ## Run unit tests only (parallel execution)
	pytest tests/test_*.py -v -n auto -k "not test_widget_integration"

test-widget: ## Run widget integration tests only
	pytest tests/test_widget_integration.py -v

test: test-unit test-widget ## Run all tests

test-all: test ## Alias for test

coverage: ## Run tests with coverage report
	pytest --cov=api --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

lint: ## Run linting checks
	@echo "Running lint checks..."
	@python -m flake8 api/ tests/ --max-line-length=120 --exclude=__pycache__ || echo "flake8 not installed, skipping"
	@python -m pylint api/ tests/ --disable=all --enable=E999,F0001 || echo "pylint not installed, skipping"

clean: ## Clean generated files
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

server: ## Start development server
	uvicorn main:app --reload

test-local: ## Test widgets locally (starts server on port 8765)
	./scripts/test_widgets_locally.sh
