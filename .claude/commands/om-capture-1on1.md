# 1:1 Capture — obsidian-mind /om-capture-1on1

## What It Does

Creates a structured 1:1 meeting note from a transcript or summary.

## When to Use

After any 1:1 meeting, or when you have meeting notes to file.

## Usage

```
/om-capture-1on1
Person: Sarah Chen
Date: 2026-05-08
Key Takeaways:
- Happy with auth progress
- Wants error monitoring before release
- 1:1 rescheduled to next Thursday

Action Items:
- [ ] Add error monitoring to auth refactor
- [ ] Send revised timeline to Sarah
```

## Template

The note is created at `work/1-1/{Person} YYYY-MM-DD.md` using the 1-1 template.

## Expected Actions

1. Create note using work/1-1 template
2. Update org/people/{Person}.md with meeting context
3. Add action items to relevant work notes
4. If praise/win mentioned → add to perf/Brag Doc.md
5. Link to {Person} in org/people/

## Notes for Claude

- Include direct quotes when provided
- Parse action items and link to project notes
- Update person's note with key context from the 1:1
