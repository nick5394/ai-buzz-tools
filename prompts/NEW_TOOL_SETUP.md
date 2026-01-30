# New Tool Setup Checklist

Use this prompt when adding a new tool to AI-Buzz Tools. It ensures all patterns are followed consistently.

## Prerequisites

Before starting, you should have:
- [ ] Clear tool purpose (one job, done well)
- [ ] User problem it solves
- [ ] Data source identified (if applicable)

---

## Step 1: Create Data File

**File:** `data/{tool_name}.json`

**Required structure:**
```json
{
  "_metadata": {
    "last_updated": "2026-01-30",
    "source": "Where data comes from",
    "description": "What this data file contains"
  },
  // ... tool-specific data
}
```

**Checklist:**
- [ ] `_metadata` section at top
- [ ] `last_updated` date populated
- [ ] Data structure documented

---

## Step 2: Create API Router

**File:** `api/{tool_name}.py`

**Copy from:** `api/error_decoder.py` (reference implementation)

**Required sections:**
```python
"""
{Tool Name} API Router
Brief description.
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, EmailStr

from api.shared import subscribe_email, load_widget, load_json_data

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# Pydantic Models
# ============================================================================

# ... request/response models

# ============================================================================
# Helper Functions (if needed)
# ============================================================================

# ... helper functions

# ============================================================================
# Endpoints
# ============================================================================

# POST /main-action - Main functionality
# GET /main-action - GET version for shareable URLs
# GET /data-listing - List available data
# POST /alerts/subscribe - Email subscription
# GET /widget - Widget HTML
```

**Checklist:**
- [ ] Docstring at top
- [ ] Logger initialized
- [ ] Pydantic models with Field descriptions
- [ ] Main endpoint (POST + GET versions)
- [ ] Data listing endpoint
- [ ] Subscribe endpoint
- [ ] Widget endpoint
- [ ] Error handling matches pattern

---

## Step 3: Create Widget

**File:** `widgets/{tool_name}_widget.html`

**Copy from:** `widgets/error_decoder_widget.html`

**Required elements:**
- [ ] Self-contained (no external CSS/JS CDNs)
- [ ] CSS variables matching other widgets:
  ```css
  --primary-color: #2563eb;
  --primary-hover: #1d4ed8;
  --success-color: #10b981;
  --error-color: #ef4444;
  --warning-color: #f59e0b;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  --border-color: #e5e7eb;
  --border-radius: 12px;
  ```
- [ ] API_BASE_URL pattern at top of JS:
  ```javascript
  const API_BASE = window.API_BASE_URL || 'https://ai-buzz-tools.onrender.com';
  ```
- [ ] Mobile responsive (test at 375px)
- [ ] Loading states
- [ ] Error states
- [ ] Share URL functionality (pointing to ai-buzz.com)
- [ ] Email subscription form

---

## Step 4: Register Router

**File:** `main.py`

**Add import:**
```python
from api import pricing, status, error_decoder, embed, tools_landing, analytics, {tool_name}
```

**Add router:**
```python
app.include_router({tool_name}.router, prefix="/{tool-slug}", tags=["{tool-name}"])
```

**Update health check tools dict:**
```python
"tools": {
    # ... existing tools
    "{tool_name}": "available",
}
```

---

## Step 5: Create Tests

**File:** `tests/test_{tool_name}.py`

**Copy structure from:** `tests/test_error_decoder.py`

**Required test classes:**
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

**Run tests:**
```bash
source venv/bin/activate && pytest tests/test_{tool_name}.py -v
```

---

## Step 6: Update Embed Router

**File:** `api/embed.py`

**Add to TOOL_ENDPOINTS dict (appears twice in file):**
```python
TOOL_ENDPOINTS = {
    # ... existing
    "{tool-slug}": "/{tool-slug}/widget",
}
```

---

## Step 7: Create Content Template

**File:** `content/tools/{slug}.md`

**Copy from:** `content/tools/_template.md`

**Required sections:**
- Title (H1)
- Intro paragraph
- Widget marker comment
- "How to Use" section
- "FAQ" section (include "Is this tool free?")
- "Related Tools" section

**SEO checklist:**
- [ ] `seo_title` under 60 characters
- [ ] `seo_description` under 155 characters
- [ ] Slug follows `ai-{tool-name}` pattern

---

## Step 8: Final Verification

```bash
# Run all tests
source venv/bin/activate && pytest -v

# Start server
uvicorn main:app --reload

# Test endpoints manually
curl http://localhost:8000/{tool-slug}/widget | head -20
curl -X POST http://localhost:8000/{tool-slug}/alerts/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

**Manual checks:**
- [ ] Widget loads at `http://localhost:8000/{tool-slug}/widget`
- [ ] Widget works on mobile (375px viewport)
- [ ] Email subscription works
- [ ] Share URL points to ai-buzz.com

---

## Files Created/Modified

After completing all steps, you should have:

**Created:**
- [ ] `data/{tool_name}.json`
- [ ] `api/{tool_name}.py`
- [ ] `widgets/{tool_name}_widget.html`
- [ ] `tests/test_{tool_name}.py`
- [ ] `content/tools/ai-{tool-slug}.md`

**Modified:**
- [ ] `main.py` (router registration)
- [ ] `api/embed.py` (tool endpoints dict)

---

## Usage

```
@prompts/NEW_TOOL_SETUP.md

I want to add a new tool called "[Tool Name]" that [solves X problem].
Help me create all the necessary files following this checklist.
```
