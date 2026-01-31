# Tool Launch Audit

**One question: Does this tool's content ecosystem work as a system?**

This prompt produces an honest assessment of a tool AND all its related content. Use before launching a new tool, promoting existing tools, or quarterly to catch drift.

**PAGE_AUDIT asks:** "Is this one page ready?"
**TOOL_LAUNCH_AUDIT asks:** "Does this tool + supporting content work together?"

---

## When to Run This

| Trigger | Why |
|---------|-----|
| Before launching a new tool | Catch gaps before users see them |
| Before promoting a tool (social, SEO push) | Don't promote broken ecosystems |
| Quarterly per tool | Catch drift, new cannibalization issues |
| After adding a new supporting post | Verify it fits the ecosystem |

---

## Before You Start

### Generate Fresh Screenshots

```bash
python scripts/screenshot_pages.py --all --format segments --jpeg --clean
```

### Read ALL HTML Source Files (Critical)

**Screenshots show appearance. HTML source shows the truth.**

For ecosystem audits, you MUST read every HTML file to:
- Check SEO meta completeness
- Count actual lines
- Extract all internal links
- Compare content for overlap/duplication

```bash
# Read all ecosystem pages at once
for page in ai-error-decoder ai-openai-429-errors ai-openai-rate-limits ai-openai-errors; do
  echo "=== content/tools/${page}.html ==="
  head -20 "content/tools/${page}.html"  # Frontmatter
  wc -l "content/tools/${page}.html"     # Line count
  grep 'href="/ai-' "content/tools/${page}.html" | head -10  # Links
  echo ""
done
```

**Quick checks from HTML:**

| Check | Command | What to Look For |
|-------|---------|------------------|
| SEO meta | `grep "seo_title:\|seo_description:" content/tools/*.html` | Empty values = critical fix |
| Line counts | `wc -l content/tools/ai-*.html \| sort -n` | Under minimums = thin content |
| All links | `grep -h 'href="/ai-' content/tools/*.html \| sort \| uniq -c` | Missing relationships |
| Content overlap | Read similar sections side-by-side | Copy-paste = cannibalization sign |

**For cannibalization checks:** Read the actual content of potentially overlapping pages side-by-side. Similar section headings, similar code examples, or similar explanations = overlap.

### Identify the Tool Ecosystem

Before auditing, map out what exists. **You cannot audit what you haven't identified.**

```bash
# List all content pages
ls -la content/tools/*.html

# Check what's live on WordPress
python scripts/wp_pages.py list
```

---

## The Audit

### Step 1: Map the Ecosystem (5 minutes)

**Identify EVERY page related to this tool.**

Fill out this table completely. Don't skip pages because they "probably don't matter."

```markdown
## Ecosystem: [Tool Name]

### Hub Page (The Tool)
| Page | URL | Lines | Has Widget | SEO Meta |
|------|-----|-------|------------|----------|
| [Tool name] | /ai-[slug] | X | Yes/No | Complete/Partial/Missing |

### Spoke Pages (Supporting Content)
| Page | URL | Lines | Type | Primary Query Target |
|------|-----|-------|------|---------------------|
| [Guide 1] | /ai-[slug] | X | Guide/Comparison | "[search query]" |
| [Guide 2] | /ai-[slug] | X | Guide/Comparison | "[search query]" |
```

**If you can't identify the primary search query a page targets, that page has no reason to exist.**

---

### Step 2: Quick Quality Gate (10 minutes)

Run a fast quality check on EVERY page in the ecosystem. This is triage, not a full PAGE_AUDIT.

For each page, answer:

| Check | Pass Criteria | Hub | Spoke 1 | Spoke 2 | Spoke 3 |
|-------|--------------|-----|---------|---------|---------|
| **Loads correctly** | Widget renders, no errors | | | | |
| **Meets line minimum** | Hub: 100+, Guide: 200+ | | | | |
| **SEO meta complete** | seo_title AND seo_description filled | | | | |
| **WordPress synced** | <5% drift on diff check | | | | |
| **Has Related Tools** | Links to 3+ other pages | | | | |

