# AI-Buzz Tools

[![Tests](https://github.com/YOUR_USERNAME/ai-buzz-tools/actions/workflows/test.yml/badge.svg)](https://github.com/YOUR_USERNAME/ai-buzz-tools/actions/workflows/test.yml)

**Unified API for AI developer tools.**

A FastAPI monorepo providing multiple tools to help developers make better decisions about AI APIs:

- **Pricing Calculator** - Compare costs across AI providers
- **Status Page** - Monitor AI API availability
- **Error Decoder** - Understand and fix API errors

## Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for widget tests)
playwright install chromium

# Run tests
make test
# or: pytest -v

# Start server
make server
# or: uvicorn main:app --reload

# Test
curl http://localhost:8000/
```

## Architecture

```
.
├── main.py              # FastAPI app with routers
├── api/                 # API routers
│   ├── pricing.py       # Pricing calculator endpoints
│   ├── status.py        # Status page endpoints
│   ├── error_decoder.py # Error decoder endpoints
│   └── shared.py        # Shared utilities
├── data/                # JSON data files
│   ├── pricing_data.json
│   ├── status_providers.json
│   └── error_patterns.json
├── widgets/             # Self-contained widget HTML files
│   ├── pricing_calculator_widget.html
│   ├── status_page_widget.html
│   └── error_decoder_widget.html
└── tests/               # Test suites
    ├── test_pricing.py
    ├── test_status.py
    ├── test_error_decoder.py
    ├── test_embed.py
    └── test_shared.py
```

## Widget Embedding

Widgets are self-contained HTML files served via `/widget` endpoints. They're embedded in WordPress using a JavaScript loader:

```html
<script
  src="https://ai-buzz-tools.onrender.com/embed.js"
  data-tool="error-decoder"
></script>
```

The loader fetches widget HTML client-side, bypassing WordPress page caching. Available tools: `pricing`, `status`, `error-decoder`.

See [WORDPRESS_SETUP.md](WORDPRESS_SETUP.md) for complete embedding guide.

## API Endpoints

### Pricing Calculator

- `GET /pricing/models` - Get all providers and models
- `POST /pricing/calculate` - Calculate costs
- `GET /pricing/calculate` - Calculate costs (GET version for shareable URLs)
- `POST /pricing/compare` - Compare specific models
- `POST /pricing/alerts/subscribe` - Subscribe to price alerts
- `GET /pricing/widget` - Get widget HTML

### Status Page

- `GET /status/check` - Check all providers (cached 60s)
- `POST /status/alerts/subscribe` - Subscribe to outage alerts
- `GET /status/widget` - Get widget HTML

### Error Decoder

- `POST /error-decoder/decode` - Decode error messages
- `GET /error-decoder/decode` - Decode error (GET version for shareable URLs)
- `GET /error-decoder/patterns` - List all error patterns
- `POST /error-decoder/alerts/subscribe` - Subscribe to error tips
- `GET /error-decoder/widget` - Get widget HTML

### Embed

- `GET /embed.js` - Universal JavaScript loader for embedding widgets

### Analytics

- `GET /analytics/stats` - Get current usage stats (in-memory, resets on deploy)
- `GET /analytics/gaps` - Get actionable gaps (what to build next)
- `GET /analytics/reset` - Reset stats (for testing)

## Analytics & Usage Tracking

The analytics system helps you understand how users interact with tools and identify gaps (things users try that don't work).

### Quick Start

```bash
# See what patterns/models to add
python scripts/analytics.py gaps

# Pull current stats before a deploy
python scripts/analytics.py pull-stats

# Generate full insights report
python scripts/analytics.py report

# Pull GA4 data (requires setup)
python scripts/analytics.py pull-ga4 --days 30
```

### What Gets Tracked

| Tool | Metrics | Gap Detection |
|------|---------|---------------|
| Error Decoder | Total decodes, match rate | Unmatched errors → patterns to add |
| Pricing Calculator | Calculations, token buckets | Models not found → pricing to add |
| Status Page | Provider checks | Most checked providers |

**Privacy**: Error messages are hashed, token counts are bucketed. No user identifiers stored.

### GA4 Setup (Optional)

To pull historical data from Google Analytics:

1. **Enable API**: Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Enable "Google Analytics Data API"

2. **Create Service Account**: IAM & Admin → Service Accounts → Create → Download JSON key

3. **Grant Access**: In GA4 Admin → Property Access Management → Add service account email as "Viewer"

4. **Set Environment Variables**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   export GA4_PROPERTY_ID="your-property-id"  # Found in GA4 Admin → Property Settings
   ```

5. **Test**:
   ```bash
   python scripts/analytics.py pull-ga4 --days 7
   ```

Data is saved to `data/analytics/` for local analysis.

## Testing

### Quick Start

**Using Make (recommended):**

```bash
# Install dependencies and browsers
make install
make install-browsers

# Run all tests
make test

# Run with coverage
make coverage
```

**Using test script:**

```bash
# Install dependencies and browsers, then run all tests
./scripts/run_tests.sh --install-deps --install-browsers

# Run tests only (assumes dependencies installed)
./scripts/run_tests.sh

# Run only unit tests
./scripts/run_tests.sh --unit-only

# Run only widget integration tests
./scripts/run_tests.sh --widget-only
```

**Using pytest directly:**

```bash
# Run all tests
pytest -v

# Run unit tests only
pytest tests/test_*.py -v -k "not test_widget_integration"

# Run widget integration tests only
pytest tests/test_widget_integration.py -v

# Run with coverage
pytest --cov=api --cov-report=term-missing --cov-report=html
```

### Test Widgets Locally

Test widgets in a browser without deploying:

```bash
# Start local server and open widgets
make test-local
# or
./scripts/test_widgets_locally.sh
```

Then open:

- `http://localhost:8765/error-decoder/widget`
- `http://localhost:8765/pricing/widget`
- `http://localhost:8765/status/widget`

### CI/CD

Tests run automatically on:

- Push to `main` branch
- Pull requests to `main` branch

The GitHub Actions workflow runs:

- Unit tests
- Widget integration tests (Playwright)
- Coverage reports

See [TESTING.md](TESTING.md) for comprehensive testing guide and checklist.

## Development

See `.cursor/rules/ai-buzz-tools.mdc` for core principles, decision framework, and testing checklist.

## License

MIT
