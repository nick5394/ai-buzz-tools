# Page Audit

**One question: Is this page ready to ship?**

This prompt produces a honest assessment of page quality with specific, actionable fixes.

---

## Before You Start

### Generate Fresh Screenshots (Required)

```bash
python scripts/screenshot_pages.py --all --format segments --jpeg --clean
```

### Read the HTML Source (Required)

Screenshots show what users see. HTML source shows the truth.

**Always read the content file before auditing:**

```bash
# Read the page content
cat content/tools/ai-[slug].html
```

**What to check in HTML:**

| Check | How | Why |
|-------|-----|-----|
| SEO meta | Look at frontmatter `seo_title:` and `seo_description:` | Empty = critical fix needed |
| Line count | `wc -l content/tools/ai-[slug].html` | Under 100 (tool) or 200 (guide) = thin content |
| Internal links | `grep 'href="/ai-' content/tools/ai-[slug].html` | Missing links = orphan page risk |
| WordPress sync | `python scripts/wp_pages.py diff --slug [slug]` | >5% drift = push needed |

**The HTML is the source of truth. If screenshots and HTML conflict, trust the HTML.**

### Check Data Freshness (Can Block Review)

```bash
grep -h "last_updated" data/*.json
```

| File | Stale After | If Stale |
|------|-------------|----------|
| `pricing_data.json` | 7 days | **STOP.** Run `python scripts/sync_pricing_from_litellm.py --apply` first. |
| `error_patterns.json` | 30 days | Note it, continue review. |
| `status_providers.json` | 90 days | Note it, continue review. |

---

## The Review

### Step 1: First Impression (2 minutes)

Look at the first screenshot of each page. Don't analyze - just react.

**Answer these honestly:**

1. If this were a job applicant's portfolio piece, would you hire them?
2. Would a developer trust this site enough to enter their email?
3. If you showed this to a designer at Stripe, what would they criticize first?

**Score: 1-10**

| Score | Meaning | Reference |
|-------|---------|-----------|
| 9-10 | Indistinguishable from Stripe/Linear | Would proudly show anyone |
| 7-8 | Professional, minor gaps | Would show to colleagues |
| 5-6 | Functional but clearly less polished | Would hesitate to share |
| 3-4 | Amateur, significant issues | Would be embarrassed |
| 1-2 | Broken or unusable | Would not show anyone |

**You MUST give a number.** "It's fine" is not a score.

**If score is below 7:** Write down exactly what's dragging it down before continuing. These are your critical issues.

---

### Step 2: Technical Verification (5 minutes)

Check these. Each is Pass or Fail - no maybes.

| Check | How to Verify | Pass/Fail |
|-------|---------------|-----------|
| **Widget loads** | Screenshot shows widget content, not empty space | |
| **No duplicate H1** | Only one main heading at top of page | |
| **Grids display correctly** | Cards in rows, not stacked vertically | |
| **Data matches** | Prices/models in content match widget | |
| **WordPress in sync** | `python scripts/wp_pages.py diff --slug [slug]` shows <5% drift | |
| **Links work** | Internal links go to correct pages | |

**Any Fail = must be in fix plan.**

---

### Step 3: Content Value (3 minutes)

Skim the content. Answer:

1. **5-second test:** Can you understand what this tool does in 5 seconds?
2. **Delete test:** If you deleted 30% of the content, would the page be worse?
3. **Developer test:** Would a senior engineer at Google find this useful?

**If any answer is "no":** Note what specifically fails.

---

### Step 4: The Verdict

Based on Steps 1-3, choose ONE:

| Verdict | Criteria | Action |
|---------|----------|--------|
| **Ship as-is** | Score 7+, all technical checks pass, content valuable | Done. Move on. |
| **Ship with fixes** | Score 5-6, OR 1-2 technical fails, OR minor content issues | Fix issues, then ship. |
| **Do not ship** | Score below 5, OR critical technical fail, OR content fundamentally broken | Major rework needed. |

---

## Required Output: Fix Plan

Your review MUST end with this. No fix plan = incomplete review.

```markdown
## Page Audit: [Page Name] - [Date]

### Scores
- **First Impression:** X/10
- **Technical:** X/6 passed
- **Verdict:** [Ship as-is / Ship with fixes / Do not ship]

### What's Good
- [At least one specific thing that works well]

### Critical Fixes (blocks shipping)

| Issue | File | Specific Change | Time |
|-------|------|-----------------|------|
| [Issue] | `content/tools/X.html` | [Exact change] | Xm |

### Minor Fixes (improve but don't block)

| Issue | File | Specific Change | Time |
|-------|------|-----------------|------|
| [Issue] | `content/tools/X.html` | [Exact change] | Xm |

### Total Estimated Time: Xm
```

