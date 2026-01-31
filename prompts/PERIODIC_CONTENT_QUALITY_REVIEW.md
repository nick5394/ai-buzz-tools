# Periodic Content Quality Review

Run this prompt to audit live pages for visual quality, rendering issues, local vs WordPress sync, and prose quality.

---

## Your Mindset: Hostile Reviewer

**You are not here to confirm things work. You are here to find problems.**

Approach every page assuming something is broken. Your job is to prove yourself wrong by finding nothing - not to skim and say "looks fine."

**Default assumption:** Every page has at least one issue. If you found zero issues, you weren't looking hard enough.

**Your goal:** Find issues that would make a developer think "this site is amateur" or "I don't trust this tool." Those destroy credibility and kill conversions.

---

## Failure Criteria (Fix Immediately)

These issues BLOCK the review. Stop and fix before continuing:

- [ ] **Broken widget** - Widget area empty or showing error
- [ ] **Duplicate H1** - Multiple H1s on any page (SEO disaster)
- [ ] **Grid layout broken** - Cards stacked vertically when should be grid
- [ ] **Large empty spaces** - More than 30% of page width empty
- [ ] **Console errors** - JavaScript errors in browser console
- [ ] **Missing sections** - FAQ, Related Tools, or main content missing

**If any of these exist, the page is BROKEN. Do not mark the review complete until fixed.**

---

## Success Criteria

A page passes review when:

1. **Visual quality:** Would fit alongside Stripe, Linear, Notion (not "pretty good for a side project")
2. **Widget works:** Loads within 5 seconds, all interactions function
3. **Content renders:** All HTML elements display correctly (tables, code blocks, lists)
4. **Mobile works:** Usable at 375px width
5. **Local/WordPress sync:** Diff shows similar character counts

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
- **Visual quality guide:** `prompts/VISUAL_QUALITY_REVIEW.md` - Comprehensive visual assessment methodology

Review the SEO rules before starting: `@.cursor/rules/seo-content-strategy.mdc`

---

## Section 0: Generate Fresh Screenshots (REQUIRED)

Before analyzing any pages, you MUST generate fresh segmented screenshots:

```bash
python scripts/screenshot_pages.py --all --format segments --jpeg --clean
```

The `--clean` flag removes any existing screenshots first, ensuring you're working with fresh captures.

This creates viewport-sized JPEG segments in `screenshots/` directory:

- `ai-pricing-calculator-001-of-09.jpg`, etc.
- Each segment is 1920x1080 at 2x resolution
- Segments overlap slightly to ensure complete coverage

---

## Section 0.5: Visual Quality Assessment (DO THIS BEFORE TECHNICAL CHECKS)

**This is the most important section.** Before checking any technical details, assess overall visual quality.

### First Impression Test (30 seconds)

Look at the first screenshot segment of each page and answer HONESTLY:

1. **Does this page look professional?** (Yes / No / Unsure)
2. **Would you be embarrassed to show this to a hiring manager?** (Yes / No)
3. **Does this look like a high-quality SaaS/tool website?** (Yes / No)
4. **Would a user trust this site enough to enter their email?** (Yes / No)

**If ANY answer is "No" or "Unsure", STOP. Document what looks wrong. This is a blocking issue.**

"Unsure" is not acceptable as a final answer - it means you need to investigate more.

### Quality Comparison (Be Brutally Honest)

Compare each page to these standards:

- **Gold standard:** Stripe, Linear, Notion, Vercel
- **Good enough:** GitHub, Render, Railway
- **Unacceptable:** Generic WordPress themes, 2015-era Bootstrap sites

Ask: "If I screenshot this and put it next to Stripe's pricing page, would anyone notice a quality gap?"

**The answer is probably yes. Your job is to identify WHAT creates that gap and fix it.**

### Common Quality Gaps to Look For

Don't just look for "broken." Look for "mediocre":

