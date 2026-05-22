---
name: ink
description: "Skill for the Ink area of swarm-bot. 221 symbols across 57 files."
---

# Ink

"221 symbols | 57 files | Cohesion: 69%"

## When to Use

- Working with code in `ext/`
- Understanding how resetLayoutShifted, createRenderer, createScreen work
- Modifying ink-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/ink.tsx` | constructor, scanElementSubtree, resetPools, onRender, clearTextSelection (+36) |
| `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/screen.ts` | CharPool, HyperlinkPool, StylePool, createScreen, withInverse (+21) |
| `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/selection.ts` | applySelectionOverlay, clearSelection, shiftSelection, shiftSelectionForFollow, finishSelection (+15) |
| `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/log-update.ts` | LogUpdate, render, transitionHyperlink, transitionStyle, renderFrameSlice (+8) |
| `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/focus.ts` | FocusManager, blur, handleNodeRemoved, getRootNode, getFocusManager (+7) |
| `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/render-node-to-output.ts` | resetLayoutShifted, wrapWithOsc8Link, applyStylesToWrappedText, renderNodeToOutput, renderChildren (+5) |
| `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/output.ts` | Output, reset, blit, flushBuffer, styledCharsWithGraphemeClustering (+3) |
| `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/reconciler.ts` | cleanupYogaNode, removeChildFromContainer, removeChild, diff, setEventHandler (+3) |
| `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/wrap-text.ts` | evictWrapCache, sliceFit, truncate, memoizedWrap, computeWrap (+1) |
| `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/parse-keypress.ts` | parseTerminalResponse, parseMultipleKeypresses, parseMouseEvent, parseSgrMouseFragment, parseTextWithSgrMouseFragments (+1) |

## Entry Points

Start here when exploring this area:

- **`resetLayoutShifted`** (Function) — `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/render-node-to-output.ts:34`
- **`createRenderer`** (Function) — `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/renderer.ts:32`
- **`createScreen`** (Function) — `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/screen.ts:510`
- **`renderToScreen`** (Function) — `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/render-to-screen.ts:58`
- **`emptyFrame`** (Function) — `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/frame.ts:17`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `CharPool` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/screen.ts` | 12 |
| `HyperlinkPool` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/screen.ts` | 60 |
| `StylePool` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/screen.ts` | 125 |
| `LogUpdate` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/log-update.ts` | 40 |
| `FocusManager` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/focus.ts` | 14 |
| `Output` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/output.ts` | 175 |
| `FocusEvent` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/events/focus-event.ts` | 10 |
| `TerminalFocusEvent` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/events/terminal-focus-event.ts` | 11 |
| `TerminalEvent` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/events/terminal-event.ts` | 18 |
| `KeyboardEvent` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/events/keyboard-event.ts` | 12 |
| `MouseEvent` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/events/mouse-event.ts` | 2 |
| `Ink` | Class | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/ink.tsx` | 141 |
| `resetLayoutShifted` | Function | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/render-node-to-output.ts` | 34 |
| `createRenderer` | Function | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/renderer.ts` | 32 |
| `createScreen` | Function | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/screen.ts` | 510 |
| `renderToScreen` | Function | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/render-to-screen.ts` | 58 |
| `emptyFrame` | Function | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/frame.ts` | 17 |
| `useSearchHighlight` | Function | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/hooks/use-search-highlight.ts` | 18 |
| `cellAtIndex` | Function | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/screen.ts` | 666 |
| `setCellStyleId` | Function | `ext/hermes-agent/ui-tui/packages/hermes-ink/src/ink/screen.ts` | 887 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `UseSelection → ComparePoints` | cross_community | 5 |
| `UseSelection → ExecFileNoThrow` | cross_community | 5 |
| `UseSelection → JoinRows` | cross_community | 4 |
| `UseSelection → Osc` | cross_community | 4 |
| `UseSelection → ShouldEmitClipboardSequence` | cross_community | 4 |
| `UseSelection → SelectionSignature` | intra_community | 4 |
| `UseSelection → Cb` | cross_community | 4 |
| `Constructor → LogError` | cross_community | 4 |
| `Constructor → Csi` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Termio | 10 calls |
| Events | 3 calls |
| Acp | 3 calls |
| Test | 2 calls |
| Ui | 1 calls |
| Handlers | 1 calls |
| Health | 1 calls |

## How to Explore

1. `gitnexus_context({name: "resetLayoutShifted"})` — see callers and callees
2. `gitnexus_query({query: "ink"})` — find related execution flows
3. Read key files listed above for implementation details
