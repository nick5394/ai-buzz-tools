# Workflow Guide

This file is for YOUR reference when working with AI agents.

---

## Decision Ownership

| Decision           | Who Decides       | AI Role                              |
| ------------------ | ----------------- | ------------------------------------ |
| What tool to build | YOU               | Suggest options if asked             |
| Feature scope      | YOU               | Propose minimum viable version       |
| Data sources       | YOU               | Research options                     |
| API design         | YOU approve       | Propose based on existing patterns   |
| Implementation     | AI                | Follow patterns from `error_decoder` |
| Test coverage      | AI                | Must hit all endpoints               |
| File structure     | Existing patterns | No new directories without approval  |

---

## Prompt Templates

### New Feature

```markdown
## What I Want

[One sentence describing the feature]

## Scope

- Include: [specific things to build]
- Exclude: [things to NOT build]

## Constraints

- No new dependencies
- Follow error_decoder.py patterns
- No new files in root

## Done When

- [ ] [Specific acceptance criteria]
- [ ] Tests pass
- [ ] Works on mobile (375px)
```

### Bug Fix

```markdown
## The Bug

[What's broken]

## Expected Behavior

[What should happen]

## Files Likely Involved

[List 1-3 files]

## Done When

- [ ] Bug is fixed
- [ ] Existing tests still pass
- [ ] No new bugs introduced
```

### Refactoring

```markdown
## What to Refactor

[Specific code/pattern to change]

## Why

[One sentence justification]

## Scope

- Touch: [specific files]
- Don't touch: [files to leave alone]

## Done When

- [ ] All tests pass
- [ ] Behavior unchanged
- [ ] Code is cleaner/simpler
```

---

## Review Checkpoints

### After Planning (before Composer implements)

- [ ] Scope matches what I asked for (no extras)
- [ ] No new files in forbidden locations
- [ ] No new dependencies added
- [ ] Estimated changes are reasonable (<5 files for simple features)

**Red flags:**

- "We could also add..."
- New directories being created
- Changes to `shared.py` or `main.py`
- More than 5 files modified for a simple feature

### After Implementation

- [ ] Run `pytest` yourself
- [ ] Test the feature manually in browser
- [ ] Check `git diff` — are the changes what you expected?
- [ ] No new files in root directory

**Quick verification:**

```bash
# See what changed
git status
git diff

# Run tests
pytest -v

# Check for new root files (should be empty)
ls -la *.md *.html 2>/dev/null | grep -v README | grep -v TESTING | grep -v WORDPRESS
```

---

## Preventing Scope Creep

### The "Minimum Viable" Rule

Always ask: "What's the smallest thing that would be useful?"

- Bad: "Add sharing features to error decoder"
- Good: "Add a copy button that copies error + solution to clipboard"

### The "One Thing" Rule

Each prompt should do ONE thing. If you find yourself writing "and also...", make it a separate prompt.

- Bad: "Fix the mobile layout and also add dark mode and improve the loading animation"
- Good: Three separate prompts, prioritized

### The "No Surprises" Rule

If AI output includes something you didn't ask for, reject it. Even if it seems useful.

> "I didn't ask for that. Remove it and stick to the original scope."

---

## The Operating Model

```
YOU write prompt → Opus plans → YOU review plan → Composer implements → YOU verify
```

You are the architect. AI is the contractor. The contractor follows your blueprints.