**Every fix MUST have:**
- Specific file path
- Exact change (not "update content" but "change X to Y in section Z")
- Time estimate

---

## Quick Reference

### Pages to Audit

| Page | URL | Type |
|------|-----|------|
| Pricing Calculator | /ai-pricing-calculator | Tool |
| Error Decoder | /ai-error-decoder | Tool |
| Status | /ai-status | Tool |
| Tools Landing | /ai-tools | Landing |
| 429 Errors Guide | /ai-openai-429-errors | Guide |
| Rate Limits Guide | /ai-openai-rate-limits | Guide |
| Pricing Comparison | /ai-openai-vs-anthropic-pricing | Guide |

### WordPress Sync Commands

```bash
# Check sync status
python scripts/wp_pages.py diff --slug [slug]

# Push local to WordPress
python scripts/wp_pages.py push --file content/tools/[file].html

# Pull WordPress to local
python scripts/wp_pages.py pull --slug [slug]
```

---

## Partial Audits

**Single page:**
```
@prompts/PAGE_AUDIT.md Run audit for /ai-pricing-calculator only.
```

**Visual only (after design changes):**
```
@prompts/PAGE_AUDIT.md Run Step 1 only for all pages. Just first impressions and scores.
```

**Technical only (after deploys):**
```
@prompts/PAGE_AUDIT.md Run Step 2 only. Verify widgets load and data is synced.
```

---

## Forcing Honesty

**Rules for the reviewer:**

1. **You MUST find at least one issue.** If you found zero, you weren't looking. Every page has something.

2. **"Looks fine" is not allowed.** Specific observations only.

3. **Compare to Stripe.** Literally open stripe.com/pricing in another tab. What's the gap?

4. **If you're unsure, it's a problem.** Uncertainty = user will also be confused.

5. **Score first, justify after.** Don't let analysis talk you into a higher score.

---

## Common Issues Reference

Consult this section when you encounter specific problems. Don't read during the review - reference when needed.

### Widget Not Loading

**Symptoms:** Empty space where widget should be, loading spinner never completes.

**Causes:**
1. Render cold start (wait 30s, refresh)
2. Wrong `data-tool` attribute (valid: `pricing`, `status`, `error-decoder`, `tools-landing`)
3. API down (check https://ai-buzz-tools.onrender.com/health)

---

### Duplicate H1 Headings

**Symptoms:** Page title appears twice at top.

**Cause:** Content file has `<h1>` but Bricks template already provides one.

**Fix:** Remove `<h1>` from content file. Start with `<p>` intro instead.

---

### Grid Layout Broken

**Symptoms:** Cards stacked vertically instead of in grid. Large empty spaces.

**Cause:** WordPress `wpautop` adding `<p></p>` tags inside grid containers.

**Fix:** Remove blank lines between grid items. Ensure `</div><div>` has no whitespace between.

```html
<!-- BAD -->
<div style="display: grid;">
<div>Card 1</div>

<div>Card 2</div>
</div>

<!-- GOOD -->
<div style="display: grid;"><div>Card 1</div><div>Card 2</div></div>
```

---

### Content Not Synced

**Symptoms:** Local file differs significantly from live page.

**Diagnosis:** `python scripts/wp_pages.py diff --slug [slug]` shows >5% difference.

**Fix:**
- If local is newer: `python scripts/wp_pages.py push --file content/tools/[file].html`
- If WordPress is newer: `python scripts/wp_pages.py pull --slug [slug]`

---

### Stale Data in Content

**Symptoms:** Prices or model names in content don't match widget/data files.

**Fix:**
1. Check what `data/pricing_data.json` says
2. Update hardcoded values in content file to match
3. Push to WordPress

---

### Broken Internal Links

**Symptoms:** Links go to 404 or wrong page.

**Common mistakes:**
- Missing leading slash: `ai-status` should be `/ai-status`
- Old slugs: `/ai-is-openai-down` should be `/ai-status`

---

### Styles Not Applying

**Symptoms:** Inline styles being ignored.

**Fix:** Add `!important` to critical layout styles:
```html
<div style="display: grid !important; gap: 24px !important;">
```

---

## When to Run This Audit

| Trigger | What to Run |
|---------|-------------|
| After pushing content | Full audit on changed pages |
| After data file updates | Step 2 (technical) on tool pages |
| Weekly maintenance | Full audit on all pages |
| Before major launches | Full audit + extra scrutiny |
| User reports issue | Full audit on reported page |

---

## Accountability

After every audit, you should be able to answer:

1. What score did each page get?
2. What specific issues did you find?
3. What's the fix plan with time estimates?
4. When will fixes be done?

If you can't answer these, the audit was incomplete.