**Any FAIL here = must be fixed before this audit can pass.**

```bash
# Quick check: SEO meta status for all pages
grep -l "seo_title:" content/tools/*.html | while read f; do
  echo "=== $f ==="
  grep "seo_title:" "$f"
  grep "seo_description:" "$f"
done
```

---

### Step 3: Search Intent Analysis (10 minutes)

**This is where cannibalization hides.**

For each page in the ecosystem, write down:

1. **What exact query would someone Google to find this page?**
2. **What is the searcher trying to DO?** (Learn? Fix? Compare? Use a tool?)
3. **Does any other page in the ecosystem target the same query?**

```markdown
### Intent Map

| Page | Target Query | Intent Type | Overlap Risk |
|------|-------------|-------------|--------------|
| /ai-error-decoder | "ai error decoder" | Transactional (use tool) | None |
| /ai-openai-429-errors | "openai 429 error fix" | Troubleshooting (solve problem) | None |
| /ai-openai-errors | "openai api errors" | Informational (learn) | HIGH with error-decoder? |
```

**Intent Types:**
- **Transactional:** User wants to DO something (use a tool, calculate, check)
- **Troubleshooting:** User has a specific problem to solve (fix error, debug)
- **Informational:** User wants to LEARN (what are rate limits, how does X work)
- **Comparison:** User wants to DECIDE (which is cheaper, which is better)

**The Rule:** Each page MUST have a unique intent. If two pages serve the same intent, one should be merged or deleted.

---

### Step 4: Cannibalization Check (5 minutes)

**Cannibalization = two of YOUR pages competing for the same search query.**

This is SEO suicide. Google picks one (often the wrong one), and both rank worse than a single strong page would.

**For each pair of pages that might overlap, answer:**

| Page A | Page B | Same Query? | Same Intent? | Verdict |
|--------|--------|-------------|--------------|---------|
| error-decoder | openai-errors | Possibly | Possibly | **INVESTIGATE** |

**How to decide:**

```
Same query + Same intent = MERGE (one page should absorb the other)
Same query + Different intent = DIFFERENTIATE (clarify what each does)
Different query + Same intent = OK (different entry points to same need)
Different query + Different intent = IDEAL (each page has unique purpose)
```

**Signs of cannibalization:**
- You can't explain in one sentence why BOTH pages should exist
- Content sections are copy-pasted between pages
- "Related Tools" links between them feel forced
- You'd struggle to tell a user which page to read first

**Prove it with HTML - read both files side-by-side:**

```bash
# Compare section headings between two pages
grep "<h[234]>" content/tools/ai-error-decoder.html
grep "<h[234]>" content/tools/ai-openai-errors.html

# Look for similar content patterns
# If both pages have "Rate Limit Errors (429)" sections with similar content = OVERLAP
```

**Overlap Checklist (check the actual HTML):**

| Check | How to Verify | If Yes |
|-------|---------------|--------|
| Same H2/H3 headings? | Compare `grep "<h[23]>" file1 file2` | Strong overlap signal |
| Same code examples? | Read code blocks in both | Definite overlap |
| Same error types covered? | Read content sections | Consider merging |
| Same FAQ questions? | Compare FAQ sections | Consolidate |

**If you find >30% content overlap, one page should absorb the other.**

**If you find cannibalization, you MUST decide:**
1. Which page is stronger? (More content, better quality, higher potential)
2. Merge the weaker into the stronger, OR
3. Delete the weaker and redirect

**"We'll differentiate them later" is not acceptable.** Decide now.

---

### Step 5: Internal Linking Audit (5 minutes)

**A content ecosystem without proper linking is just a collection of orphan pages.**

Check every link relationship:

```markdown
### Link Matrix

| From ↓ / To → | error-decoder | 429-errors | rate-limits | openai-errors |
|---------------|---------------|------------|-------------|---------------|
| error-decoder | - | ✓ | ✓ | ? |
| 429-errors | ✓ | - | ✓ | ✗ |
| rate-limits | ✓ | ✓ | - | ✗ |
| openai-errors | ✓ | ✓ | ? | - |
```

**Requirements (non-negotiable):**

