# Periodic Analytics Review

Run this prompt when you want to understand what users are searching for and prioritize improvements based on real usage data.

---

## Your Mindset: Data Detective

**Data without action is waste. Action without data is guessing.**

This review exists to answer: **What are users telling us they need that we're not providing?**

Every unmatched search is a user who came to your tool and left disappointed. Every missing model is a potential customer who found nothing. **These are failures, not "opportunities."**

---

## Failure Criteria (Fix Immediately)

These issues mean the review has uncovered urgent problems:

- [ ] **Same error searched 5+ times but not in patterns** - Users are failing repeatedly
- [ ] **Popular model missing from pricing** - Users can't get the info they came for
- [ ] **Provider with zero checks** - Entire provider is invisible or broken
- [ ] **No data since last deploy** - Analytics might be broken

---

## Success Criteria

The analytics review succeeds when:

1. **Top 5 unmatched errors are addressed** - Added to patterns or documented why not
2. **Top 5 missing models are resolved** - Added or documented as invalid
3. **Usage trends are understood** - Which tools growing? Which stagnant?
4. **A prioritized action list exists** - Not just findings, but what to do about them

---

## Context

This review uses data from the analytics system to identify gaps in your tools. Key files:

- **Analytics script:** `scripts/analytics.py` - Pulls stats and generates reports
- **Latest report:** `data/analytics/latest_report.md` - Generated insights
- **Error patterns:** `data/error_patterns.json` - Patterns to potentially expand
- **Pricing data:** `data/pricing_data.json` - Models to potentially add

Review the rules before starting: `@.cursor/rules/ai-buzz-tools.mdc`

---

## Section 1: Pull Latest Data

Run these commands to get current analytics:

```bash
# Activate environment first
source venv/bin/activate

# Pull in-memory stats from production (resets on deploy)
python scripts/analytics.py pull-stats

# Generate the insights report
python scripts/analytics.py report
```

**Review the generated report:**

```bash
# Read the report
cat data/analytics/latest_report.md
```

**Report:**
- Total tool uses since last deploy
- Token usage distribution
- Any gaps detected

---

## Section 2: Analyze Gaps

Run the gaps command for actionable insights:

```bash
python scripts/analytics.py gaps
```

**What to look for (be thorough, not dismissive):**

### 1. Unmatched Error Patterns

These are users who came for help and got nothing.

| Frequency | Interpretation | Required Action |
|-----------|----------------|-----------------|
| 5+ searches | Multiple users hit this | Add pattern TODAY |
| 2-4 searches | Real problem, not one-off | Add pattern THIS WEEK |
| 1 search | Could be typo or edge case | Document, watch for recurrence |

**Don't dismiss unmatched errors.** Each one represents a frustrated user who may not come back.

### 2. Missing Pricing Models

These are users who couldn't complete their task.

For each missing model, verify:
- **Does the model exist?** (Check official provider page)
- **Is it GA or preview?** (Preview models change frequently)
- **Is it in LiteLLM?** (If yes, run sync)

**Don't assume typos.** Users often know model names better than you think.

### 3. Provider Popularity

| Finding | Interpretation | Action |
|---------|----------------|--------|
| Provider with 50%+ of checks | High demand, ensure excellent coverage | Audit all patterns/models for this provider |
| Provider with <5% of checks | Low demand OR poor discoverability | Check if provider is visible in UI |
| Provider with 0 checks | Broken or invisible | URGENT: Investigate immediately |

**Questions to answer WITH DATA:**
- What are the top 5 unmatched error searches? (List them)
- What are the top 5 missing model searches? (List them)
- What percentage of searches match vs don't match?
- Are users searching for providers we don't support? (Which ones?)

---

## Section 3: Prioritize Additions

Based on gaps found, prioritize what to add. **Every gap needs a decision, not a "maybe later."**

### Error Patterns

For each unmatched error, evaluate:

1. **Frequency** - How many times was it searched?
2. **Actionability** - Can we provide a useful fix?
3. **Provider coverage** - Do we have other errors for this provider?

**Decision framework (no wiggle room):**

