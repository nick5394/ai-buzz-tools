# Testing Guide

This document describes the testing framework and checklist for AI-Buzz Tools.

## Quick Start

```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Install pre-push hook (required before first push)
./scripts/install-hooks.sh

# Run all tests
pytest

# Run tests for a specific tool
pytest tests/test_error_decoder.py -v

# Start server for manual testing
uvicorn main:app --reload

# Test a tool with the test script
./scripts/test_tool.sh error-decoder
```

## Pre-Push Hook

**Required:** Before pushing to `main`, you must install the pre-push hook. This ensures tests pass and changed tools work on localhost before code reaches the repository.

### Installation

```bash
# Install the hook (one-time setup)
./scripts/install-hooks.sh
```

This installs a git hook that automatically runs before every push to `main`.

**Verification:**
After installation, verify the hook is in place:

```bash
ls -la .git/hooks/pre-push
# Should show executable file
```

### What the Hook Does

The pre-push hook performs two checks:

1. **Unit Tests** - Runs `pytest` to verify all unit tests pass
2. **Localhost Verification** - For changed tools, spins up a local server and tests endpoints:
   - Health check endpoint
   - Widget endpoint
   - Data endpoints (patterns/models/providers)
   - Main functionality endpoint

### Tool Detection

The hook automatically detects which tools changed by analyzing modified files:

- Changes to `api/pricing.py`, `widgets/pricing_*.html`, or `data/pricing_*.json` → tests `pricing`
- Changes to `api/status.py`, `widgets/status_*.html`, or `data/status_*.json` → tests `status`
- Changes to `api/error_decoder.py`, `widgets/error_decoder_*.html`, or `data/error_patterns.json` → tests `error-decoder`
- Changes to `main.py`, `api/shared.py`, or `requirements.txt` → tests all tools

### Bypassing the Hook

In emergency situations (e.g., hotfix), you can bypass the hook:

```bash
git push --no-verify
```

**Warning:** CI will still run and block the merge if tests fail. Use sparingly.

### Troubleshooting

**Hook blocks push but tests pass locally:**

- Make sure you're in the project root directory
- Check that dependencies are installed: `pip install -r requirements.txt`
- Verify pytest works: `pytest -v`

**Server fails to start in hook:**

- Check if port 8001-8100 is available: `lsof -i :8001`
- Kill any existing uvicorn processes: `pkill -f uvicorn`
- Check server logs: `tail -20 /tmp/pre-push-server.log`

**Hook not running:**

- Verify hook is installed: `ls -la .git/hooks/pre-push`
- Reinstall: `./scripts/install-hooks.sh`
- Check hook is executable: `chmod +x .git/hooks/pre-push`

## Testing Checklist

Every tool MUST pass the complete checklist in `.cursor/rules/ai-buzz-tools.mdc` before being considered complete.

### Quick Verification

1. **Run Automated Tests**

   ```bash
   pytest tests/test_{tool_name}.py -v
   ```

2. **Start Server and Test Manually**

   ```bash
   uvicorn main:app --reload
   ```

   Then test endpoints:
   - `http://localhost:8000/{tool}/patterns` (or `/models`, `/providers`)
   - `http://localhost:8000/{tool}/widget`
   - POST to main endpoint with sample data

3. **Test Widget in Browser**
   - Open `http://localhost:8000/{tool}/widget`
   - Test main functionality
   - Test share URL generation
   - Test email subscription
   - Test mobile responsive (Chrome DevTools → 375px)

4. **Verify Share URLs**
   - Generate share URL
   - Verify it points to `https://www.ai-buzz.com/...` (NOT localhost/Render)
   - Test that URL parameters work

## Test Structure

### Test File Naming

- `tests/test_{tool_name}.py` (e.g., `test_error_decoder.py`)

### Test Class Structure

```python
class Test{ToolName}Main:
    """Test main functionality endpoint."""

class Test{ToolName}Data:
    """Test data listing endpoint."""

class Test{ToolName}Subscribe:
    """Test email subscription."""

class Test{ToolName}Widget:
    """Test widget endpoint."""

class Test{ToolName}Integration:
    """Integration tests."""
```

### Example Test

See `tests/test_error_decoder.py` for a complete example.

## Common Test Patterns

### Testing Success Cases

```python
def test_success_case(self, client):
    response = client.post("/tool/endpoint", json={"key": "value"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

### Testing Error Cases

```python
def test_invalid_input(self, client):
    response = client.post("/tool/endpoint", json={"key": ""})
    assert response.status_code == 422  # Validation error
```

### Testing Widget

```python
def test_get_widget(self, client):
    response = client.get("/tool/widget")
    assert response.status_code == 200
    assert "widget" in response.text.lower()
    assert "<style>" in response.text  # Self-contained
    assert "<script>" in response.text  # Self-contained
```

## Fixtures

Common fixtures are available in `tests/conftest.py`:

- `client` - FastAPI test client
- Tool-specific sample data fixtures

## Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_error_decoder.py

# Specific test
pytest tests/test_error_decoder.py::TestErrorDecoderDecode::test_decode_rate_limit_error

# With coverage
pytest --cov=api --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Manual Testing Checklist

When testing a tool manually:

- [ ] Server starts without errors
- [ ] Main endpoint works (POST and GET versions)
- [ ] Data listing endpoint returns data
- [ ] Widget loads in browser
- [ ] Widget functionality works
- [ ] Share URL generation works
- [ ] Share URLs point to ai-buzz.com
- [ ] Email subscription works (check console for errors)
- [ ] Mobile responsive (test at 375px)
- [ ] Error handling shows user-friendly messages
- [ ] Loading states work

## Troubleshooting

### Tests Fail to Import

```bash
# Make sure you're in the project root
cd /path/to/ai-buzz-tools

# Install dependencies
pip install -r requirements.txt
```

### Server Won't Start

```bash
# Check for port conflicts
lsof -i :8000

# Try different port
uvicorn main:app --port 8001
```

### Widget Not Loading

- Check browser console for errors
- Verify widget file exists in `widgets/` directory
- Check that router is included in `main.py`

## Continuous Integration

For CI/CD, run:

```bash
pytest --cov=api --cov-report=xml
```

This generates coverage reports that can be integrated into CI pipelines.
