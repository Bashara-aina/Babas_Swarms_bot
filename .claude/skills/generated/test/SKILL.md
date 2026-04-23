---
name: test
description: "Skill for the Test area of swarm-bot. 99 symbols across 38 files."
---

# Test

99 symbols | 38 files | Cohesion: 77%

## When to Use

- Working with code in `ext/`
- Understanding how handleWriteCommand, modifyStyle, undoModification work
- Modifying test-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/skills/gstack/browse/src/browser-manager.ts` | getActiveSession, getPage, setRefMap, resolveRef, getRefRole (+11) |
| `ext/skills/gstack/browse/src/cookie-picker-routes.ts` | generatePickerCode, getSessionFromCookie, isValidSession, corsOrigin, jsonResponse (+2) |
| `ext/skills/gstack/test/skill-e2e.test.ts` | designQualityJudge, recordE2E, setupBrowseShims, logCost, dumpOutcomeDiagnostic (+1) |
| `ext/skills/gstack/browse/test/cookie-import-browser.test.ts` | encryptCookieValue, chromiumEpoch, createFixtureDb, createMacFixtureDb, createLinuxFixtureDb |
| `ext/skills/gstack/test/helpers/llm-judge.ts` | callJudge, makeRequest, judge, outcomeJudge |
| `ext/skills/gstack/test/skill-routing-e2e.test.ts` | recordRouting, installSkills, initGitRepo, createRoutingWorkDir |
| `ext/skills/gstack/test/helpers/e2e-helpers.ts` | recordE2E, setupBrowseShims, logCost, dumpOutcomeDiagnostic |
| `ext/skills/gstack/browse/test/sidebar-agent.test.ts` | parseQueueLine, parseQueueFile, shorten, describeToolCall |
| `ext/skills/gstack/design/src/cli.ts` | parseArgs, printUsage, main |
| `ext/skills/gstack/browse/test/snapshot.test.ts` | handleReadCommand, handleWriteCommand |

## Entry Points

Start here when exploring this area:

- **`handleWriteCommand`** (Function) — `ext/skills/gstack/browse/src/write-commands.ts:128`
- **`modifyStyle`** (Function) — `ext/skills/gstack/browse/src/cdp-inspector.ts:451`
- **`undoModification`** (Function) — `ext/skills/gstack/browse/src/cdp-inspector.ts:568`
- **`serve`** (Function) — `ext/skills/gstack/design/src/serve.ts:48`
- **`updateDesignMd`** (Function) — `ext/skills/gstack/design/src/memory.ts:104`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `handleWriteCommand` | Function | `ext/skills/gstack/browse/src/write-commands.ts` | 128 |
| `modifyStyle` | Function | `ext/skills/gstack/browse/src/cdp-inspector.ts` | 451 |
| `undoModification` | Function | `ext/skills/gstack/browse/src/cdp-inspector.ts` | 568 |
| `serve` | Function | `ext/skills/gstack/design/src/serve.ts` | 48 |
| `updateDesignMd` | Function | `ext/skills/gstack/design/src/memory.ts` | 104 |
| `evolve` | Function | `ext/skills/gstack/design/src/evolve.ts` | 22 |
| `diffMockups` | Function | `ext/skills/gstack/design/src/diff.ts` | 18 |
| `verifyAgainstMockup` | Function | `ext/skills/gstack/design/src/diff.ts` | 92 |
| `generateCompareHtml` | Function | `ext/skills/gstack/design/src/compare.ts` | 19 |
| `compare` | Function | `ext/skills/gstack/design/src/compare.ts` | 621 |
| `startTestServer` | Function | `ext/skills/gstack/browse/test/test-server.ts` | 10 |
| `getCookiePickerHTML` | Function | `ext/skills/gstack/browse/src/cookie-picker-ui.ts` | 9 |
| `generatePickerCode` | Function | `ext/skills/gstack/browse/src/cookie-picker-routes.ts` | 36 |
| `handleCookiePickerRoute` | Function | `ext/skills/gstack/browse/src/cookie-picker-routes.ts` | 90 |
| `getExternalHosts` | Function | `ext/skills/gstack/hosts/index.ts` | 60 |
| `callJudge` | Function | `ext/skills/gstack/test/helpers/llm-judge.ts` | 31 |
| `makeRequest` | Function | `ext/skills/gstack/test/helpers/llm-judge.ts` | 34 |
| `judge` | Function | `ext/skills/gstack/test/helpers/llm-judge.ts` | 61 |
| `recordE2E` | Function | `ext/skills/gstack/test/helpers/e2e-helpers.ts` | 162 |
| `outcomeJudge` | Function | `ext/skills/gstack/test/helpers/llm-judge.ts` | 95 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → ResolveApiKey` | cross_community | 5 |
| `Main → BriefToPrompt` | cross_community | 4 |
| `Main → CreateSessionId` | cross_community | 4 |
| `Main → SessionPath` | cross_community | 4 |
| `HandleWriteCommand → IsBlockedIpv6` | cross_community | 4 |
| `Start → OpenBrowser` | cross_community | 3 |
| `HandleMetaCommand → GetActiveSession` | cross_community | 3 |
| `Main → PrintUsage` | intra_community | 3 |
| `Main → CallImageGeneration` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_894 | 7 calls |
| Cluster_952 | 4 calls |
| Cluster_951 | 4 calls |
| Cluster_870 | 3 calls |
| Cluster_936 | 3 calls |
| Cekwajar.id | 3 calls |
| Cluster_945 | 2 calls |
| Cluster_872 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "handleWriteCommand"})` — see callers and callees
2. `gitnexus_query({query: "test"})` — find related execution flows
3. Read key files listed above for implementation details
