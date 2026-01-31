# Periodic Architecture Review

Run this prompt when the codebase feels unruly or on a regular schedule (monthly quick-check, quarterly full review).

---

## Your Mindset: Code Auditor

**Technical debt compounds. Small messes become big messes. Inconsistency breeds bugs.**

This review exists to answer: **Is this codebase getting better or worse?**

"About the same" is getting worse. Entropy is the default. Without active maintenance, codebases decay.

---

## Failure Criteria (Fix Immediately)

These issues BLOCK the review. Stop and fix:

- [ ] **Any failing tests** - Tests must pass. Period.
- [ ] **Coverage below 80%** - Untested code is broken code waiting to happen
- [ ] **Router without matching test file** - No tests = no confidence
- [ ] **Widget with external CDN dependency** - Violates self-contained principle
- [ ] **Share URLs pointing to Render** - Should point to ai-buzz.com

---

## Success Criteria

The codebase passes review when:

1. **All tests pass** - `pytest` returns 0 failures
2. **Coverage ≥80%** - Every router has comprehensive tests
3. **Patterns are consistent** - New code matches `error_decoder.py`
4. **No dead code** - Unused functions, files, or imports removed
5. **Documentation is accurate** - README matches reality

---

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

**No "I'll do a deeper review later."** If you're doing a quick check, schedule the full review.

---

## Section 1: Health Check

Run these commands and report results:

```bash
# Run all tests
pytest -v

# Check coverage
pytest --cov=api --cov-report=term-missing

# Check for lint errors (if configured)
make lint
```

**Report (be specific):**

- Tests: X passing, Y failing
- Coverage: X% (≥80% required)
- Warnings: [list any]

### Interpreting Results

| Result           | Interpretation      | Action                             |
| ---------------- | ------------------- | ---------------------------------- |
| Any test failing | Codebase is broken  | FIX IMMEDIATELY                    |
| Coverage <80%    | Code is undertested | Add tests before continuing        |
| Coverage <70%    | Serious problem     | Stop all feature work, write tests |
| New warnings     | Something changed   | Investigate before continuing      |

**"Tests pass" is the minimum bar, not the goal.** Passing tests with poor coverage is false confidence.

---

## Section 2: Code Quality Scan

**Check for these issues (assume they exist until proven otherwise):**

### 1. Duplication (DRY Violations)

Every copy-paste is future technical debt. Check:

- Widget endpoints across `api/*.py` - Should be nearly identical
- Subscribe endpoints across `api/*.py` - Should use shared pattern
- Error handling blocks - Should follow same structure

**If you find duplication:**

1. Can it be extracted to `api/shared.py`?
2. If not, document why (valid reasons: different error messages, different response types)
3. If you're not sure, extract it. Duplication is worse than over-abstraction.

### 2. Consistency (Pattern Violations)

Every deviation creates confusion and bugs. Check:

| Check            | Reference                | Finding               |
| ---------------- | ------------------------ | --------------------- |
| Router structure | `api/error_decoder.py`   | Same? Different? Why? |
| Data files       | Have `_metadata` section | Yes/No                |
| Widget CSS       | Same variables           | Yes/No                |
| Error handling   | Try/except pattern       | Consistent?           |

**If patterns don't match:**

1. Is the deviation intentional and documented?
2. If not, fix it to match the reference
3. If intentional, add a comment explaining why

### 3. Complexity (Future Bug Magnets)

Long functions are hard to test, hard to understand, hard to modify.

- **Any function over 50 lines?** Flag it.
- **Any function with 3+ levels of nesting?** Flag it.
- **Any function with 5+ parameters?** Flag it.

**Check specifically:**

- `api/pricing.py:calculate_pricing` - Is it still complex?
- Any new complex functions since last review?

### 4. Magic Numbers (Time Bombs)

Hardcoded values without context become bugs when context changes.

```bash
# Search for suspicious numbers
grep -r "[0-9]\{2,\}" api/*.py | grep -v "test_" | grep -v "\.pyc"
```

**Every number should either:**

- Be a named constant
- Have a comment explaining it
- Be obviously self-documenting (like `range(10)`)

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

**Untested code is broken code you haven't discovered yet.**

### 1. Missing Test Files

Every router MUST have a test file:

```bash
# List all routers
ls api/*.py | grep -v __init__ | grep -v shared

# List all test files
ls tests/test_*.py
```

**Map routers to tests:**

| Router           | Test File               | Status      |
| ---------------- | ----------------------- | ----------- |
| `api/pricing.py` | `tests/test_pricing.py` | ✓ / MISSING |
| `api/status.py`  | `tests/test_status.py`  | ✓ / MISSING |
| ...              | ...                     | ...         |

**Missing test file = IMMEDIATE FIX REQUIRED**

### 2. Uncovered Code

Check the coverage report:

```bash
pytest --cov=api --cov-report=term-missing
```

Look for the "Missing" column. Each line number listed is a potential bug.

**Prioritize:**

1. Error handling code - Most likely to have bugs
2. Edge cases - Most likely to be forgotten
3. Main functionality - Should already be covered, but verify

### 3. Flaky Tests

Run tests 3 times:

```bash
pytest && pytest && pytest
```

**Any test that fails intermittently is WORSE than no test.** It trains you to ignore failures.

### 4. Widget Integration

Are all widgets tested in `test_widget_integration.py`?

For each widget in `widgets/*.html`:

- [ ] Widget loads without error
- [ ] API endpoint responds
- [ ] Key elements present in HTML

---

## Section 5: Cursor Rules Audit

**Rules are only useful if they're accurate.** Outdated rules are worse than no rules - they mislead.

```bash
# List all rules
ls .cursor/rules/*.mdc
```

### For Each Rule File, Verify:

| Check                   | Question                                      | If No                   |
| ----------------------- | --------------------------------------------- | ----------------------- |
| Still accurate?         | Does rule match current codebase?             | Update rule             |
| Reference impl correct? | Does `error_decoder.py` match what rule says? | Update one or the other |
| No contradictions?      | Does this rule conflict with any other?       | Resolve conflict        |
| Frontmatter correct?    | Proper activation metadata?                   | Fix frontmatter         |

### Specific Checks

1. **`ai-buzz-tools.mdc`**
   - Does reference implementation section still point to correct files?
   - Are code examples still valid?
   - Are decision frameworks still being followed?

2. **`file-protection.mdc`**
   - Are tier assignments still correct?
   - Any new critical files not listed?
   - Any listed files that no longer exist?

3. **`project-context.mdc`**
   - Is current status accurate?
   - Are "completed" items actually complete?
   - Are constraints still valid?

**Rule drift is invisible until it causes problems.** Catch it now.

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

---

## Accountability

**At the end of every review, answer:**

1. **Is the codebase better or worse than last review?** (Be honest)
2. **What did I fix?** (List specific changes)
3. **What did I defer?** (List with justification - "not important" is not justification)
4. **What's the test coverage trend?** (Up, down, or stagnant?)
5. **When is the next review?** (Schedule it now)

### Red Flags You're Cutting Corners

- "Tests pass" without checking coverage
- "Patterns look consistent" without actually comparing files
- "No major issues" on every review (impossible - something always needs work)
- Skipping the full review for months in a row

**This codebase is your product's foundation.** Shortcuts here become user-facing bugs.
