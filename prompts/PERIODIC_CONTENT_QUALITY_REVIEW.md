# Periodic Content Quality Review

Run this prompt to audit live pages for rendering issues, compare local vs WordPress content, and review prose quality.

---

## Quick Start

**Run in Cursor chat:**

```
@prompts/PERIODIC_CONTENT_QUALITY_REVIEW.md

Run a full content quality review.
```

---

## Context

This audit focuses on content quality and live page rendering. Key files:

- **Content files:** `content/tools/*.html` - Source of truth (HTML with YAML frontmatter)
- **WordPress sync:** `scripts/wp_pages.py` - Push/pull commands
- **Quality rules:** `.cursor/rules/seo-content-strategy.mdc`

Review the SEO rules before starting: `@.cursor/rules/seo-content-strategy.mdc`

---

## Section 0: Generate Fresh Screenshots (REQUIRED)

Before analyzing any pages, you MUST generate fresh segmented screenshots:

```bash
python scripts/screenshot_pages.py --all --format segments --clean
```

The `--clean` flag removes any existing screenshots first, ensuring you're working with fresh captures.

This creates viewport-sized PNG segments in `screenshots/` directory:
- `ai-pricing-calculator-001.png`, `ai-pricing-calculator-002.png`, etc.
- Each segment is 1920x1080 at full resolution
- Segments overlap slightly to ensure complete coverage

### Why Segmented Screenshots Are Required

1. **Full resolution** - Each segment captures details at readable size
2. **No compression** - Unlike full-page captures of very long pages (5000+ px)
3. **Optimal for AI analysis** - Standard-sized images analyze better than extremely tall ones
4. **Complete coverage** - Overlapping segments ensure nothing is missed

### Analysis Workflow

1. Run the screenshot capture command above
2. Use the Read tool to view each PNG segment for every page
3. For each segment, check:
   - Table column alignment
   - Code block formatting (monospace font, proper indentation)
   - Header hierarchy and sizing (H3 > H4)
   - List bullet/number alignment
   - Spacing between sections
   - Widget rendering (if visible in segment)
4. Document issues with specific segment number and description

**DO NOT skip this step.** DOM-only analysis misses visual formatting issues.

---

## Section 1: Live Page Rendering Check

Fetch each live tool page and check for rendering issues.

### Pages to Check

| Page | URL |
|------|-----|
| Status | https://www.ai-buzz.com/ai-status |
| Error Decoder | https://www.ai-buzz.com/ai-error-decoder |
| Pricing Calculator | https://www.ai-buzz.com/ai-pricing-calculator |
| Tools Landing | https://www.ai-buzz.com/ai-tools |

### What to Look For

1. **Duplicate headings** - Page title (from Bricks) + content H2 should NOT create double headings
2. **Widget loading** - Does the widget embed load correctly?
3. **Broken formatting** - Lists, code blocks, tables rendering properly?
4. **Mobile responsiveness** - Check at 375px width
5. **Missing content** - Is all content from the local file showing?

### How to Check

Use the WebFetch tool or browser to fetch each page:

```
Fetch https://www.ai-buzz.com/ai-status and check for:
- Any duplicate H1/H2 headings
- Widget script tag presence
- All expected sections present
```

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Duplicate H1 | Old markdown conversion bug | Re-push HTML content |
| Missing content | Never pushed after local edit | Push local file |
| Widget not loading | Script blocked or JS error | Check browser console |
| Broken tables | HTML table syntax error | Fix in local file, re-push |

---

## Section 2: Local vs Live Comparison

Compare local content files against what's rendered on WordPress.

### Run Diff for Each Page

```bash
# Check each page
python scripts/wp_pages.py diff --slug ai-status
python scripts/wp_pages.py diff --slug ai-error-decoder
python scripts/wp_pages.py diff --slug ai-pricing-calculator
python scripts/wp_pages.py diff --slug ai-tools
python scripts/wp_pages.py diff --slug ai-openai-429-errors
python scripts/wp_pages.py diff --slug ai-openai-rate-limits
python scripts/wp_pages.py diff --slug ai-openai-vs-anthropic-pricing
```

### Interpret Results

- **Local much longer than remote** → Content never pushed. Run `push --file`.
- **Remote much longer than local** → WordPress edited directly. Run `pull --slug` to sync.
- **Similar length** → Content is likely in sync.

### If Out of Sync

```bash
# Push local to WordPress (local is source of truth)
python scripts/wp_pages.py push --file content/tools/[slug].html

# Or pull from WordPress (if WordPress has newer content)
python scripts/wp_pages.py pull --slug [slug]
```

---

## Section 3: Prose Quality Audit

Review each content file for clarity and value.

### Quality Checklist

For each content file, check:

