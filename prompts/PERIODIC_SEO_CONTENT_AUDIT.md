# Periodic SEO & Content Audit

Run this prompt monthly to analyze content performance, audit internal linking, and identify SEO optimization opportunities.

---

## Quick Start

**Run in Cursor chat:**

```
@prompts/PERIODIC_SEO_CONTENT_AUDIT.md

Run a full SEO content audit.
```

**Or run manually via terminal:**

```bash
# 1. Pull GA4 traffic data (last 30 days)
python scripts/analytics.py pull-ga4 --days 30

# 2. Run internal linking audit
python scripts/analytics.py seo-audit

# 3. Check content line counts
wc -l content/tools/*.md | sort -n
```

---

## Context

This audit focuses on whether content is effectively driving traffic to tools. Key files:

- **Analytics script:** `scripts/analytics.py` - Pulls GA4 data and generates link audit
- **Content pages:** `content/tools/*.md` - WordPress page content
- **SEO rules:** `.cursor/rules/seo-content-strategy.mdc` - Quality standards

**Prerequisite:** GA4 custom dimension for `tool_name` must be configured. See Section 0 if funnel data shows errors.

Review the rules before starting: `@.cursor/rules/seo-content-strategy.mdc`

---

## Section 0: Verify GA4 Configuration

Before running the audit, verify GA4 is properly configured to track tool usage by tool name.

```bash
python scripts/analytics.py pull-ga4 --days 7
```

**Check the output:**

- If funnel data shows `"success": true` with tool breakdowns → GA4 is configured correctly
- If funnel data shows `"success": false` with dimension error → Configure the custom dimension

### Configuring GA4 Custom Dimension (One-Time Setup)

1. Go to **GA4 Admin** → **Data display** → **Custom definitions**
2. Click **Create custom dimension**
3. Configure:
   - Dimension name: `Tool Name`
   - Scope: `Event`
   - Event parameter: `tool_name`
4. Save

**Note:** Custom dimensions take 24-48 hours to populate. Historical data won't backfill.

---

## Section 1: Pull Traffic Data

Get the latest GA4 traffic data:

```bash
# Pull last 30 days of data
python scripts/analytics.py pull-ga4 --days 30
```

**Categorize pages by type:**

| Type         | Pages                                                                                |
| ------------ | ------------------------------------------------------------------------------------ |
| Tool pages   | `/ai-pricing-calculator`, `/ai-error-decoder`, `/ai-status`                          |
| Guide pages  | `/ai-openai-429-errors`, `/ai-openai-rate-limits`, `/ai-openai-vs-anthropic-pricing` |
| Landing page | `/ai-tools`                                                                          |

**Questions to answer:**

1. Which tool pages get the most traffic?
2. Which guide pages get the most traffic?
3. Are guide pages driving traffic to related tool pages?
4. What's the ratio of guide page views to tool page views?

---

## Section 2: Internal Linking Audit

Run the automated linking audit:

```bash
python scripts/analytics.py seo-audit
```

**What to look for:**

1. **Orphan pages** - Pages not linked FROM other pages (poor discoverability)
2. **Weak pages** - Pages with fewer than 3 outbound links (not supporting the network)
3. **Duplicate links** - Same page linked multiple times (cleanup needed)
4. **Missing connections** - Obvious relationships not linked

**Standard to meet:**

- Every page links OUT to at least 3 related pages
- Every page is linked FROM at least 2 other pages
- No duplicate links in Related Tools sections

---

## Section 3: Content-to-Tool Conversion

**If GA4 custom dimension is configured:**

Check the funnel data to see which tools are being used:

```bash
# View the latest GA4 data
cat data/analytics/ga4_*.json | tail -1 | jq '.funnel'
```

**Questions to answer:**

1. Which tools have the highest usage?
2. What's the email signup rate per tool?
3. Are guide pages correlating with tool usage increases?

**If GA4 custom dimension is NOT configured:**

Use proxy metrics:

- Compare traffic to `/ai-openai-429-errors` vs `/ai-error-decoder`
- If guide has more traffic but tool has less, the CTA might need improvement
- Look for scroll depth and engagement metrics

---

## Section 4: SEO Quality Check

For each content page, verify against `seo-content-strategy.mdc` standards:

### Minimum Line Counts

| Page Type                    | Minimum Lines | Check Command                 |
| ---------------------------- | ------------- | ----------------------------- |
| Tool page (widget-focused)   | 100+          | `wc -l content/tools/ai-*.md` |
| Guide page (content-focused) | 200+          | Same                          |

