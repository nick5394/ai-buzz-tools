# Testing Checklist - Quick Reference

This is a quick reference checklist. See `.cursor/rules/ai-buzz-tools.mdc` for the full testing framework.

## ✅ Pre-Development

- [ ] Data file created with `_metadata` section
- [ ] API router created following existing patterns
- [ ] Pydantic models defined for request/response

## ✅ Required Endpoints

- [ ] Main functionality endpoint (POST + GET versions)
- [ ] Data listing endpoint (`/patterns`, `/models`, or `/providers`)
- [ ] Email subscription endpoint (`/alerts/subscribe`)
- [ ] Widget endpoint (`/widget`)

## ✅ Widget

- [ ] Self-contained (CSS + JS inline)
- [ ] Mobile responsive (test at 375px)
- [ ] Share URLs point to `ai-buzz.com`
- [ ] Matches existing widget style

## ✅ Testing

- [ ] Unit tests written (`tests/test_{tool}.py`)
- [ ] Integration tests written
- [ ] All tests pass: `pytest`
- [ ] Manual testing on localhost
- [ ] Widget tested in browser

## ✅ Integration

- [ ] Router added to `main.py`
- [ ] Health check updated
- [ ] README updated

## ✅ Deployment

- [ ] All tests pass
- [ ] No linting errors
- [ ] Share URLs verified (not localhost/Render)

## Quick Commands

```bash
# Run tests
pytest tests/test_{tool}.py -v

# Start server
uvicorn main:app --reload

# Test tool script
./scripts/test_tool.sh {tool-name}
```