- **Typography:** Are headings the right size? Is line height comfortable? Font weights varied appropriately?
- **Whitespace:** Is spacing consistent? Does content breathe or feel cramped?
- **Alignment:** Are elements aligned to a grid? Any elements that look "off" by a few pixels?
- **Color:** Is the color palette consistent? Any jarring color combinations?
- **Hierarchy:** Is it instantly clear what's most important on the page?

**Mediocre is unacceptable.** Users have seen great design. Anything less than great damages credibility.

### Layout Check

For each page, verify:

| Check            | What to Look For                                                      |
| ---------------- | --------------------------------------------------------------------- |
| Content width    | Is content appropriately wide? Not cramped in narrow center column?   |
| Grid layouts     | Do grids display as grids (multiple columns), not stacked vertically? |
| Spacing          | Consistent margins and padding? No cramped or overly sparse areas?    |
| Visual hierarchy | Clear distinction between headings, subheadings, body text?           |
| Balance          | Content distributed well across the page, not pushed to one side?     |

### Red Flags to Watch For

- Content confined to narrow center column with large empty margins
- Cards/items stacked vertically when they should be in a grid
- Large unexplained empty spaces
- Elements that look misaligned or "off"
- Inconsistent styling between sections
- Page looks different from other pages on the site

### If Issues Found

1. Document the issue clearly: "Content is confined to ~50% page width with large empty gutters"
2. Take note of which screenshot segment shows the issue
3. Investigate the cause (CSS, HTML structure, WordPress/Bricks, wpautop)
4. Do NOT proceed to technical checks until visual issues are understood

**For comprehensive visual assessment methodology, see: `prompts/VISUAL_QUALITY_REVIEW.md`**

---

## Section 1: Live Page Rendering Check

Fetch each live tool page and check for rendering issues.

### Pages to Check

| Page               | URL                                           |
| ------------------ | --------------------------------------------- |
| Status             | https://www.ai-buzz.com/ai-status             |
| Error Decoder      | https://www.ai-buzz.com/ai-error-decoder      |
| Pricing Calculator | https://www.ai-buzz.com/ai-pricing-calculator |
| Tools Landing      | https://www.ai-buzz.com/ai-tools              |

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

### Common Issues Quick Reference

| Issue                     | Cause                                         | Fix                                                     |
| ------------------------- | --------------------------------------------- | ------------------------------------------------------- |
| Duplicate H1              | Old markdown conversion or Bricks template    | Re-push HTML content or fix Bricks template             |
| Missing content           | Never pushed after local edit                 | Push local file                                         |
| Widget not loading        | Script blocked, JS error, or cold start       | Check browser console, wait for Render                  |
| Broken tables             | HTML table syntax error                       | Fix in local file, re-push                              |
| Grid layout broken        | WordPress wpautop adds empty `<p>` tags       | Remove HTML comments and blank lines between grid items |
| Code blocks not formatted | Missing `<pre><code>` or wpautop interference | Use proper code block HTML                              |
| Links not working         | Wrong URL path or missing protocol            | Fix href values                                         |
| Styles not applying       | Inline styles stripped or overridden          | Check Bricks CSS, use !important if needed              |

---

### Issue: Duplicate H1 Headings

**What it looks like:**

- Two H1 headings at the top of the page
- Page title appears twice (once from Bricks template, once from content)

**Visual symptoms in screenshots:**

- "AI Tools" appears as large heading, then again below it
- Awkward spacing at top of page
- SEO warning (multiple H1s hurt rankings)

**How to detect:**

1. **Screenshot inspection**: Look at top of page for repeated titles
2. **MCP browser**: Search for `[level=1]` in snapshot - should only appear once
3. **WebFetch**: Check markdown output for multiple `# Title` patterns

**Common causes:**

1. Bricks template has H1 element + content also has H1
2. Old markdown file had `# Title` that got converted to H1
3. Content starts with `<h1>` when it shouldn't

**How to fix:**

1. Check if Bricks template already provides H1:
   - If yes: Content should NOT have `<h1>` - start with `<p>` or `<h2>`
   - If no: Content should have exactly one `<h1>`

