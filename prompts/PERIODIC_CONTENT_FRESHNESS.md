# Periodic Content Freshness Review

Run this prompt after updating data files, or when you suspect content pages have drifted from the source of truth.

---

## Your Mindset: Fact Checker

**Stale data destroys trust instantly.** A user who sees wrong pricing will never trust your tool again.

This review exists to answer: **Is every piece of data on every page accurate right now?**

"Probably accurate" is not acceptable. Verify or fix.

---

## Failure Criteria (Fix Immediately)

These issues mean users are seeing WRONG information:

- [ ] **Pricing table doesn't match `pricing_data.json`** - Users making wrong decisions
- [ ] **Model names are deprecated** - Users searching for ghosts
- [ ] **External links are broken** - Users hitting dead ends
- [ ] **Local vs WordPress drift >10% character difference** - Something is out of sync
- [ ] **Data file `last_updated` >30 days old** - Data is probably stale

---

## Success Criteria

The content passes freshness review when:

1. **All hardcoded values match data files** - Verified, not assumed
2. **All external links work** - Tested, not guessed
3. **Local and WordPress are in sync** - Diff shows minimal difference
4. **Data files updated within 30 days** - Or explicit reason why not
5. **No deprecated model names** - Verified against provider docs

---

## Context

Content pages often contain hardcoded values (prices, model names, limits) that can become stale when data files are updated. This review ensures consistency.

Key files:

- **Data files:** `data/*.json` - Source of truth for pricing, errors, status
- **Content pages:** `content/tools/*.html` - WordPress page content
- **WordPress sync:** `scripts/wp_pages.py` - Push/pull/diff commands

Review the rules before starting: `@.cursor/rules/seo-content-strategy.mdc`

---

## Section 1: Check Data Freshness

Review the `_metadata.last_updated` field in each data file:

```bash
# Check all data file timestamps
grep -h "last_updated" data/*.json
```

**Data files to check:**

| File                    | Update Frequency | Stale After | Action if Stale             |
| ----------------------- | ---------------- | ----------- | --------------------------- |
| `pricing_data.json`     | Weekly           | 7 days      | Run sync script IMMEDIATELY |
| `error_patterns.json`   | Monthly          | 30 days     | Manual review               |
| `status_providers.json` | Quarterly        | 90 days     | Check endpoints still work  |

### Staleness is a BUG

**Stale pricing data means users are making decisions with wrong numbers.**

This is not "something to update when we have time." This is a bug in production.

### If Pricing Data is Stale (>7 days)

Run the sync script to pull latest from LiteLLM:

```bash
# Preview changes first
python scripts/sync_pricing_from_litellm.py --verbose

# Apply if changes look good
python scripts/sync_pricing_from_litellm.py --apply
```

