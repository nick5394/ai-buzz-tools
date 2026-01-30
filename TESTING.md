# Testing Guide

This document describes the testing framework for AI-Buzz Tools.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Install pre-push hook (one-time setup)
./scripts/install-hooks.sh

# Run all tests
pytest

# Run with coverage (for CI or when you want it)
pytest --cov=api --cov-report=html --cov-fail-under=80
```

## Running Tests

### Primary Methods

```bash
# Run all tests
pytest

# Run specific tool tests
pytest tests/test_error_decoder.py -v

# Run widget integration tests only
pytest tests/test_widget_integration.py -v

# Run with visible browser (debugging)
pytest tests/test_widget_integration.py --headed

# Stop on first failure
pytest -x
```

### Using Make

```bash
make test          # All tests
make test-unit     # Unit tests only (parallel)
make test-widget   # Widget integration tests only
make coverage      # Generate coverage report
```

## Pre-Push Hook

The pre-push hook runs `pytest` before every push to `main`. Install it once:

```bash
./scripts/install-hooks.sh
```

**Bypass (emergencies only):** `git push --no-verify`

CI will still run and block merge if tests fail.

## Test Structure

### File Naming

- `tests/test_{tool_name}.py` - Unit tests for each tool
- `tests/test_widget_integration.py` - Playwright browser tests

### Class Structure

```python
class Test{ToolName}Main:
    """Test main functionality endpoint."""

class Test{ToolName}Data:
    """Test data listing endpoint."""

class Test{ToolName}Subscribe:
    """Test email subscription."""

class Test{ToolName}Widget:
    """Test widget endpoint."""
```

### Fixtures (in `tests/conftest.py`)

- `client` - FastAPI test client
- `browser` - Playwright browser (session-scoped)
- `page` - Playwright page (function-scoped)
- `test_server` - Local server on port 8765

## Widget Integration Tests

Browser-based tests using Playwright. Test that widgets load, interactions work, and API calls succeed.

### Key Pattern

```python
@pytest.mark.asyncio
async def test_widget_action(self, page: Page, test_server):
    await load_widget(page, "widget-name", test_server)

    # Wait for API response when clicking
    async with page.expect_response(lambda r: "/api/endpoint" in r.url):
        await page.locator("#button").click()

    # Assert result
    await page.locator("#result").wait_for(state="visible", timeout=5000)
    assert await page.locator("#result").is_visible()
```

### Helper Functions

- `load_widget(page, widget_name, api_base)` - Load widget HTML
- `wait_for_results(page, widget_name)` - Wait for results section
- `wait_for_error_state(page, widget_name)` - Wait for error state

### Debugging

```bash
# See browser window
pytest tests/test_widget_integration.py --headed

# Pause in test for inspection
await page.pause()  # Opens Playwright inspector
```

## Continuous Integration

GitHub Actions runs on every push/PR to `main`:

1. Installs dependencies
2. Installs Playwright browsers
3. Runs all tests with coverage
4. Enforces 80% minimum coverage

**Workflow:** `.github/workflows/test.yml`

## Troubleshooting

### Tests fail to import

```bash
pip install -r requirements.txt
```

### Playwright browsers not found

```bash
playwright install chromium --with-deps
```

### Widget tests timeout

```bash
# Run with visible browser to see what's happening
pytest tests/test_widget_integration.py --headed
```

### Port conflicts

```bash
lsof -i :8000  # Check what's using the port
pkill -f uvicorn  # Kill existing servers
```

## Test Files

- `tests/test_pricing.py` - Pricing calculator
- `tests/test_status.py` - Status page
- `tests/test_error_decoder.py` - Error decoder
- `tests/test_widget_integration.py` - Browser tests for all widgets
- `tests/test_embed.py` - Embed loader
- `tests/test_shared.py` - Shared utilities
- `tests/conftest.py` - Fixtures and configuration

## Coverage

Coverage is enforced in CI (80% minimum). To check locally:

```bash
make coverage
# Opens htmlcov/index.html
```
