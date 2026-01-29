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

# Start server
uvicorn main:app --reload

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
<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="error-decoder"></script>
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

## Testing

Run tests with coverage:

```bash
pytest
```

Run tests without coverage:

```bash
pytest --no-cov
```

See [TESTING.md](TESTING.md) for comprehensive testing guide and checklist.

## Development

See `.cursor/rules/ai-buzz-tools.mdc` for core principles, decision framework, and testing checklist.

## License

MIT
