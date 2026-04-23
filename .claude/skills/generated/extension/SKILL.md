---
name: extension
description: "Skill for the Extension area of swarm-bot. 76 symbols across 6 files."
---

# Extension

76 symbols | 6 files | Cohesion: 81%

## When to Use

- Working with code in `ext/`
- Understanding how sendMessage work
- Modifying extension-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/skills/gstack/extension/sidepanel.js` | authHeaders, formatChatTime, addChatEntry, handleAgentEvent, sendMessage (+34) |
| `ext/skills/gstack/extension/inspector.js` | removeHighlight, onKeyDown, stopPicker, buildSelector, isUnique (+9) |
| `ext/skills/gstack/extension/content.js` | showStatusPill, captureBasicData, basicBuildSelector, basicPickerCleanup, onBasicClick (+7) |
| `ext/skills/gstack/extension/background.js` | setConnected, setDisconnected, notifyContentScripts, getBaseUrl, loadAuthToken (+4) |
| `halolight-ref/src/lib/api/mock-api.ts` | sendMessage |
| `project/rumahlabuh/components/ui/sidebar.tsx` | SidebarTrigger |

## Entry Points

Start here when exploring this area:

- **`sendMessage`** (Method) — `halolight-ref/src/lib/api/mock-api.ts:307`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `sendMessage` | Method | `halolight-ref/src/lib/api/mock-api.ts` | 307 |
| `authHeaders` | Function | `ext/skills/gstack/extension/sidepanel.js` | 29 |
| `formatChatTime` | Function | `ext/skills/gstack/extension/sidepanel.js` | 95 |
| `addChatEntry` | Function | `ext/skills/gstack/extension/sidepanel.js` | 109 |
| `handleAgentEvent` | Function | `ext/skills/gstack/extension/sidepanel.js` | 165 |
| `sendMessage` | Function | `ext/skills/gstack/extension/sidepanel.js` | 316 |
| `pollChat` | Function | `ext/skills/gstack/extension/sidepanel.js` | 392 |
| `updateStopButton` | Function | `ext/skills/gstack/extension/sidepanel.js` | 519 |
| `stopAgent` | Function | `ext/skills/gstack/extension/sidepanel.js` | 525 |
| `startFastPoll` | Function | `ext/skills/gstack/extension/sidepanel.js` | 555 |
| `stopFastPoll` | Function | `ext/skills/gstack/extension/sidepanel.js` | 560 |
| `escapeHtml` | Function | `ext/skills/gstack/extension/sidepanel.js` | 811 |
| `fetchRefs` | Function | `ext/skills/gstack/extension/sidepanel.js` | 849 |
| `runCleanup` | Function | `ext/skills/gstack/extension/sidepanel.js` | 1265 |
| `runScreenshot` | Function | `ext/skills/gstack/extension/sidepanel.js` | 1323 |
| `inspectorShowData` | Function | `ext/skills/gstack/extension/sidepanel.js` | 953 |
| `renderBoxModel` | Function | `ext/skills/gstack/extension/sidepanel.js` | 992 |
| `fmtBoxVal` | Function | `ext/skills/gstack/extension/sidepanel.js` | 1029 |
| `renderMatchedRules` | Function | `ext/skills/gstack/extension/sidepanel.js` | 1038 |
| `renderRule` | Function | `ext/skills/gstack/extension/sidepanel.js` | 1097 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → UpdateSendButton` | cross_community | 8 |
| `Generate_report → UpdateSendButton` | cross_community | 7 |
| `Chat_with_report_agent → UpdateSendButton` | cross_community | 7 |
| `Prepare_simulation → UpdateSendButton` | cross_community | 6 |
| `Start_simulation → UpdateSendButton` | cross_community | 6 |
| `Get_prepare_status → UpdateSendButton` | cross_community | 6 |
| `Get_simulation_history → UpdateSendButton` | cross_community | 6 |
| `Prepare_simulation → UpdateSendButton` | cross_community | 6 |
| `Synthesize_session → UpdateSendButton` | cross_community | 6 |
| `Interview_agents → UpdateSendButton` | cross_community | 6 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Handlers | 3 calls |
| Layout | 1 calls |
| Ui | 1 calls |

## How to Explore

1. `gitnexus_context({name: "sendMessage"})` — see callers and callees
2. `gitnexus_query({query: "extension"})` — find related execution flows
3. Read key files listed above for implementation details