| Searches | Decision | Timeline |
|----------|----------|----------|
| 5+ | Add pattern | TODAY - This is failing users repeatedly |
| 2-4 | Add if fix is clear | THIS WEEK |
| 1 | Document and monitor | Check again next review |

**For each error you decide NOT to add, document WHY:**
- "Can't provide actionable fix" - Acceptable
- "Too provider-specific" - Acceptable
- "Seems like a typo" - Only if you verified
- "Not a priority" - NOT ACCEPTABLE. Users needed this.

### Pricing Models

For each missing model, check:

1. **Does it exist?** - Search official provider pricing page
2. **Is it in LiteLLM?** - Run `python scripts/sync_pricing_from_litellm.py` to check
3. **Is it GA?** - Skip beta/preview only if <3 searches

**Decision framework:**

| Finding | Action | Timeline |
|---------|--------|----------|
| Model in LiteLLM | Run sync script | TODAY |
| Model exists, not in LiteLLM | Add manually | THIS WEEK |
| Model doesn't exist | Verify it's a typo, document | NOTE |
| Preview model, 3+ searches | Add anyway (users want it) | THIS WEEK |

**Don't hide behind "it's preview."** If users are searching for it, they need it.

---

## Section 4: Implement Changes

Based on your prioritization, make the changes:

### Adding Error Patterns

1. Open `data/error_patterns.json`
2. Copy an existing pattern as a template
3. Fill in the fields:

```json
{
  "id": "provider_error_type",
  "provider": "Provider Name",
  "provider_id": "provider",
  "error_keywords": ["keyword1", "keyword2"],
  "title": "Human-readable title",
  "explanation": "What this error means",
  "fix": "1. Step one\n2. Step two",
  "severity": "error|warning|info",
  "common": true|false,
  "docs_url": "https://..."
}
```

4. Test: `pytest tests/test_error_decoder.py -v`

### Adding Pricing Models

**Option A: Sync from LiteLLM (preferred)**

```bash
python scripts/sync_pricing_from_litellm.py --verbose  # Preview
python scripts/sync_pricing_from_litellm.py --apply    # Apply
```

**Option B: Add manually**

1. Open `data/pricing_data.json`
2. Find the provider section
3. Add the model following existing format
4. Update `_metadata.last_updated`

---

## Output Template

Copy and fill this out:

```markdown
## Analytics Review - [DATE]

### Data Summary
- Stats pulled: [timestamp]
- Total tool uses: [count]
- Days since last deploy: [estimate]

### Gaps Found

#### Unmatched Errors (Top 5)
| Error Search | Count | Action |
|--------------|-------|--------|
| [error text] | X | Add/Skip/Investigate |

#### Missing Models (Top 5)
| Model Search | Count | Action |
|--------------|-------|--------|
| [model name] | X | Sync/Add manually/Skip |

### Changes Made
- [ ] Added X error patterns
- [ ] Added X pricing models
- [ ] Ran pricing sync

### Notes for Next Review
- [Anything to watch for]
```

---

## Usage

**Full review:**
```
@prompts/PERIODIC_ANALYTICS_REVIEW.md

Run a full analytics review and implement high-priority additions.
```

**Just check gaps:**
```
@prompts/PERIODIC_ANALYTICS_REVIEW.md

Run sections 1-2 only - just show me the gaps, don't make changes.
```

**Add specific pattern:**
```
@prompts/PERIODIC_ANALYTICS_REVIEW.md

Add an error pattern for "context length exceeded" errors for OpenAI.
```

---

## Accountability

**At the end of every review, answer:**

1. **How many unmatched searches were there?** (Number, not "some")
2. **How many did I address?** (Should be 100% of high-frequency)
3. **What patterns did I add?** (List them)
4. **What did I decide NOT to add?** (List with reasons)
5. **What's the trend?** (Are gaps increasing or decreasing over time?)

**"No significant gaps" should be rare.** Users are always searching for things you don't have. If you found nothing, the analytics might be broken.

### Trend Tracking

Keep a running log:

| Date | Unmatched Errors | Missing Models | Patterns Added | Models Added |
|------|------------------|----------------|----------------|--------------|
| YYYY-MM-DD | X | X | X | X |

**If unmatched errors are increasing, you're falling behind user needs.**
