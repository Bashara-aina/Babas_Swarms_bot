# Skill Template

Full template for creating new skills.

## Minimal Skill Structure

```
skill-name/
├── SKILL.md                    # Required
├── .claude-plugin/
│   └── plugin.json            # Required
├── references/                 # Optional
│   ├── CONCEPT.md
│   └── EXAMPLES.md
└── scripts/                    # Optional
    └── helper.sh
```

## SKILL.md Template

```markdown
---
name: skill-name
description: Brief description. Use when [specific triggers].
---

# Skill Title

## Quick Start

[Minimal working example]

## Workflows

[Step-by-step processes]

## Examples

[Concrete usage examples]

## Advanced

[Link to: references/ADVANCED.md]
```

## plugin.json Template

```json
{
  "name": "skill-name",
  "description": "Skill description",
  "version": "1.0.0",
  "skills": ["./"]
}
```

## Reference File Template

```markdown
# Reference Title

## Section 1

Content...

## Section 2

Content...
```

## Script Template

```bash
#!/bin/bash
# Script description

set -euo pipefail

# Main logic here
```

## Description Best Practices

### Good Descriptions
```
"Extract text from PDFs, fill forms, merge documents. Use when working with PDF files."
"Set up CI/CD pipeline with GitHub Actions. Use when user mentions 'CI', 'CD', 'pipeline'."
```

### Bad Descriptions
```
"Helps with documents."           # Too vague
"Process files."                # What files? How?
```

## When to Split into References

| Condition | Action |
|----------|--------|
| SKILL.md > 100 lines | Split |
| Multiple distinct domains | Split |
| Advanced content rarely needed | Split |
| Detailed examples needed | Split |

## Skill Checklist

- [ ] Name is kebab-case (`my-skill`)
- [ ] Description has triggers ("Use when...")
- [ ] SKILL.md has Quick Start section
- [ ] plugin.json has correct name
- [ ] References linked correctly from SKILL.md
- [ ] Scripts are executable (`chmod +x`)