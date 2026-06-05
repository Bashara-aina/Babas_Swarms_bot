# Copilot Instructions: Taste Standard

> **Note:** GitHub Copilot automatically reads this file to set its global behavior. By including this in the `.github` folder, Copilot stops writing generic "slop" code and adheres to the premium Taste Skill standards.

## The "Anti-Slop" Manifesto for Copilot

1. **No Generic UI:** Stop generating default SaaS templates. Use high contrast, strong typographic hierarchy, and extreme care for alignment.
2. **Premium Whitespace:** Elements need room to breathe. Use proportional `clamp()` spacing over rigid padding.
3. **Cinematic Motion:** Never use linear easing. All animations must use spring physics (`stiffness: 100, damping: 20` or similar).
4. **Complete Implementation:** No placeholders. No `// TODO: add actual code here`. Write the full, working implementation every single time.
5. **Contextual Awareness:** For deep style configurations, read the localized `SKILL.md` files in the `skills/` directory.

## Companion: Impeccable Skill

The repo also ships [impeccable](https://github.com/pbakaus/impeccable) at `.github/skills/impeccable/` (auto-discovered by GitHub Copilot). It is a vocabulary-first design skill with **23 commands** and **27 anti-pattern rules**.

### When to use impeccable

- The user mentions a specific impeccable command: `audit`, `polish`, `critique`, `distill`, `harden`, `animate`, `bolder`, `quieter`, `typeset`, `layout`, `colorize`, `adapt`, `onboard`, `overdrive`, `delight`, `optimize`, `clarify`, `extract`, `document`, `init`, `shape`, `craft`, `live`
- The user wants the **brand-vs-product register** (design defaults adjust by project type)
- The user wants the **27 anti-pattern rules** explicitly enumerated

Read the canonical install at `.github/skills/impeccable/SKILL.md` and follow its router table.

### Pairing with taste-skill

Both skills ban the same LLM tells (Inter, purple gradients, 3-equal-icon-cards, emoji as icons, "Welcome to..." headings). For frontend work, prefer running them in this order:

1. **Impeccable** sets vocabulary + brand-vs-product register + anti-pattern guard.
2. **Taste-skill** sets dials (VARIANCE / MOTION / DENSITY) + shape variant for the build.
3. Run the **impeccable CLI** for a final deterministic check: `npx impeccable detect src/`.

The 18-item pre-flight above is the taste-skill checklist. Impeccable has its own 27-rule anti-pattern detector built in.