### SEO Meta Check

```bash
# Check SEO titles (should be under 60 chars)
grep "seo_title:" content/tools/*.md

# Check SEO descriptions (should be under 155 chars)
grep "seo_description:" content/tools/*.md
```

**Verify:**

- [ ] All seo_title values under 60 characters
- [ ] All seo_description values under 155 characters
- [ ] All pages have unique titles (no duplicates)

### Thin Content Flag

Any page under 100 lines needs attention:

```bash
wc -l content/tools/*.md | sort -n | head -10
```

---

## Section 5: Actionable Recommendations

Based on your findings, prioritize improvements:

### Priority 1: Fix Structural Issues

- Remove duplicate links
- Add missing inbound links to orphan pages
- Ensure landing page (`/ai-tools`) is linked from tool pages

### Priority 2: Improve Weak Content

- Expand pages under 100 lines
- Add code examples to guide pages missing them
- Improve FAQ sections with real user questions

### Priority 3: Optimize SEO

- Update meta descriptions for high-traffic pages with low engagement
- Improve titles for pages with low click-through
- Consider consolidating pages competing for same keywords

---

## Output Template

Copy and fill this out:

```markdown
## SEO Content Audit - [DATE]

### Traffic Summary (Last 30 Days)

| Page                   | Views | Users | Type    |
| ---------------------- | ----- | ----- | ------- |
| /ai-pricing-calculator | X     | X     | Tool    |
| /ai-error-decoder      | X     | X     | Tool    |
| /ai-status             | X     | X     | Tool    |
| /ai-tools              | X     | X     | Landing |
| /ai-openai-429-errors  | X     | X     | Guide   |
| ...                    |       |       |         |

### Internal Linking Status

- Total pages: X
- Orphan pages (0 inbound): [list]
- Weak pages (<3 outbound): [list]
- Duplicate links found: [list]

### Conversion Metrics

| Tool          | Uses | Email Signups | Conversion |
| ------------- | ---- | ------------- | ---------- |
| pricing       | X    | X             | X%         |
| error-decoder | X    | X             | X%         |
| status        | X    | X             | X%         |

(If custom dimension not configured: "N/A - configure GA4 custom dimension")

### Content Quality

| Page                | Lines | Status               |
| ------------------- | ----- | -------------------- |
| ai-error-decoder.md | X     | OK / Needs expansion |
| ...                 |       |                      |

### Actions Taken

- [ ] Fixed X duplicate links
- [ ] Added inbound links to X orphan pages
- [ ] Expanded X thin pages
- [ ] Updated X SEO meta descriptions

### Notes for Next Audit

- [Anything to watch for]
```

---

## How to Run This Audit

### Option A: Let Cursor Run It (Recommended)

Open Cursor chat and type:

```
@prompts/PERIODIC_SEO_CONTENT_AUDIT.md

Run a full SEO content audit.
```

Cursor will execute all the commands and generate a summary report.

### Option B: Run Manually

**Step 1: Activate your environment**

```bash
cd /Users/nick/Documents/Github/ai-buzz-tools
source .venv/bin/activate
```

**Step 2: Pull GA4 data**

```bash
python scripts/analytics.py pull-ga4 --days 30
```

**Step 3: Run linking audit**

```bash
python scripts/analytics.py seo-audit
```

**Step 4: Check content quality**

```bash
# Line counts (thin content check)
wc -l content/tools/*.md | sort -n

# SEO meta check
grep "seo_title:" content/tools/*.md
```

**Step 5: Review and act on findings**

Use the Output Template above to document findings and track actions.

---

## Partial Audits

**Just check linking:**

```
@prompts/PERIODIC_SEO_CONTENT_AUDIT.md

Run section 2 only - audit internal linking structure.
```

**Traffic analysis only:**

```
@prompts/PERIODIC_SEO_CONTENT_AUDIT.md

Run sections 1 and 3 - analyze traffic and conversion without making changes.
```

**After fixing content:**

```
@prompts/PERIODIC_SEO_CONTENT_AUDIT.md

Re-run the seo-audit command to verify my fixes worked.
```

---

## Relationship to Other Prompts

```
PERIODIC_CONTENT_FRESHNESS.md
└── Focus: Is data accurate? Are WordPress and local in sync?

PERIODIC_ANALYTICS_REVIEW.md
└── Focus: What tool features are users asking for that we don't have?

PERIODIC_SEO_CONTENT_AUDIT.md (this prompt)
└── Focus: Is content driving traffic to tools? What needs SEO attention?
```

Run all three periodically, but they address different concerns.