1. **Hub links to ALL spokes** - The tool page must link to every supporting guide
2. **Spokes link back to hub** - Every guide must link to the tool
3. **Spokes link to related spokes** - Guides should cross-reference each other
4. **No orphans** - Every page has at least 2 inbound links

**Check with grep:**

```bash
# Find what each page links to
for f in content/tools/ai-error-decoder.html content/tools/ai-openai-429-errors.html; do
  echo "=== Links in $f ==="
  grep -o 'href="/ai-[^"]*"' "$f" | sort -u
done
```

---

### Step 6: Content Gap Analysis (5 minutes)

**What questions does the ecosystem NOT answer?**

Think like a developer using your tool:

1. What would they ask after using the tool?
2. What would they search for before finding the tool?
3. What edge cases aren't covered?
4. What related problems exist that you don't address?

```markdown
### Gap Analysis

| Question a User Might Have | Answered Where? | Gap? |
|---------------------------|-----------------|------|
| "How do I fix 429 errors?" | /ai-openai-429-errors | No |
| "What are my current rate limits?" | /ai-openai-rate-limits | No |
| "Is the API down right now?" | /ai-status | No |
| "How do I handle Anthropic 529 errors?" | Nowhere | **YES** |
```

**Gaps are opportunities, not failures.** But you should know what they are.

---

### Step 7: Depth Distribution (3 minutes)

**Is the content weight distributed correctly?**

The hub (tool page) should be:
- Focused on the TOOL functionality
- Quick reference, not exhaustive guide
- Entry point that links OUT to deeper content

The spokes (supporting content) should be:
- Deep dives on specific topics
- Long-form, substantive content
- Answer specific search queries thoroughly

**Check the balance:**

| Page | Lines | Role | Correct? |
|------|-------|------|----------|
| error-decoder (hub) | 327 | Tool + reference | Maybe too heavy? |
| 429-errors (spoke) | 307 | Deep troubleshooting | Correct |
| rate-limits (spoke) | ??? | Reference guide | ??? |

**Warning signs:**
- Hub is heavier than spokes = spokes might be too thin
- Hub duplicates spoke content = unnecessary overlap
- Spoke is thinner than hub = spoke might not justify existing

---

### Step 8: The Verdict

Based on Steps 1-7, choose ONE:

| Verdict | Criteria | Action |
|---------|----------|--------|
| **Ready to promote** | All quality gates pass, no cannibalization, linking complete, no critical gaps | Ship it, promote it |
| **Fix then promote** | Minor issues: missing SEO meta, incomplete linking, small gaps | Fix issues, then promote |
| **Restructure first** | Cannibalization found, OR major gaps, OR content weight wrong | Merge/delete/create pages first |
| **Not ready** | Multiple quality failures, fundamental problems | Major rework needed |

---

## Required Output

Your audit MUST end with this. No summary = incomplete audit.

```markdown
## Tool Ecosystem Audit: [Tool Name] - [Date]

### Ecosystem Map

**Hub:** /ai-[tool] (X lines)
**Spokes:**
- /ai-[guide-1] (X lines) - "[target query]"
- /ai-[guide-2] (X lines) - "[target query]"

### Quality Gate Results

| Page | Lines | SEO Meta | WordPress Sync | Links Out |
|------|-------|----------|----------------|-----------|
| [hub] | X | ✓/✗ | ✓/✗ | ✓/✗ |
| [spoke 1] | X | ✓/✗ | ✓/✗ | ✓/✗ |

### Cannibalization Assessment

| Risk | Pages | Decision |
|------|-------|----------|
| HIGH/MEDIUM/NONE | [pages] | Merge/Differentiate/OK |

### Internal Linking Status

- Hub → All Spokes: ✓/✗
- Spokes → Hub: ✓/✗
- Spoke ↔ Spoke: ✓/✗
- Orphan pages: [list or "None"]

### Content Gaps Identified

1. [Gap description] - Priority: High/Medium/Low
2. [Gap description] - Priority: High/Medium/Low

### Verdict: [Ready to promote / Fix then promote / Restructure first / Not ready]

### Actions Required

| Priority | Action | Page(s) | Time |
|----------|--------|---------|------|
| P0 (now) | [action] | [files] | Xm |
| P1 (this week) | [action] | [files] | Xm |
| P2 (this month) | [action] | [files] | Xm |

### Total Estimated Time: Xm
```

