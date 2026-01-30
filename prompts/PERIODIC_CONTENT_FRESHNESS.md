# Periodic Content Freshness Review

Run this prompt after updating data files, or when you suspect content pages have drifted from the source of truth.

## Context

Content pages often contain hardcoded values (prices, model names, limits) that can become stale when data files are updated. This review ensures consistency.

Key files:

- **Data files:** `data/*.json` - Source of truth for pricing, errors, status
- **Content pages:** `content/tools/*.md` - WordPress page content
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

| File | Update Frequency | Action if Stale |
|------|------------------|-----------------|
| `pricing_data.json` | Weekly | Run sync script |
| `error_patterns.json` | Monthly | Manual review |
| `status_providers.json` | Quarterly | Check endpoints still work |

### If Pricing Data is Stale

Run the sync script to pull latest from LiteLLM:

```bash
# Preview changes first
python scripts/sync_pricing_from_litellm.py --verbose

# Apply if changes look good
python scripts/sync_pricing_from_litellm.py --apply
```

**Note what changed:**
- New models added?
- Prices updated?
- Models removed?

---

## Section 2: Content-Data Consistency

Check that hardcoded values in content match the data files.

### Pricing Calculator Page

The page at `content/tools/ai-pricing-calculator.md` has a "Quick Price Comparison" table with hardcoded prices.

**Check these values against `data/pricing_data.json`:**

```bash
# View the comparison table in the content
grep -A 10 "Quick Price Comparison" content/tools/ai-pricing-calculator.md

# Compare against actual data
cat data/pricing_data.json | grep -A 5 '"gpt-4o"'
cat data/pricing_data.json | grep -A 5 '"claude-3-5-sonnet"'
cat data/pricing_data.json | grep -A 5 '"gemini-1.5-pro"'
```

**Checklist:**
- [ ] GPT-4o prices match?
- [ ] GPT-4o-mini prices match?
- [ ] Claude 3.5 Sonnet prices match?
- [ ] Claude 3 Haiku prices match?
- [ ] Gemini 1.5 Pro prices match?
- [ ] Gemini 1.5 Flash prices match?

### Model Names Check

Search content for potentially deprecated model names:

```bash
# Look for old model names that might be deprecated
grep -r "gpt-3.5-turbo-0301\|gpt-4-0314\|claude-2\|claude-instant" content/tools/
```

**If deprecated models found:**
- Update to current model names
- Or remove if no longer relevant

### Error Decoder Content

Check `content/tools/ai-error-decoder.md` mentions providers we actually support:

```bash
# List providers in error patterns
cat data/error_patterns.json | grep '"provider":' | sort | uniq

# Check content mentions same providers
grep -i "openai\|anthropic\|google\|mistral" content/tools/ai-error-decoder.md
```

---

## Section 3: WordPress Sync Check

Ensure local content files match what's published on WordPress.

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
```

**If differences found:**
- Local is newer? Push to WordPress: `python scripts/wp_pages.py push --file content/tools/[file].md`
- WordPress is newer? Pull to local: `python scripts/wp_pages.py pull --slug [slug]`
- Conflict? Review manually and decide which version to keep

---

## Section 4: External Links Spot Check

Verify that external links in data files still work.

### Pricing Sources

Check 2-3 pricing source URLs from `data/pricing_data.json`:

```bash
# List all source URLs
cat data/pricing_data.json | grep -o 'https://[^"]*' | head -5
```

**Manually verify these load correctly:**
- [ ] OpenAI pricing page
- [ ] Anthropic pricing page
- [ ] Google AI pricing page

### Error Documentation URLs

Check 2-3 `docs_url` values from `data/error_patterns.json`:

```bash
# List doc URLs
cat data/error_patterns.json | grep '"docs_url"' | head -5
```

**Manually verify these link to relevant documentation:**
- [ ] First docs link works?
- [ ] Second docs link works?
- [ ] Third docs link works?

### Status Page URLs

Check status page URLs from `data/status_providers.json`:

```bash
cat data/status_providers.json | grep '"status_page"'
```

---

## Output Template

Copy and fill this out:

```markdown
## Content Freshness Review - [DATE]

### Data Freshness Status
| File | Last Updated | Status |
|------|--------------|--------|
| pricing_data.json | [date] | Fresh/Stale |
| error_patterns.json | [date] | Fresh/Stale |
| status_providers.json | [date] | Fresh/Stale |

### Pricing Sync
- Sync run: Yes/No
- New models: [list]
- Price changes: [list]

### Content-Data Mismatches
| Page | Issue | Action |
|------|-------|--------|
| [page] | [mismatch] | [fix] |

### WordPress Sync Status
| Page | Status |
|------|--------|
| ai-pricing-calculator | In sync / Local newer / WP newer |
| ai-error-decoder | In sync / Local newer / WP newer |
| ai-status | In sync / Local newer / WP newer |

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
