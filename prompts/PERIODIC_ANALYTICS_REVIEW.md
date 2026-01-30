# Periodic Analytics Review

Run this prompt when you want to understand what users are searching for and prioritize improvements based on real usage data.

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

**What to look for:**

1. **Unmatched Error Patterns**
   - Errors users searched for that didn't match any pattern
   - High-frequency unmatched errors = high-priority additions

2. **Missing Pricing Models**
   - Models users searched for that aren't in pricing data
   - Check if model exists (might be typo vs real gap)

3. **Provider Popularity**
   - Which providers are users checking most?
   - Any providers with zero checks? (might indicate discovery problem)

**Questions to answer:**
- What are the top 5 unmatched error searches?
- What are the top 5 missing model searches?
- Are users searching for providers we don't support?

---

## Section 3: Prioritize Additions

Based on gaps found, prioritize what to add:

### Error Patterns

For each unmatched error, evaluate:

1. **Frequency** - How many times was it searched?
2. **Actionability** - Can we provide a useful fix?
3. **Provider coverage** - Do we have other errors for this provider?

**Decision framework:**
- 5+ searches → Add immediately
- 2-4 searches → Add if fix is clear
- 1 search → Note for later, might be one-off

### Pricing Models

For each missing model, check:

1. **Does it exist?** - Search official provider pricing page
2. **Is it in LiteLLM?** - Run `python scripts/sync_pricing_from_litellm.py` to check
3. **Is it GA?** - Skip beta/preview models unless frequently requested

**Decision framework:**
- Model exists in LiteLLM → Run sync script
- Model exists but not in LiteLLM → Add manually to `pricing_data.json`
- Model doesn't exist → User probably made a typo

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