**Document what changed (don't skip this):**

- New models added: [list]
- Prices updated: [list models with price changes]
- Models removed: [list]

**If prices changed, the pricing calculator page content might need updating too.** Check Section 2.

### If Error Patterns are Stale (>30 days)

Ask: "Have OpenAI, Anthropic, or Google changed their error messages in the last month?"

Check their changelog/release notes. New API versions often mean new error formats.

---

## Section 2: Content-Data Consistency

Check that hardcoded values in content match the data files. **Every mismatch is a lie to users.**

### Pricing Calculator Page

The page at `content/tools/ai-pricing-calculator.html` may have hardcoded prices.

**Check these values against `data/pricing_data.json`:**

```bash
# View the comparison table in the content (if exists)
grep -A 10 "Quick Price Comparison" content/tools/ai-pricing-calculator.html

# Compare against actual data
cat data/pricing_data.json | grep -A 5 '"gpt-4o"'
cat data/pricing_data.json | grep -A 5 '"claude-3-5-sonnet"'
cat data/pricing_data.json | grep -A 5 '"gemini-1.5-pro"'
```

**Verify EACH value (don't skim):**

| Model                    | Content Says | Data File Says | Match? |
| ------------------------ | ------------ | -------------- | ------ |
| GPT-4o input             | $            | $              | ✓/✗    |
| GPT-4o output            | $            | $              | ✓/✗    |
| GPT-4o-mini input        | $            | $              | ✓/✗    |
| GPT-4o-mini output       | $            | $              | ✓/✗    |
| Claude 3.5 Sonnet input  | $            | $              | ✓/✗    |
| Claude 3.5 Sonnet output | $            | $              | ✓/✗    |
| ...                      | ...          | ...            | ...    |

**Any ✗ = FIX IMMEDIATELY.** Users are seeing wrong prices.

### Model Names Check

Search content for deprecated model names:

```bash
# Look for old model names that might be deprecated
grep -r "gpt-3.5-turbo-0301\|gpt-4-0314\|claude-2\|claude-instant" content/tools/
```

**Deprecated model names in content are embarrassing.** It signals "this site isn't maintained."

**If deprecated models found:**

1. Check if model still works (some deprecated names still function)
2. Update to current model name if there's an equivalent
3. Remove if no longer relevant
4. Never leave deprecated names as-is

### Error Decoder Content

Check `content/tools/ai-error-decoder.html` mentions providers we actually support:

```bash
# List providers in error patterns
cat data/error_patterns.json | grep '"provider":' | sort | uniq

# Check content mentions same providers
grep -i "openai\|anthropic\|google\|mistral" content/tools/ai-error-decoder.html
```

**If content mentions a provider we don't support, that's misleading.** Fix it.

---

## Section 3: WordPress Sync Check

Ensure local content files match what's published on WordPress. **Drift means one version is wrong.**

### List All Pages

```bash
python scripts/wp_pages.py list
```

### Check Each Page for Drift

Run diff for each content page:

```bash
# Check each page
python scripts/wp_pages.py diff --slug ai-pricing-calculator
python scripts/wp_pages.py diff --slug ai-error-decoder
python scripts/wp_pages.py diff --slug ai-status
python scripts/wp_pages.py diff --slug ai-tools
python scripts/wp_pages.py diff --slug ai-openai-429-errors
python scripts/wp_pages.py diff --slug ai-openai-rate-limits
python scripts/wp_pages.py diff --slug ai-openai-vs-anthropic-pricing
```

### Interpreting Drift

| Character Difference | Interpretation                   | Action                                 |
| -------------------- | -------------------------------- | -------------------------------------- |
| <5%                  | Minor drift, probably whitespace | Verify, then sync local → WordPress    |
| 5-20%                | Significant drift                | Review what's different before syncing |
| >20%                 | Major drift                      | Something is wrong. Investigate.       |

**If differences found:**

1. **Local is newer?** (You edited locally but forgot to push)
   - Push to WordPress: `python scripts/wp_pages.py push --file content/tools/[file].html`
   - Verify the push succeeded with another diff

2. **WordPress is newer?** (Someone edited in WordPress)
   - This shouldn't happen. Local is source of truth.
   - Pull to local: `python scripts/wp_pages.py pull --slug [slug]`
   - Then review what changed and why

3. **Conflict?** (Both changed)
   - This is a problem. Review manually.
   - Decide which version is correct
   - Sync and document what you chose

**"In sync" is the only acceptable state.** Any drift gets resolved NOW, not later.

---

## Section 4: External Links Spot Check

Verify that external links in data files still work. **Broken links destroy user trust.**

### Pricing Sources (MUST CHECK)

```bash
# List all source URLs
cat data/pricing_data.json | grep -o 'https://[^"]*' | head -5
```

**Actually load each URL.** Don't assume they work because they worked last month.

| URL               | Status             | Notes |
| ----------------- | ------------------ | ----- |
| OpenAI pricing    | ✓ / 404 / Redirect |       |
| Anthropic pricing | ✓ / 404 / Redirect |       |
| Google AI pricing | ✓ / 404 / Redirect |       |

**Redirects are warnings.** If a URL redirects, update to the new URL.
**404s are emergencies.** Fix immediately.

### Error Documentation URLs

```bash
# List doc URLs
cat data/error_patterns.json | grep '"docs_url"' | head -5
```

**Check at least 3 random docs URLs:**

| URL     | Status             | Notes |
| ------- | ------------------ | ----- |
| [url 1] | ✓ / 404 / Redirect |       |
| [url 2] | ✓ / 404 / Redirect |       |
| [url 3] | ✓ / 404 / Redirect |       |

**If any doc URL is broken, users clicked "Learn more" and got a 404.** That's a bad experience.

### Status Page URLs

```bash
cat data/status_providers.json | grep '"status_page"'
```

**Load each status page URL.** These are critical - if they don't work, the status tool is useless.

| Provider  | Status Page URL | Works? |
| --------- | --------------- | ------ |
| OpenAI    |                 | ✓ / ✗  |
| Anthropic |                 | ✓ / ✗  |
| Google    |                 | ✓ / ✗  |

**Any broken status URL = IMMEDIATE FIX.** The whole tool depends on these.

---

## Output Template

Copy and fill this out:

```markdown
## Content Freshness Review - [DATE]

### Data Freshness Status

| File                  | Last Updated | Status      |
| --------------------- | ------------ | ----------- |
| pricing_data.json     | [date]       | Fresh/Stale |
| error_patterns.json   | [date]       | Fresh/Stale |
| status_providers.json | [date]       | Fresh/Stale |

### Pricing Sync

- Sync run: Yes/No
- New models: [list]
- Price changes: [list]

### Content-Data Mismatches

| Page   | Issue      | Action |
| ------ | ---------- | ------ |
| [page] | [mismatch] | [fix]  |

### WordPress Sync Status

| Page                  | Status                           |
| --------------------- | -------------------------------- |
| ai-pricing-calculator | In sync / Local newer / WP newer |
| ai-error-decoder      | In sync / Local newer / WP newer |
| ai-status             | In sync / Local newer / WP newer |

### External Links

- Broken links found: [list or "None"]

### Actions Taken

- [ ] Updated pricing table in ai-pricing-calculator.md
- [ ] Pushed X pages to WordPress
- [ ] Fixed broken links

### Notes for Next Review

- [Anything to watch for]
```

---

## Usage

**Full review:**

```
@prompts/PERIODIC_CONTENT_FRESHNESS.md

Run a full content freshness review.
```

**After pricing sync:**

```
@prompts/PERIODIC_CONTENT_FRESHNESS.md

I just ran the pricing sync script. Check if content pages need updating.
```

**WordPress sync only:**

```
@prompts/PERIODIC_CONTENT_FRESHNESS.md

Run section 3 only - check WordPress sync status for all pages.
```

---

## Accountability

**At the end of every review, answer:**

1. **How old is the pricing data?** (Days since `last_updated`)
2. **How many hardcoded values did I verify?** (Should be ALL of them)
3. **How many broken links did I find?** (Should be zero)
4. **What is out of sync with WordPress?** (Should be nothing)
5. **What did I fix?** (List specific changes)

### Freshness Tracking

Keep a log:

| Date       | Pricing Age | Broken Links | WordPress Drift | Actions          |
| ---------- | ----------- | ------------ | --------------- | ---------------- |
| YYYY-MM-DD | X days      | X            | X pages         | [what you fixed] |

**If pricing is consistently >7 days old, automate the sync.** Manual processes get forgotten.

### The Trust Test

Ask yourself: "If a user compared our pricing numbers to the official provider pages right now, would they match?"

If you're not 100% confident, **verify.**