2. Remove duplicate from local file:

   ```html
   <!-- BAD - if Bricks already has H1 -->
   <h1>AI Tools</h1>
   <p>Introduction...</p>

   <!-- GOOD - let Bricks handle H1 -->
   <p>Introduction...</p>
   ```

3. Push and verify:
   ```bash
   python scripts/wp_pages.py push --file content/tools/[slug].html
   # Purge caches
   python scripts/screenshot_pages.py --slug [slug] --format segments --jpeg
   ```

**Prevention:**

- Never put `<h1>` in content files - Bricks template handles it
- Start content with `<p>` intro paragraph
- Use `<h2>` and below for content sections

---

### Issue: Missing Content

**What it looks like:**

- Local file has content that doesn't appear on live page
- Sections are missing from rendered page
- Page is shorter than expected

**Visual symptoms in screenshots:**

- Page ends abruptly
- Expected sections (FAQ, Related Tools) are missing
- Widget area is empty

**How to detect:**

1. **Diff check**:

   ```bash
   python scripts/wp_pages.py diff --slug [slug]
   ```

   - Local much longer than remote = content never pushed

2. **Character count comparison**:
   - Local: 5000 chars, Remote: 2000 chars = missing content

3. **Section checklist**: Verify each expected section appears:
   - [ ] Intro paragraph
   - [ ] Widget embed
   - [ ] Main content sections
   - [ ] FAQ section
   - [ ] Related Tools section

**Common causes:**

1. Edited local file but forgot to push
2. Push command failed silently
3. WordPress truncated content (rare)
4. Wrong file pushed (old version)

**How to fix:**

1. Verify local file has the content:

   ```bash
   wc -l content/tools/[slug].html  # Check line count
   ```

2. Push the content:

   ```bash
   python scripts/wp_pages.py push --file content/tools/[slug].html
   ```

3. Verify push succeeded:

   ```bash
   python scripts/wp_pages.py diff --slug [slug]
   # Chars should now be similar
   ```

4. Purge all caches and verify with screenshot

**Prevention:**

- Always run `push` after editing local files
- Verify with `diff` after pushing
- Keep local files as source of truth

---

### Issue: Widget Not Loading

**What it looks like:**

- Empty space where widget should be
- Loading spinner that never completes
- "Error loading widget" message
- Widget container exists but is empty

**Visual symptoms in screenshots:**

- Blank white space in widget area
- Missing pricing calculator/status cards/error decoder
- Page looks incomplete

**How to detect:**

1. **Screenshot inspection**: Is the widget area empty or showing error?

2. **MCP browser snapshot**: Look for widget container refs:

   ```yaml
   # Widget loaded correctly:
   - generic [ref=e78]:
       - heading "Get Tool Updates" [level=2]
       - textbox "Email address"
       - button "Notify Me"

   # Widget failed to load:
   - paragraph [ref=e76]:
       - generic [ref=e78] # Empty or minimal content
   ```

3. **Screenshot script output**: Check for widget load warnings:

   ```
   ⚠ Widget may not be loaded: Timeout 25000ms exceeded
   ```

4. **Browser console** (via MCP browser_console_messages):
   - JavaScript errors
   - Network request failures
   - CORS errors

**Common causes:**

1. **Render cold start** (most common):
   - Free tier spins down after inactivity
   - First request takes 10-30 seconds
   - Widget times out waiting

2. **Script tag error**:

   ```html
   <!-- Wrong -->
   <script
     src="https://ai-buzz-tools.onrender.com/embed.js"
     data-tool="wrong-name"
   ></script>

   <!-- Correct tool names: pricing, status, error-decoder, tools-landing -->
   ```

3. **API endpoint down**:
   - Check https://ai-buzz-tools.onrender.com/health
   - Check Render dashboard for deploy status

4. **JavaScript blocked**:
   - Ad blocker interference
   - CSP (Content Security Policy) blocking external scripts

**How to fix:**

1. **For cold start issues**:
   - Wait 30 seconds and refresh
   - Screenshot script already has 25s timeout for widgets
   - Consider upgrading Render plan if critical