---

## Forcing Honesty

**Rules for the reviewer:**

1. **You MUST find at least one issue.** Perfect ecosystems don't exist. If you found nothing, you weren't looking.

2. **"They're different enough" is not allowed.** If you can't articulate WHY two pages both need to exist in one sentence, there's overlap.

3. **Every gap is a conscious choice.** You can choose not to fill a gap, but you must acknowledge it exists.

4. **Linking is binary.** A link exists or it doesn't. "They're kind of connected" means they're not connected.

5. **Cannibalization is worse than a gap.** Two competing pages hurt more than one missing page. When in doubt, merge.

6. **The hub serves the tool, not the content.** If your tool page is becoming a reference guide, you need more spokes.

---

## Tool Ecosystems Reference

### Error Decoder Ecosystem

| Page | Type | Target Query |
|------|------|--------------|
| /ai-error-decoder | Hub | "ai error decoder", "decode api error" |
| /ai-openai-429-errors | Spoke | "openai 429 error", "rate limit error fix" |
| /ai-openai-rate-limits | Spoke | "openai rate limits", "openai tier limits" |
| /ai-openai-errors | Spoke | ??? (Potential overlap with hub) |

### Pricing Calculator Ecosystem

| Page | Type | Target Query |
|------|------|--------------|
| /ai-pricing-calculator | Hub | "ai pricing calculator", "gpt-4 cost calculator" |
| /ai-openai-vs-anthropic-pricing | Spoke | "openai vs anthropic pricing", "gpt-4 vs claude cost" |

### Status Page Ecosystem

| Page | Type | Target Query |
|------|------|--------------|
| /ai-status | Hub | "is openai down", "ai api status" |
| (no spokes yet) | - | Consider: "openai outage history", "when does openai go down" |

---

## Quick Start

**Full ecosystem audit:**
```
@prompts/TOOL_LAUNCH_AUDIT.md

Audit the Error Decoder ecosystem. Include:
- /ai-error-decoder (hub)
- /ai-openai-429-errors
- /ai-openai-rate-limits  
- /ai-openai-errors

Provide screenshots for each page.
```

**Cannibalization check only:**
```
@prompts/TOOL_LAUNCH_AUDIT.md

Run Steps 3-4 only. Check if /ai-error-decoder and /ai-openai-errors cannibalize each other.
```

**Pre-launch check:**
```
@prompts/TOOL_LAUNCH_AUDIT.md

I'm about to launch the [X] tool. Audit the full ecosystem and tell me if it's ready to promote.
```

---

## Relationship to Other Prompts

```
PAGE_AUDIT.md
└── Single page quality check. "Is this page ready?"

TOOL_LAUNCH_AUDIT.md (this prompt)
└── Ecosystem health check. "Does this tool + content work as a system?"

PERIODIC_SEO_CONTENT_AUDIT.md
└── Site-wide SEO check. "Is all content performing?"

PERIODIC_CONTENT_FRESHNESS.md
└── Data accuracy check. "Is information current?"
```

**Typical workflow:**
1. Build tool + supporting content
2. Run PAGE_AUDIT on each page individually
3. Run TOOL_LAUNCH_AUDIT on the ecosystem
4. Fix issues found
5. Launch/promote
6. Run PERIODIC audits monthly/quarterly

---

## Accountability

After every ecosystem audit, you should be able to answer:

1. **How many pages are in this ecosystem?** (Exact number)
2. **What query does each page target?** (One sentence each)
3. **Is there any cannibalization?** (Yes/No with evidence)
4. **Is linking complete?** (Yes/No with specifics)
5. **What gaps exist?** (List them)
6. **What's the verdict?** (Ready/Fix/Restructure/Not ready)
7. **What's the fix plan?** (Specific actions with time estimates)

If you can't answer these, the audit was incomplete.
