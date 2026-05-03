---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [module-or-path]
description: "Generate or update documentation. Without args: update all docs. With path: docs for specific module."
---

# /docs — Documentation generator

Generate or update documentation for code, modules, or architecture.

## Usage
```
/docs
/docs handlers/ai.py
/docs core/intent_router.py
```

## What it generates
- Module docstrings
- README files
- Architecture diagrams (ASCII)
- API documentation
- Decision records (ADR)

## Steps

1. Identify the module or path to document (or all of `core/` if no args)
2. Read the relevant source files to understand the API
3. Run `grep -n "def \|class " <path>` to find all public symbols
4. Generate module docstring from symbol signatures + actual implementation
5. For architecture docs: write to `.wiki/architecture/`
6. For ADRs: write to `.wiki/decisions/ADR-NNN.md`
7. Verify the doc file was created and is non-empty

## Swarm-Bot Documentation Locations
| Type | Location |
|------|----------|
| Module docs | docstrings in .py files |
| Architecture | .wiki/architecture/ |
| Decisions | .wiki/decisions/ADR-*.md |
| Research | .wiki/research/ |
| Logs | .wiki/logs/ |

## Docstring Convention
```python
def function(param: type) -> return_type:
    """Short description.

    Args:
        param: description

    Returns:
        description

    Raises:
        ExceptionType: when this happens
    """
```

## Output
Saves documentation to the appropriate location and reports where.