2. **For script tag issues**:
   - Verify data-tool attribute matches: `pricing`, `status`, `error-decoder`, `tools-landing`
   - Verify script URL is correct: `https://ai-buzz-tools.onrender.com/embed.js`

3. **For API issues**:
   - Check Render dashboard for deployment status
   - Check API health endpoint
   - Review recent commits for breaking changes

4. **Verify fix**:
   ```bash
   # Take screenshot with longer timeout if needed
   python scripts/screenshot_pages.py --slug [slug] --format segments --jpeg
   ```

**Prevention:**

- Use correct data-tool values (documented in WORDPRESS_SETUP.md)
- Monitor Render dashboard for deployment failures
- Consider paid Render tier for no cold starts

---

### Issue: Broken Tables

**What it looks like:**

- Table content appears as plain text
- Columns misaligned
- Missing borders/styling
- Data runs together without separation

**Visual symptoms in screenshots:**

- Text that should be in columns is in a single line
- Pipe characters `|` visible in content
- No visible table structure

**How to detect:**

1. **Screenshot inspection**: Does the table render with proper columns and rows?

2. **Compare to expected**: Tables should have:
   - Clear column headers
   - Aligned data in columns
   - Visible borders or row separation

3. **Check local HTML**: Verify proper table structure

**Common causes:**

1. **Markdown table not converted**:

   ```
   <!-- This is markdown, not HTML - won't render -->
   | Column 1 | Column 2 |
   |----------|----------|
   | Data 1   | Data 2   |
   ```

2. **Malformed HTML table**:

   ```html
   <!-- Missing closing tags -->
   <table>
     <tr>
       <td>Data</td>
     </tr>
   </table>

   <!-- Missing thead/tbody -->
   <table>
     <tr>
       <th>Header</th>
     </tr>
     <tr>
       <td>Data</td>
     </tr>
   </table>
   ```

3. **wpautop interference**: Blank lines inside table converted to `<p>` tags

**Correct table HTML structure:**

```html
<table>
  <thead>
    <tr>
      <th>Header 1</th>
      <th>Header 2</th>
      <th>Header 3</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Data 1</td>
      <td>Data 2</td>
      <td>Data 3</td>
    </tr>
    <tr>
      <td>Data 4</td>
      <td>Data 5</td>
      <td>Data 6</td>
    </tr>
  </tbody>
</table>
```

**wpautop-safe table (no blank lines):**

```html
<table>
  <thead>
    <tr>
      <th>Header 1</th>
      <th>Header 2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Data 1</td>
      <td>Data 2</td>
    </tr>
    <tr>
      <td>Data 3</td>
      <td>Data 4</td>
    </tr>
  </tbody>
</table>
```

**How to fix:**

1. Convert markdown tables to HTML
2. Ensure proper `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>` structure
3. Remove blank lines inside table tags
4. Push and verify

**Prevention:**

- Always use HTML tables, never markdown
- Keep table HTML compact (no blank lines inside)
- Test table rendering locally if possible

---

### Issue: Code Blocks Not Formatted

**What it looks like:**

- Code appears as regular text (no monospace font)
- Code runs together with surrounding text
- Syntax highlighting missing
- Indentation lost

**Visual symptoms in screenshots:**

- Code snippets look like regular paragraphs
- Python/JavaScript code without distinctive styling
- `def function():` appearing in serif font

**How to detect:**

1. **Screenshot inspection**: Is code in monospace font with background?
2. **Check for code styling**: Should have gray/dark background, fixed-width font

**Common causes:**

1. **Missing pre/code tags**:

   ```html
   <!-- BAD - just backticks (markdown) -->
   `code here`

   <!-- BAD - code tag without pre -->
   <code>multi-line code</code>
   ```

2. **wpautop breaking code blocks**:

   ```html
   <!-- BAD - blank lines inside -->
   <pre><code>
   line 1
   
   line 2
   </code></pre>
   ```

**Correct code block HTML:**

