---
name: components
description: "Skill for the Components area of swarm-bot."
---

# Components

"components area"

## When to Use

- Working with code in `ext/`
- Understanding how lineNav, TextInput, flushParentChange work
- Modifying components-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | invert, seg, graphemeStops, snapPos, prevPos (+22) |
| `ext/hermes-agent/ui-tui/src/components/agentsOverlay.tsx` | formatRowId, statusGlyph, GanttStrip, ListRow, DiffPane (+9) |
| `ext/hermes-agent/ui-tui/src/lib/subagentTree.ts` | topLevelSubagents, hotnessBucket, formatSummary, fmtCost, fmtTokens (+6) |
| `ext/hermes-agent/ui-tui/src/components/markdown.tsx` | splitRow, isTableDivider, MdImpl, gap, start (+3) |
| `ext/hermes-agent/ui-tui/src/lib/inputMetrics.ts` | graphemes, visualLines, widthBetween, cursorLayout, offsetFromPosition (+1) |
| `ext/hermes-agent/ui-tui/src/components/appChrome.tsx` | SpawnHud, TranscriptScrollbar, jump, modelLabel, StatusRule |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/providers.tsx` | getResolvedTheme, applyTheme, ThemeProvider, handler |
| `ARCHIVE_cekwajar-src-version/cekwajar.id/src/components/providers.tsx` | getResolvedTheme, applyTheme, ThemeProvider, handler |
| `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/components/ClockContext.tsx` | updateInterval, now, setTickInterval, ClockProvider |
| `cekwajar.id-20260415T173403Z-3-001/cekwajar (1).id/components/combined.js` | fmtIDR, fmtIDRShort, parseIDR, WajarSlipPage |

## Entry Points

Start here when exploring this area:

- **`lineNav`** (Function) — `ext/hermes-agent/ui-tui/src/components/textInput.tsx:145`
- **`TextInput`** (Function) — `ext/hermes-agent/ui-tui/src/components/textInput.tsx:233`
- **`flushParentChange`** (Function) — `ext/hermes-agent/ui-tui/src/components/textInput.tsx:393`
- **`canFastEchoBase`** (Function) — `ext/hermes-agent/ui-tui/src/components/textInput.tsx:436`
- **`canFastAppend`** (Function) — `ext/hermes-agent/ui-tui/src/components/textInput.tsx:438`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `lineNav` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 145 |
| `TextInput` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 233 |
| `flushParentChange` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 393 |
| `canFastEchoBase` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 436 |
| `canFastAppend` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 438 |
| `canFastBackspace` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 451 |
| `commit` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 459 |
| `emitPaste` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 521 |
| `clearSel` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 569 |
| `moveCursor` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 592 |
| `startMouseSelection` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 636 |
| `dragMouseSelection` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 646 |
| `isMultiClickAt` | Function | `ext/hermes-agent/ui-tui/src/components/textInput.tsx` | 681 |
| `topLevelSubagents` | Function | `ext/hermes-agent/ui-tui/src/lib/subagentTree.ts` | 320 |
| `hotnessBucket` | Function | `ext/hermes-agent/ui-tui/src/lib/subagentTree.ts` | 331 |
| `formatSummary` | Function | `ext/hermes-agent/ui-tui/src/lib/subagentTree.ts` | 236 |
| `fmtCost` | Function | `ext/hermes-agent/ui-tui/src/lib/subagentTree.ts` | 266 |
| `fmtTokens` | Function | `ext/hermes-agent/ui-tui/src/lib/subagentTree.ts` | 283 |
| `fmtDuration` | Function | `ext/hermes-agent/ui-tui/src/lib/subagentTree.ts` | 303 |
| `cursorLayout` | Function | `ext/hermes-agent/ui-tui/src/lib/inputMetrics.ts` | 109 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `AgentsOverlay → _patch_litellm_for_minimax` | cross_community | 8 |
| `AgentsOverlay → Items` | cross_community | 7 |
| `AgentsOverlay → Get_hermes_home` | cross_community | 6 |
| `TextInput → Seg` | cross_community | 5 |
| `TextInput → IsWhitespace` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Hermes_cli | 8 calls |
| Test | 8 calls |
| Layout | 5 calls |
| Tools | 3 calls |
| Pages | 3 calls |
| Cluster_2648 | 2 calls |
| Ink | 1 calls |
| Scripts | 1 calls |

## How to Explore

1. `gitnexus_context({name: "lineNav"})` — see callers and callees
2. `gitnexus_query({query: "components"})` — find related execution flows
3. Read key files listed above for implementation details
