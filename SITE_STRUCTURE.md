# AI-Buzz Site Structure

This document describes the content architecture of ai-buzz.com, including categories, pages, and posts.

## Overview

AI-Buzz has three main content pillars:

```
ai-buzz.com
├── AI News                    # Timely news and analysis (~350 posts)
├── AI Tutorials & Guides      # Educational content for learners
└── AI Developer Tools         # Interactive tools + troubleshooting guides
```

The **AI Developer Tools** section is distinct from the other two because:
- It serves working developers (not learners or news readers)
- It includes both interactive tools (Pages) and reference guides (Posts)
- Content targets problem-solving queries ("fix 429 error", "compare pricing")

---

## Category Hierarchy

### Top-Level Categories

| Category | Slug | Purpose | Post Count |
|----------|------|---------|------------|
| AI News and Industry Impact | `ai-news` | News, analysis, industry trends | ~350 |
| AI Tutorials & Guides | `ai-tutorials` | Educational content | ~6 |
| AI Developer Tools | `ai-developer-tools` | Developer reference/tools | 3+ |

### AI News Subcategories

Under "AI News and Industry Impact":

- AI Business & Enterprise (`business`)
- AI Legal & Policy (`policy`)
- AI Research & Innovation (`research`)
- AI in Software & Tech (`tech`)

### AI Tutorials Subcategories

Under "AI Tutorials & Guides":

- AI Development (`development`)
- AI Fundamentals (`fundamentals`)

### AI Developer Tools

This is a **top-level category** (not under AI Tutorials) because:
1. Different search intent (problem-solving vs learning)
2. Different audience (working developers vs learners)
3. Better SEO for "AI developer tools" keyword

---

## Content Types

### WordPress Pages (Tools)

Interactive tool pages with embedded widgets. These are WordPress **Pages** (not Posts) because they're utilities, not articles.

| Page | URL | Widget |
|------|-----|--------|
| AI Tools Hub | `/ai-tools` | `tools-landing` |
| AI Pricing Calculator | `/ai-pricing-calculator` | `pricing` |
| AI Status Page | `/ai-status` | `status` |
| AI Error Decoder | `/ai-error-decoder` | `error-decoder` |

**Content files:** `content/tools/ai-*.html`

### WordPress Posts (Guides)

Reference and troubleshooting guides. These are WordPress **Posts** with category "AI Developer Tools".

| Post | URL | Category |
|------|-----|----------|
| OpenAI 429 Errors Guide | `/ai-openai-429-errors` | AI Developer Tools |
| OpenAI Rate Limits | `/ai-openai-rate-limits` | AI Developer Tools |
| OpenAI vs Anthropic Pricing | `/ai-openai-vs-anthropic-pricing` | AI Developer Tools |

**Content files:** `content/tools/ai-*.html` (pushed as posts via `wp_pages.py push-post`)

---

## URL Structure

All tool/guide content uses flat URLs (no category prefix):

```
https://www.ai-buzz.com/ai-pricing-calculator     # Tool page
https://www.ai-buzz.com/ai-openai-429-errors      # Guide post
https://www.ai-buzz.com/ai-developer-tools/        # Category archive
```

The category archive at `/ai-developer-tools/` lists all guide posts in the "AI Developer Tools" category.

---

## Navigation Menu

```
AI News  |  AI Tutorials & Guides  |  AI Developer Tools
                                          │
                                          ├── AI Pricing Calculator
                                          ├── AI Status Page
                                          ├── AI Error Decoder
                                          ├── ────────────────
                                          ├── OpenAI Rate Limits
                                          └── OpenAI 429 Errors
```

**Menu configuration:**
- "AI Developer Tools" links to `/ai-tools` (hub page) - recommended for UX
- Alternative: Link to `/ai-developer-tools/` (category archive) - pure SEO play
- Dropdown shows both tool pages and guide posts

---

## Internal Linking Structure

