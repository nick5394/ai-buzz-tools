# Prompt Template

Use this template when creating new prompts for Cursor.

---

## Structure

```markdown
# [Prompt Title]

[1-2 sentence description of when to use this prompt]

## Context

[What the AI needs to know before starting]
- Key files to reference
- Current state assumptions
- Relevant rules: `@.cursor/rules/[rule].mdc`

---

## [Section 1: First Task]

[Clear instructions for what to do]

**Checklist:**
- [ ] Item 1
- [ ] Item 2

---

## [Section 2: Second Task]

[Continue pattern...]

---

## Output Template

[Define what the output should look like]

```markdown
## [Title] - [DATE]

### Section 1
- Finding 1
- Finding 2

### Recommended Actions
- [ ] Action 1
```

---

## Usage

[How to invoke this prompt]

\`\`\`
@prompts/[this-file].md

[Example invocation]
\`\`\`
```

---

## Best Practices

1. **Be specific** - Vague prompts produce vague results
2. **Reference files** - Use `@path/to/file.ext` to include context
3. **Define output** - Tell the AI exactly what format you want
4. **Include examples** - Show good vs bad outputs
5. **Keep it focused** - One prompt, one purpose
6. **Make it reusable** - Parameterize where possible

---

## Anti-Patterns

**Bad prompt:**
```
Make the code better
```

**Good prompt:**
```
Review api/pricing.py for:
1. Functions over 50 lines (extract helpers)
2. Duplicated error handling (extract to decorator)
3. Magic numbers (extract to constants)

Output: List of findings with line numbers and suggested fixes.
```
