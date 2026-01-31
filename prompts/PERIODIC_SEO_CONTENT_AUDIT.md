# Periodic SEO & Content Audit

Run this prompt monthly to analyze content performance, audit internal linking, and identify SEO optimization opportunities.

---

## Your Mindset: Growth Skeptic

**Traffic that doesn't convert is vanity. Conversions that don't grow are failure.**

This audit exists to answer one question: **Is content driving users to tools, and are tools converting to email signups?**

If the answer is "I don't know" - that's a failure. Set up tracking.
If the answer is "No" - that's a failure. Fix the content.
If the answer is "Sort of" - that's still a failure. "Sort of" doesn't grow a business.

---

## Failure Criteria (Fix Immediately)

These issues BLOCK the review. Stop and fix:

- [ ] **GA4 not configured** - Can't measure = can't improve
- [ ] **Any page has zero organic traffic** - Content isn't being found
- [ ] **Orphan pages** - Pages with no inbound links (invisible to users)
- [ ] **Tool pages with <50 views/month** - Tools aren't being discovered
- [ ] **Conversion rate <1%** - Tool use to email signup (if measurable)

---

## Success Criteria

The audit passes when:

1. **Every page has measurable traffic** - No pages with zero views
2. **Internal linking is complete** - Every page linked from 2+ other pages
3. **Guide pages drive tool usage** - Visible correlation in data
4. **Email signups are growing** - Week over week, month over month
5. **No thin content** - Every page exceeds minimum line count

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

**Questions to answer (with numbers, not vibes):**

1. Which tool pages get the most traffic? **Write the exact numbers.**
2. Which guide pages get the most traffic? **Write the exact numbers.**
3. Are guide pages driving traffic to related tool pages? **What's the evidence?**
4. What's the ratio of guide page views to tool page views? **Calculate it.**

**Benchmarks (be honest about where you stand):**

| Metric                   | Target | Acceptable | Failing |
| ------------------------ | ------ | ---------- | ------- |
| Tool page views/month    | 500+   | 100-500    | <100    |
| Guide page views/month   | 300+   | 50-300     | <50     |
| Landing page views/month | 200+   | 50-200     | <50     |

**If any page is in "Failing" category, that's a problem that needs a plan.**

---

## Section 2: Internal Linking Audit

Run the automated linking audit:

```bash
python scripts/analytics.py seo-audit
```

**What to look for (these are not suggestions, they're requirements):**

1. **Orphan pages** - Pages not linked FROM other pages = **IMMEDIATE FIX REQUIRED**
2. **Weak pages** - Pages with fewer than 3 outbound links = **FIX THIS WEEK**
3. **Duplicate links** - Same page linked multiple times = **FIX TODAY**
4. **Missing connections** - Obvious relationships not linked = **FIX THIS WEEK**

**Standards (non-negotiable):**

| Requirement                                  | Why It Matters                                |
| -------------------------------------------- | --------------------------------------------- |
| Every page links OUT to 3+ related pages     | Keeps users on site, builds topic authority   |
| Every page is linked FROM 2+ other pages     | Orphan pages don't rank, can't be discovered  |
| No duplicate links in Related Tools sections | Looks sloppy, wastes link equity              |
| Tool pages link to related guide pages       | Guides have more SEO content, help tools rank |
| Guide pages link to relevant tools           | Converts informational traffic to tool usage  |

**The linking structure is a SYSTEM.** One weak link affects everything.

### If Orphan Pages Found

This is an emergency. An orphan page:

- Won't rank in Google (no internal link equity)
- Won't be discovered by users (no navigation path)
- Is wasted effort (you built it but nobody sees it)

**Fix immediately:** Add links from at least 2 related pages.

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

For each content page, verify against `seo-content-strategy.mdc` standards.

### Minimum Line Counts (Hard Requirements)

| Page Type                    | Minimum Lines | Failing                                   |
| ---------------------------- | ------------- | ----------------------------------------- |
| Tool page (widget-focused)   | 100+          | <100 = thin content penalty risk          |
| Guide page (content-focused) | 200+          | <200 = won't rank for competitive queries |

```bash
# Check line counts - flag anything below minimum
wc -l content/tools/*.html | sort -n
```

**Thin content is not acceptable.** Google penalizes thin content. Users don't trust thin content. Fix it.

### SEO Meta Check (These Directly Impact Click-Through Rate)

```bash
# Check SEO titles (should be under 60 chars)
grep "seo_title:" content/tools/*.html

# Check SEO descriptions (should be under 155 chars)
grep "seo_description:" content/tools/*.html
```

**Non-negotiable requirements:**

- [ ] All seo_title values under 60 characters (truncated titles look broken)
- [ ] All seo_description values under 155 characters (truncated descriptions hurt CTR)
- [ ] All pages have UNIQUE titles (duplicate titles = Google confusion)
- [ ] Titles include primary keyword (no keyword = won't rank)
- [ ] Descriptions include call-to-action (no CTA = lower click-through)

### Meta Quality Assessment

For each page, answer:

1. **Would you click this in Google results?** If no, rewrite it.
2. **Does the title promise something specific?** "AI Pricing Calculator" > "Pricing Tool"
3. **Does the description explain what the user will get?** Not what the page is.

**Example of bad vs good:**

| Bad                          | Good                                                             |
| ---------------------------- | ---------------------------------------------------------------- |
| "AI Error Decoder Tool"      | "Decode AI API Errors Instantly - Fix OpenAI & Anthropic Errors" |
| "A tool for checking prices" | "Compare GPT-4 vs Claude pricing in seconds. Free calculator."   |

### Thin Content Emergency

Any page under minimum lines:

1. **Identify the gap** - What sections are missing?
2. **Add value** - More examples, deeper explanations, code snippets
3. **Don't pad** - Adding fluff is worse than thin content
4. **Push immediately** - Thin content hurts rankings every day it's live

---

## Section 5: Actionable Recommendations

Based on your findings, prioritize improvements. **Everything here needs a deadline.**

### Priority 1: Fix Immediately (Today)

These are emergencies. Don't end the review without fixing:

- [ ] Remove duplicate links
- [ ] Add inbound links to orphan pages
- [ ] Fix any broken links
- [ ] Ensure landing page (`/ai-tools`) is linked from all tool pages

### Priority 2: Fix This Week

These hurt performance but aren't emergencies:

- [ ] Expand pages under minimum line count
- [ ] Add code examples to guide pages missing them
- [ ] Improve FAQ sections with real user questions (not filler)
- [ ] Fix meta titles/descriptions that are too long

### Priority 3: Improve This Month

Optimizations that compound over time:

- [ ] Update meta descriptions for high-traffic pages with low engagement
- [ ] Improve titles for pages with low click-through
- [ ] Consolidate pages competing for same keywords
- [ ] Add schema markup if missing

### Tracking Accountability

**For every recommendation, write:**

1. What exactly needs to change
2. Which file(s) need editing
3. When it will be done (specific date)
4. How you'll verify it worked

**Vague recommendations like "improve content quality" are useless.** Be specific.

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

---

## Accountability

**At the end of every audit, answer:**

1. **What's the current traffic trend?** Up, down, or flat vs last month?
2. **What's blocking growth?** Be specific. "Content quality" is not specific.
3. **What did I fix today?** List the actual changes made.
4. **What's the plan for unfixed issues?** With dates.
5. **What will I measure next time to verify improvement?**

**"No major issues found" is almost never true.** If you found nothing to improve, you weren't looking hard enough.