```
                    ┌─────────────────────┐
                    │   /ai-tools (hub)   │
                    │  (WordPress Page)   │
                    └─────────┬───────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │   Pricing   │    │   Status    │    │   Error     │
    │ Calculator  │    │   Page      │    │  Decoder    │
    │   (Page)    │    │   (Page)    │    │   (Page)    │
    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
           │                  │                  │
           └──────────────────┼──────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ /ai-developer-tools │
                    │  (Category Archive) │
                    └─────────┬───────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │ 429 Errors  │    │ Rate Limits │    │  Pricing    │
    │   Guide     │    │   Guide     │    │ Comparison  │
    │   (Post)    │    │   (Post)    │    │   (Post)    │
    └─────────────┘    └─────────────┘    └─────────────┘
```

**Every page/post links to:**
1. Related tools/guides (in "Related Tools" section)
2. Category archive (`/ai-developer-tools/`)

**Category archive links to:**
- All guide posts (automatic via WordPress)

**Hub page links to:**
- All tool pages (manual, in page content)
- All guide posts (manual, in "Helpful Guides" section)

---

## SEO Configuration

### Category Archive SEO

**URL:** `https://www.ai-buzz.com/ai-developer-tools/`

| Field | Value |
|-------|-------|
| SEO Title | AI Developer Tools - Free Pricing Calculator, Status & Error Decoder |
| Meta Description | Free tools for AI developers. Compare API costs, check if OpenAI is down, decode error messages. No signup required. |
| Focus Keyphrase | AI developer tools |

Configure in: WordPress Admin > Posts > Categories > Edit "AI Developer Tools" > AIOSEO panel

### Breadcrumbs

**For guide Posts:**
```
Home > AI Developer Tools > OpenAI 429 Errors Guide
```
(Automatic via WordPress category)

**For tool Pages:**
```
Home > AI Developer Tools > AI Pricing Calculator
```
(Requires manual configuration in Bricks or AIOSEO)

---

## Managing the Structure

### Adding a New Guide Post

1. Create content file: `content/tools/ai-new-guide.html`
2. Push to WordPress: `python scripts/wp_pages.py push-post --file content/tools/ai-new-guide.html`
3. Assign to category: In WordPress Admin, edit post > Categories > check "AI Developer Tools"

Or use the setup script:
```bash
python scripts/setup_developer_tools_category.py
```

### Adding a New Tool Page

1. Create widget: `widgets/new_tool_widget.html`
2. Create API: `api/new_tool.py`
3. Create content: `content/tools/ai-new-tool.html`
4. Push to WordPress: `python scripts/wp_pages.py push --file content/tools/ai-new-tool.html`
5. Update hub page: Add card to `/ai-tools`
6. Update menu: Add dropdown item

### Verifying Structure

```bash
# List all categories
python scripts/setup_developer_tools_category.py --list-categories

# Check category archive is accessible
curl -L https://www.ai-buzz.com/ai-developer-tools/
```

---

## Quick Reference

| Item | URL | Type |
|------|-----|------|
| Hub page | `/ai-tools` | Page |
| Category archive | `/ai-developer-tools/` | Category |
| Pricing Calculator | `/ai-pricing-calculator` | Page |
| Status Page | `/ai-status` | Page |
| Error Decoder | `/ai-error-decoder` | Page |
| 429 Errors Guide | `/ai-openai-429-errors` | Post |
| Rate Limits Guide | `/ai-openai-rate-limits` | Post |
| Pricing Comparison | `/ai-openai-vs-anthropic-pricing` | Post |

---

## Related Documentation

- [WORDPRESS_SETUP.md](./WORDPRESS_SETUP.md) - WordPress integration and widget embedding
- [.cursor/rules/seo-content-strategy.mdc](./.cursor/rules/seo-content-strategy.mdc) - SEO guidelines
- [.cursor/rules/project-context.mdc](./.cursor/rules/project-context.mdc) - Project overview
