# Exercise Naming Conventions

Reference for naming exercises and sections.

## Directory Naming

### Sections
- Format: `XX-section-name`
- XX = zero-padded number (01, 02, 03...)
- Name = dash-case (lowercase with hyphens)
- Examples:
  - `01-introduction`
  - `02-user-authentication`
  - `03-database-basics`

### Exercises
- Format: `XX.YY-exercise-name`
- XX.YY = section number + exercise number
- Examples:
  - `01.01-hello-world`
  - `01.02-variables`
  - `02.01-login-flow`

## File Structure

```
exercises/
├── 01-introduction/
│   ├── 01.01-hello-world/
│   │   ├── explainer/
│   │   │   └── readme.md
│   │   ├── problem/
│   │   │   └── readme.md
│   │   └── solution/
│   │       └── readme.md
│   └── 01.02-variables/
│       ├── explainer/
│       │   └── readme.md
│       └── problem/
│           └── readme.md
└── 02-user-authentication/
    └── 02.01-login-flow/
        └── problem/
            └── readme.md
```

## Required Readme Format

Every `readme.md` must have:
1. A title (line starting with `#`)
2. Non-empty content

```markdown
# Hello World

Your first exercise.
```

## Common Patterns

### Explainer Only (No Problem/Solution)
```
exercises/
└── 01-intro/
    └── 01.01-hello/
        └── explainer/
            └── readme.md
```

### Full Variant Set
```
exercises/
└── 02-api/
    └── 02.01-fetch/
        ├── explainer/
        │   └── readme.md
        ├── problem/
        │   ├── readme.md
        │   └── main.ts
        └── solution/
            ├── readme.md
            └── main.ts
```

## Lint Rules

The linter (`pnpm ai-hero-cli internal lint`) checks:
- Each exercise has at least one of: `explainer/`, `problem/`, `solution/`
- `readme.md` exists and non-empty in primary subfolder
- No `.gitkeep` files
- No `speaker-notes.md` files
- No broken links
- `main.ts` required per subfolder unless readme-only