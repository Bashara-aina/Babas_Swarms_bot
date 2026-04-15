---
description: >-
  Create and manage skills. Skills are reusable prompt templates that encode
  best practices for specific tasks. Use to create new skills, review existing
  ones, or manage skill collections.
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---
# /skill — Create and Manage Skills

## WHEN TO USE

Use `/skill` when:
- You find yourself repeating the same guidance patterns
- You want to encode best practices for reuse
- You need to create a skill for a new domain
- You want to review/analyze existing skills
- You want to improve skill quality

## SKILL TYPES

### Rigid Skills
Must follow exactly. Examples:
- TDD (test-driven development)
- Debugging protocol
- Security audit

### Flexible Skills
Adapt principles to context. Examples:
- Code review patterns
- Documentation style
- Architecture patterns

## USAGE

```
/skill create [name] [description]
/skill review [name]
/skill list
/skill delete [name]
/skill improve [name]
```

## EXAMPLES

### Create a skill
```
/skill create tdd "Test-driven development workflow"

Creates: .opencode/skills/tdd.md
```

### Review existing skill
```
/skill review code-review-patterns
```
Output: Quality rating, issues, recommendations.

### List all skills
```
/skill list
```
Output:
```
AVAILABLE SKILLS:
- tdd (rigid) — Test-driven development workflow
- debugging (rigid) — Systematic debugging protocol
- code-review (flexible) — Code review best practices
- architecture (flexible) — System architecture patterns
- ... (N total)
```

## SKILL ANATOMY

```markdown
---
name: skill-name
description: >-
  One-line description of what this skill does
type: rigid | flexible
---

# Skill Title

## When to Use
[When to invoke this skill]

## Instructions
[Step-by-step instructions]

## Anti-Hallucination Rules
[Rules specific to this skill]

## Output Format
[How to format output]

## Examples
[At least 2 examples with input → output]
```

## CREATION WORKFLOW

```
1. /skill create [name] [description]
2. Writer creates skill file following template
3. /skill review [name] evaluates quality
4. If issues found: improve and re-review
5. If approved: skill is ready to use
```

## WHAT MAKES A GOOD SKILL

### Good trigger conditions
Specific situations, not vague "when relevant":
- "User says 'write a test' or 'add tests for X'"
- "Bug report with stack trace received"

### Good instructions
Step-by-step, not abstract:
- "1. Run failing test 2. Write minimal code 3. Run test again"

### Bad instructions
Vague guidance:
- "1. Follow TDD principles 2. Be thorough"

## ANTI-HALLUCINATION RULES

1. **Follow template** — use exact structure shown
2. **Verify file write** — cat file after creating
3. **Review before claiming done** — run skill-reviewer
4. **Check for duplicates** — /skill list before creating
5. **Validate examples** — examples must be realistic

## STATUS
```
SKILL STATUS: ✅ [operation] | ❌ FAILED
Skill: [name]
Rating: [X.X/5.0 if reviewed]
Recommendation: [RECOMMENDED/NEEDS IMPROVEMENT]
```
