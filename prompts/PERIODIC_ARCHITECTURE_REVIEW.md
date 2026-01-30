# Periodic Architecture Review

Run this prompt when the codebase feels unruly or on a regular schedule (monthly quick-check, quarterly full review).

## Context

This repository contains AI-Buzz Tools - a collection of free developer tools. The key files are:

- **Rules:** `.cursor/rules/*.mdc` - Project principles and patterns
- **Reference implementation:** `api/error_decoder.py` - Copy patterns from here
- **Shared utilities:** `api/shared.py` - Common functions for all tools

Review the rules before starting: `@.cursor/rules/ai-buzz-tools.mdc`

---

## Choose Your Mode

### Quick Check (~15 min)
Run sections 1-2 only. Good for monthly maintenance.

### Full Review (~45 min)
Run all sections. Good for quarterly review or before major changes.

---

## Section 1: Health Check

Run these commands and report results:

```bash
# Run all tests
source venv/bin/activate && pytest -v

# Check coverage
pytest --cov=api --cov-report=term-missing

# Check for lint errors (if configured)
make lint
```

**Report:**
- Tests: X passing, Y failing
- Coverage: X%
- Any new warnings or deprecations?

---

## Section 2: Code Quality Scan

**Check for these issues:**

1. **Duplication** - Are patterns being repeated that should be extracted?
   - Compare widget endpoints across `api/*.py`
   - Compare subscribe endpoints across `api/*.py`
   - Look for repeated error handling blocks

2. **Consistency** - Are patterns being followed?
   - Do new routers match `error_decoder.py` structure?
   - Do data files have `_metadata` sections?
   - Are CSS variables consistent in widgets?

3. **Complexity** - Any functions over 50 lines?
   - Check `api/pricing.py:calculate_pricing` - still complex?
   - Any new complex functions added?

4. **Magic Numbers** - Any unexplained constants?
   - Search for hardcoded numbers without comments

---

## Section 3: Architecture Patterns

**Verify these patterns are still being followed:**

1. **File organization:**
   - API routers in `api/`
   - Data files in `data/` with `_metadata`
   - Self-contained widgets in `widgets/`
   - Tests follow `test_{tool}.py` naming

2. **Endpoint structure:**
   - Main functionality endpoint (POST + GET)
   - Data listing endpoint
   - Subscribe endpoint
   - Widget endpoint

3. **Error handling:**
   - FileNotFoundError caught explicitly
   - Logging with `exc_info=True` for exceptions
   - User-friendly error messages

4. **New anti-patterns to watch for:**
   - External dependencies in widgets (CDN links)
   - Share URLs not pointing to ai-buzz.com
   - Module-level mutable state (except documented caches)

---

## Section 4: Testing Gaps

**Check for:**

1. **Missing test files** - Every router in `api/` should have `tests/test_{name}.py`
2. **Uncovered code** - Check coverage report for gaps
3. **Flaky tests** - Any tests that sometimes fail?
4. **Widget integration** - Are all widgets tested in `test_widget_integration.py`?

```bash
# List all routers
ls api/*.py | grep -v __init__ | grep -v shared

# List all test files
ls tests/test_*.py
```

---

## Section 5: Cursor Rules Audit

**Review each rule file:**

1. **Still accurate?** - Do rules reflect current patterns?
2. **Gaps?** - Any new patterns not documented?
3. **Conflicts?** - Any rules that contradict each other?
4. **Frontmatter?** - All rules have proper activation metadata?

```bash
# List all rules
ls .cursor/rules/*.mdc
```

**Common issues:**
- Reference implementation changed but rules not updated
- New shared utilities not documented
- File protection tiers out of date

---

## Section 6: Documentation Currency

**Check these files are still accurate:**

- [ ] `README.md` - Architecture diagram, API endpoints, quick start
- [ ] `TESTING.md` - Test commands, troubleshooting
- [ ] `WORDPRESS_SETUP.md` - Embedding instructions
- [ ] `.cursor/rules/README.md` - Rule system overview (if exists)

**Questions:**
- Any new tools not documented?
- Any deprecated features still documented?
- Badge URLs correct?

---

## Output Template

Copy and fill this out:

```markdown
## Architecture Review - [DATE]

### Mode: [Quick Check / Full Review]

### Health Status
- Tests: X passing, Y failing
- Coverage: X%
- Warnings: [list any]

### Findings

#### High Priority
1. [Finding] - Effort: [Low/Med/High]

#### Medium Priority
1. [Finding] - Effort: [Low/Med/High]

#### Low Priority
1. [Finding] - Effort: [Low/Med/High]

### Recommended Actions
- [ ] Action 1
- [ ] Action 2

### Deferred (Not Urgent)
- Item 1 (reason for deferring)

### Notes for Next Review
- [Anything to check next time]
```

---

## Usage

**Full review:**
```
@prompts/PERIODIC_ARCHITECTURE_REVIEW.md

Run a full architecture review of this codebase.
```

**Quick check:**
```
@prompts/PERIODIC_ARCHITECTURE_REVIEW.md

Run a quick check (sections 1-2 only).
```

**Specific focus:**
```
@prompts/PERIODIC_ARCHITECTURE_REVIEW.md

Run only section 4 (Testing Gaps).
```