```html
<!-- Inline code -->
<code>single_function()</code>

<!-- Multi-line code block -->
<pre><code>def example():
    return "Hello"

result = example()</code></pre>

<!-- With language class for syntax highlighting -->
<pre><code class="language-python">def example():
    return "Hello"</code></pre>
```

**wpautop-safe code block:**

```html
<pre><code class="language-python">def example():
    return "Hello"
result = example()</code></pre>
```

Note: Newlines INSIDE `<pre><code>` are preserved (that's what `<pre>` does). The issue is blank lines that wpautop interprets as paragraph breaks.

**How to fix:**

1. Wrap code in `<pre><code>...</code></pre>`
2. Add language class if syntax highlighting desired
3. Ensure no double-blank-lines inside code blocks
4. Push and verify

**Prevention:**

- Always use `<pre><code>` for multi-line code
- Use `<code>` for inline code references
- Test code block rendering after pushing

---

### Issue: Links Not Working

**What it looks like:**

- Clicking link goes to wrong page
- 404 error when clicking link
- Link goes to external URL when should be internal

**Visual symptoms:**

- Can't verify in static screenshots
- Must test interactively via MCP browser

**How to detect:**

1. **MCP browser inspection**: Check `/url:` values in snapshot

   ```yaml
   - link "Is OpenAI Down?" [ref=e106]:
       - /url: /ai-status # Relative URL - correct
   ```

2. **Check for common mistakes**:
   - Missing leading slash: `ai-status` vs `/ai-status`
   - Wrong path: `/ai-is-openai-down` (old) vs `/ai-status` (new)
   - Accidental external URL

**Common causes:**

1. **Relative vs absolute paths**:

   ```html
   <!-- BAD - missing leading slash -->
   <a href="ai-status">Status</a>

   <!-- GOOD -->
   <a href="/ai-status">Status</a>
   ```

2. **Outdated links after page merges**:
   - `/ai-is-openai-down` → should be `/ai-status`
   - `/ai-openai-errors` → should be `/ai-error-decoder`

3. **Typos in slugs**:

   ```html
   <!-- BAD -->
   <a href="/ai-pricng-calculator">Pricing</a>

   <!-- GOOD -->
   <a href="/ai-pricing-calculator">Pricing</a>
   ```

**How to fix:**

1. Search local file for all `href=` occurrences
2. Verify each link path is correct
3. Update any outdated paths (check SEO rules for merged pages)
4. Push and verify with MCP browser

**Prevention:**

- Use relative paths with leading slash: `/ai-status`
- Check SEO rules for any page merges/redirects
- Verify links after any page restructuring

---

### Issue: Styles Not Applying

**What it looks like:**

- Elements appear unstyled (no colors, borders, etc.)
- Inline styles being ignored
- Layout not matching HTML inline styles

**Visual symptoms in screenshots:**

- Plain text where styled cards expected
- Missing borders, shadows, backgrounds
- Wrong colors or fonts

**How to detect:**

1. **Screenshot comparison**: Does element match intended style?
2. **MCP browser**: Check if style attributes present in DOM
3. **Compare working vs broken**: Same styles work elsewhere?

**Common causes:**

1. **Bricks CSS overriding inline styles**:
   - Bricks has high-specificity CSS
   - May need `!important` to override

2. **WordPress stripping styles**:
   - Some security plugins strip inline styles
   - Check if styles appear in rendered HTML

3. **Typo in style attribute**:

   ```html
   <!-- BAD - typo -->
   <div style="dispaly: grid;">
     <!-- GOOD -->
     <div style="display: grid;"></div>
   </div>
   ```

**How to fix:**

1. **Check if styles are in rendered HTML** (via MCP browser or view source)

2. **If being overridden, add !important:**

   ```html
   <div style="display: grid !important; gap: 24px !important;"></div>
   ```

3. **If being stripped, check WordPress plugins**

**Prevention:**

- Test styles work after pushing
- Use `!important` sparingly for critical layout styles
- Keep inline styles simple; complex styling may need Bricks

---

### WordPress wpautop Issues (CRITICAL)

WordPress's `wpautop` filter automatically converts blank lines, newlines, and certain HTML patterns into `<p></p>` tags. This is the #1 cause of broken layouts on our tool pages.

#### What wpautop Does

| Input Pattern                | What WordPress Outputs              |
| ---------------------------- | ----------------------------------- |
| Two consecutive newlines     | `<p></p>`                           |
| HTML comment on its own line | Often wraps nearby content in `<p>` |
| Blank line inside a `<div>`  | `<p></p>` inside the div            |
| `</div>\n\n<div>`            | `</div><p></p><div>`                |

#### Visual Symptoms (What You'll See in Screenshots)

1. **Grid layout broken**: Items in single column instead of 2-3 columns
2. **Large empty spaces**: Huge gaps on left/right side of content
3. **Cards pushed to one side**: Content hugging right edge with empty left
4. **Inconsistent layouts**: Some grids work, others don't on same page
5. **Unexpected vertical stacking**: Elements that should be side-by-side are stacked

#### How to Detect (Step-by-Step)

**Method 1: Visual Comparison**

1. Look at the screenshot - is the grid displaying correctly?
2. Compare to similar sections on the same page (if one grid works and another doesn't, wpautop is likely the cause)

**Method 2: MCP Browser Inspection (Most Reliable)**

```
1. Use CallMcpTool with browser_navigate to load the page
2. Look at the page snapshot DOM structure
3. Search for empty "paragraph" elements inside "generic" (div) containers
4. Count direct children of grid containers - should match expected items
```

**What to look for in MCP browser snapshot:**

```yaml
# BAD - Empty paragraphs breaking the grid:
- generic [ref=e31]: # Grid container
    - paragraph [ref=e32] # EMPTY <p> - PROBLEM!
    - generic [ref=e33]: # Card 1
    - paragraph [ref=e40] # EMPTY <p> - PROBLEM!
    - generic [ref=e41]: # Card 2

# GOOD - Clean grid with no empty paragraphs:
- generic [ref=e57]: # Grid container
    - generic [ref=e58]: # Card 1
    - generic [ref=e62]: # Card 2
    - generic [ref=e66]: # Card 3
```

**Method 3: Character Count Comparison**

- If remote content is significantly longer than local, WordPress may have added `<p>` tags
- Run `python scripts/wp_pages.py diff --slug [slug]` and note the character difference

#### Problematic HTML Patterns (AVOID THESE)

**Pattern 1: Blank lines between grid items**

```html
<!-- BAD -->
<div style="display: grid;">
  <div>Card 1</div>

  <div>Card 2</div>
</div>
```

**Pattern 2: HTML comments inside grids**

```html
<!-- BAD -->
<div style="display: grid;">
  <!-- First card -->
  <div>Card 1</div>
  <!-- Second card -->
  <div>Card 2</div>
</div>
```

**Pattern 3: Newlines after opening grid tag**

```html
<!-- BAD -->
<div style="display: grid;">
  <div>Card 1</div>
</div>
```

**Pattern 4: Newlines before closing grid tag**

```html
<!-- BAD -->
<div>Card 2</div>
</div>
```

#### Safe HTML Patterns (USE THESE)

**Pattern 1: Inline siblings (safest)**

```html
<div style="display: grid;">
  <div>Card 1</div>
  <div>Card 2</div>
  <div>Card 3</div>
</div>
```

**Pattern 2: Closing-to-opening on same line**

```html
<div style="display: grid;">
  <div>Card 1 content here</div>
  <div>Card 2 content here</div>
  <div>Card 3 content here</div>
</div>
```

**Key rule**: `</div><div>` must have NO characters between them (no newline, no space, no comment)

#### Fixing Existing Content

1. **Identify the broken grid** in local HTML file
2. **Remove all HTML comments** inside the grid container
3. **Remove blank lines** between sibling divs
4. **Ensure pattern**: `</div><div>` with nothing between
5. **Push to WordPress**: `python scripts/wp_pages.py push --file content/tools/[slug].html`
6. **Purge caches**: WordPress cache AND SiteGround cache
7. **Verify with screenshot**: `python scripts/screenshot_pages.py --slug [slug] --format segments --jpeg`
8. **Verify with MCP browser**: Check DOM for empty paragraphs

#### Prevention Checklist (Before Pushing Any Content)

- [ ] No blank lines inside grid containers
- [ ] No HTML comments inside grid containers
- [ ] All `</div><div>` sibling pairs have no whitespace between them
- [ ] Opening grid tag immediately followed by first child: `<div style="display: grid;"><div>`
- [ ] Last child immediately followed by closing grid tag: `</div></div>`
- [ ] Test locally if possible before pushing

#### Why This Happens

WordPress's `wpautop` was designed for blog posts with simple text. It assumes blank lines = new paragraph. Our HTML content with CSS Grid layouts breaks this assumption. Unfortunately, we can't disable wpautop without affecting other content, so we must write wpautop-safe HTML.

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

Review each content file for clarity and value. **Most content is worse than you think.**

### The Developer Test

Read each page and ask: "Would a senior developer at Google find this content useful?"

- If yes → Content passes
- If "maybe" → Content needs work
- If no → Content is failing its purpose

**"Maybe" is failure.** Developers have limited time. They will leave if content doesn't immediately prove its value.

### Quality Checklist (Be Harsh)

For each content file, check:

- [ ] **No redundancy** - Same information not repeated in multiple sections. If FAQ repeats intro, that's a failure.
- [ ] **Clear language** - Would a junior developer understand this in 30 seconds?
- [ ] **Scannable** - Can you get the key points in 10 seconds of skimming?
- [ ] **Value density** - Delete every sentence that doesn't teach something. What's left?
- [ ] **Action-oriented** - Does every section tell users what to DO, not just what exists?

### Red Flags (Fix These)

| Issue               | Example                          | Why It's Bad                           | Fix                           |
| ------------------- | -------------------------------- | -------------------------------------- | ----------------------------- |
| Redundant sections  | FAQ repeats intro content        | Wastes user time, looks unprofessional | Delete the redundant version  |
| Wall of text        | 10+ line paragraphs              | Users won't read it, instant bounce    | Break up with headers/bullets |
| Vague language      | "various issues may occur"       | Sounds like filler, zero value         | Be specific or delete         |
| Missing examples    | "implement retries" with no code | Useless to developers                  | Add working code example      |
| Self-congratulatory | "our amazing tool"               | Cringe, damages trust                  | Delete entirely               |
| Marketing fluff     | "unlock the power of AI"         | Developers hate this                   | Replace with specific benefit |
| Passive voice       | "errors can be decoded"          | Weak, unclear                          | "Decode errors instantly"     |

### Content Length Guidelines

| Page Type                    | Minimum Lines | Maximum Lines |
| ---------------------------- | ------------- | ------------- |
| Tool page (widget-focused)   | 100           | 200           |
| Guide page (content-focused) | 200           | 350           |

**Under minimum = thin content (SEO penalty, low value)**
**Over maximum = bloated (users won't read, trim the fat)**

```bash
# Check line counts
wc -l content/tools/*.html | sort -n
```

### The "Delete Test"

For every paragraph, ask: "If I deleted this, would the page be worse?"

- If yes → Keep it
- If unsure → Probably delete it
- If no → Definitely delete it

**Most pages have 20-30% filler that should be deleted.**

---

## Section 4: User-First Review

Read each page as a **skeptical, busy developer** who will leave in 5 seconds if the page doesn't prove its worth.

### The 5-Second Test

Load each page and look away. Look back for 5 seconds. Can you answer:

1. What does this tool do?
2. Why should I care?
3. How do I use it?

**If any answer is unclear in 5 seconds, the page fails.** Fix the above-fold content.

### Critical Questions

1. **Can users complete their task in under 60 seconds?**
   - Time yourself. Actually use the tool. Is it under 60 seconds?
   - If not, why? What's slowing them down?

2. **Is the most important info above the fold?**
   - Widget MUST be visible without scrolling on desktop
   - Value proposition MUST be clear in first 2 sentences
   - If you have to scroll to understand what the page does, it fails

3. **Would YOU sign up for the email list?**
   - Be honest. Is the value proposition compelling?
   - "Stay updated" is not compelling
   - "Get notified when OpenAI changes pricing" is compelling

4. **Does the FAQ answer questions people ACTUALLY have?**
   - Not "Is this tool free?" (obvious filler)
   - Real questions: "How accurate is the pricing data?" "How often is it updated?"

5. **Are internal links earning their place?**
   - Every link should help the user accomplish something
   - "Related Tools" section: Would a user actually want these tools after using this one?

### User Journey Audit

For each page, map the expected user journey:

1. User lands on page (from Google, link, etc.)
2. User understands value (5 seconds)
3. User uses tool (60 seconds)
4. User optionally signs up for email (10 seconds)
5. User optionally explores related tools

**At each step, ask: "Why would the user NOT continue?"** That's where you have a problem.

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

| Page                  | Status      | Issues Found |
| --------------------- | ----------- | ------------ |
| ai-status             | OK / Issues | [list]       |
| ai-error-decoder      | OK / Issues | [list]       |
| ai-pricing-calculator | OK / Issues | [list]       |
| ai-tools              | OK / Issues | [list]       |

### Local vs Live Sync

| Page      | Local (chars) | Remote (chars) | Status                               |
| --------- | ------------- | -------------- | ------------------------------------ |
| ai-status | X             | X              | In sync / Local newer / Remote newer |
| ...       |               |                |                                      |

### Prose Quality

| Page           | Lines | Issues  | Action   |
| -------------- | ----- | ------- | -------- |
| ai-status.html | X     | [issue] | [action] |
| ...            |       |         |          |

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
- **Weekly** - Yes, weekly. Quality drift happens faster than you think.
- **After complaints** - If users report issues with a page
- **Before major launches** - Ensure all pages are in good shape
- **When traffic is low** - Quality issues might be why

## Accountability

**At the end of every review, answer these questions:**

1. How many issues did I find? (If zero, I wasn't looking hard enough)
2. How many issues did I fix? (Should be 100% of blocking issues)
3. What issues am I leaving unfixed? Why?
4. When will unfixed issues be addressed?

**Do not end the review with "everything looks good" unless you can prove it.**

---

## Updating This Prompt (Continuous Improvement)

**Every time you find a new issue type, update this documentation.**

The goal: Future reviews should automatically catch issues you discovered manually.

### After Finding a New Issue

Ask yourself:

1. Would the existing documentation have caught this?
2. If no → Add it to the Common Issues section
3. If yes but missed → Make the documentation clearer

### What to Document

For each new issue type, add:

- **Visual symptoms** (what it looks like in screenshots)
- **How to detect** (specific inspection methods)
- **Common causes** (root cause analysis)
- **How to fix** (step-by-step)
- **Prevention** (how to avoid in future)

### Where to Update

| Issue Type                 | Update Location                    |
| -------------------------- | ---------------------------------- |
| Visual/layout issues       | Section 0.5 + Common Issues        |
| WordPress/Bricks issues    | Common Issues - wpautop section    |
| Technical rendering issues | Common Issues                      |
| New detection methods      | Section 1 (Live Page Rendering)    |
| Visual quality criteria    | `prompts/VISUAL_QUALITY_REVIEW.md` |

### Template for New Issues

```markdown
### Issue: [Descriptive Name]

**What it looks like:**

- [Visual description a human would notice]

**Visual symptoms in screenshots:**

- [Specific visual indicators]

**How to detect:**

1. [Detection method 1]
2. [Detection method 2]

**Common causes:**

1. [Cause with explanation]
2. [Cause with explanation]

**How to fix:**

1. [Specific fix step]
2. [Verification step]

**Prevention:**

- [How to avoid this in the future]
```

**Remember: Time spent documenting saves 10x time in future reviews.**