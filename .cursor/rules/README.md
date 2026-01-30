# Cursor Rules Index

This directory contains rules that guide AI interactions with this codebase.

## How Rules Work

- **Always Applied:** Rules with `alwaysApply: true` are active in every conversation
- **Glob-based:** Rules with `globs` patterns only activate when editing matching files
- **On-demand:** Rules with `alwaysApply: false` can be referenced with `@.cursor/rules/[name].mdc`

## Rule Files

### Always Applied (Core Rules)

| File | Purpose |
|------|---------|
| `ai-buzz-tools.mdc` | Core principles, architecture patterns, decision framework |
| `project-context.mdc` | Project mission, status, WordPress integration |
| `composer-discipline.mdc` | Completion requirements, testing rules, scope discipline |
| `file-protection.mdc` | File modification tiers, creation boundaries |

### Conditionally Applied

| File | Trigger | Purpose |
|------|---------|---------|
| `testing-checklist.mdc` | `tests/**` | Testing requirements and patterns |
| `seo-content-strategy.mdc` | `content/tools/**` | SEO and content quality standards |
| `wordpress-workflow.mdc` | Manual | WordPress push/verify workflow |

### Reference Only

| File | Purpose |
|------|---------|
| `documentation-index.mdc` | Points to relevant docs for different areas |
| `workflow-guide.mdc` | Human reference for prompt templates |

## Quick Reference

### Adding a New Tool
1. Follow patterns in `api/error_decoder.py`
2. Check `testing-checklist.mdc` for test requirements
3. Check `project-context.mdc` for WordPress setup

### Before Modifying Critical Files
Check `file-protection.mdc` - some files require explicit approval:
- `main.py`, `api/shared.py`, `requirements.txt`
- `.cursor/rules/*.mdc`

### When Stuck
Reference `ai-buzz-tools.mdc` for:
- Decision priority order
- Thinking lenses (product, SEO, developer, skeptic)
- Reference implementation patterns

## Rule Maintenance

When updating rules:
1. Keep them focused (one concern per rule)
2. Include examples (good and bad)
3. Update this README if adding new rules
4. Test that `alwaysApply` and `globs` work as expected
