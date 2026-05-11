# Project Archive — obsidian-mind /om-project-archive

## What It Does

Moves a completed project from work/active/ to work/archive/YYYY/ and updates indexes.

## When to Use

When a project is completed or archived.

## Usage

```
/om-project-archive
Project: Auth Refactor
Archive Date: 2026-05-08
Summary: Designed and implemented new auth system with error monitoring.
```

## Expected Actions

1. Move `work/active/Auth Refactor.md` to `work/archive/2026/Auth Refactor.md`
2. Update `work/active/` index if one exists
3. Update `brain/North Star.md` if project was listed
4. Create a final status note linking to archived work
5. Update any competency evidence links

## Expected Output

```
Project Archived: Auth Refactor
=============================
Location: work/archive/2026/Auth Refactor.md
Archive Date: 2026-05-08
Final Summary: Designed and implemented new auth system with error monitoring.

Linked Competencies:
- System Design → evidence preserved
- Communication → evidence preserved

Indexes Updated:
- brain/North Star.md — project removed from active
- work/active/ — note moved to archive
```

## Notes for Claude

- Always create an archive summary with key achievements
- Preserve all wikilinks when moving
- Update any parent indexes (work/active/Index.md)
- Maintain evidence links for performance reviews
- Tag with quarter for easy retrieval: #archive-2026-q2