- [ ] **No redundancy** - Same information not repeated in multiple sections
- [ ] **Clear language** - Avoids jargon, explains technical terms
- [ ] **Scannable** - Uses headers, bullets, and code blocks effectively
- [ ] **Value density** - Every section earns its place (no filler)
- [ ] **Action-oriented** - Tells users what to do, not just what exists

### Red Flags

| Issue | Example | Fix |
|-------|---------|-----|
| Redundant sections | FAQ repeats intro content | Consolidate or remove |
| Wall of text | 10+ line paragraphs | Break up with headers/bullets |
| Vague language | "various issues may occur" | Be specific with examples |
| Missing examples | "implement retries" with no code | Add code example |
| Self-congratulatory | "our amazing tool" | Focus on user benefit |

### Content Length Guidelines

| Page Type | Target Lines | Current |
|-----------|--------------|---------|
| Tool page (widget-focused) | 100-200 | Check with `wc -l` |
| Guide page (content-focused) | 200-350 | Check with `wc -l` |

```bash
# Check line counts
wc -l content/tools/*.html | sort -n
```

---

## Section 4: User-First Review

Read each page from a user's perspective.

### Questions to Ask

1. **Can users complete their task in under 60 seconds?**
   - Widget should be prominent and immediately usable
   - No signup required for core functionality

2. **Is the most important info above the fold?**
   - Widget or key action should be visible without scrolling
   - Intro should explain value proposition in 1-2 sentences

3. **Are CTAs clear without being pushy?**
   - "Subscribe for alerts" is good
   - "DON'T MISS OUT! SIGN UP NOW!" is bad

4. **Does the FAQ answer real questions?**
   - Check analytics for common search queries
   - Review support requests or comments

5. **Are internal links helpful?**
   - Related tools section should link to genuinely related content
   - Links should use descriptive anchor text

### Visual Verification Checklist

Using the segmented screenshots from Section 0, verify:

- [ ] Fresh segmented screenshots generated before review
- [ ] ALL segments for each page inspected (not just first/last)
- [ ] Table column alignment verified in relevant segments
- [ ] Code block formatting correct (monospace, proper indentation)
- [ ] Header hierarchy visually clear (H3 larger than H4)
- [ ] List alignment proper (bullets/numbers line up)
- [ ] Spacing between sections appropriate
- [ ] Widgets render correctly
- [ ] No content appearing as wall of text (indicates HTML not rendering)

---

## Output Template

Copy and fill this out:

```markdown
## Content Quality Review - [DATE]

### Live Page Rendering
| Page | Status | Issues Found |
|------|--------|--------------|
| ai-status | OK / Issues | [list] |
| ai-error-decoder | OK / Issues | [list] |
| ai-pricing-calculator | OK / Issues | [list] |
| ai-tools | OK / Issues | [list] |

### Local vs Live Sync
| Page | Local (chars) | Remote (chars) | Status |
|------|---------------|----------------|--------|
| ai-status | X | X | In sync / Local newer / Remote newer |
| ... | | | |

### Prose Quality
| Page | Lines | Issues | Action |
|------|-------|--------|--------|
| ai-status.html | X | [issue] | [action] |
| ... | | | |

### User Experience
- [ ] All widgets load correctly
- [ ] Key actions above the fold
- [ ] CTAs are clear but not pushy
- [ ] FAQ answers real questions

### Actions Taken
- [ ] Pushed X pages to WordPress
- [ ] Fixed rendering issue on X
- [ ] Improved prose on X

### Notes for Next Review
- [Anything to watch for]
```

---

## Partial Reviews

**Live rendering only:**
```
@prompts/PERIODIC_CONTENT_QUALITY_REVIEW.md

Run section 1 only - check live pages for rendering issues.
```

**Sync check only:**
```
@prompts/PERIODIC_CONTENT_QUALITY_REVIEW.md

Run section 2 only - compare local vs WordPress content.
```

**Prose quality only:**
```
@prompts/PERIODIC_CONTENT_QUALITY_REVIEW.md

Run sections 3 and 4 - review prose quality and user experience.
```

---

## Relationship to Other Prompts

```
PERIODIC_CONTENT_FRESHNESS.md
└── Focus: Is data accurate? Are hardcoded values correct?

PERIODIC_SEO_CONTENT_AUDIT.md
└── Focus: Is content driving traffic? Internal linking correct?

PERIODIC_CONTENT_QUALITY_REVIEW.md (this prompt)
└── Focus: Is content rendering correctly? Is prose clear and valuable?
```

Run all three periodically - they catch different issues.

---

## When to Run This Review

- **After pushing content** - Verify it rendered correctly
- **Monthly** - Catch drift between local and WordPress
- **After complaints** - If users report issues with a page
- **Before major launches** - Ensure all pages are in good shape
