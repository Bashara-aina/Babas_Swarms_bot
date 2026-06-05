#!/usr/bin/env python3
"""
Seeds the memory store with critical project knowledge.
Run ONCE after setup: python scripts/bootstrap_memory.py
Safe to re-run — deduplication prevents double-storing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory.store import MemoryStore

store = MemoryStore()

CORE_KNOWLEDGE = [
    {
        "content": (
            "Babas_Swarms_bot is a Python multi-agent swarm system. "
            "Main entry point: main.py. "
            "Task orchestration: task_orchestrator.py. "
            "Request routing: router.py. "
            "Agent definitions: agents.py + agents/ directory. "
            "Legion multi-agent system: legion/ directory. "
            "LLM client: llm_client.py + llm_client/ directory. "
            "Bridge integrations: bridges/. "
            "Tool definitions: tools/. "
            "Skill handlers: skills/. "
            "Supabase integration: supabase/ directory."
        ),
        "agent_id": "shared",
        "memory_type": "semantic",
        "importance": 2.0,
    },
    {
        "content": (
            "Primary LLM: MiniMax M3 on $20/month flat plan. "
            "Context limit: 200K tokens per call. "
            "This limit is overcome by the InfiniteMemoryLLM wrapper "
            "which injects only the most relevant recalled context "
            "before each call. Compaction is disabled. "
            "Cache-read tokens dominate usage (4.77B in 25 days). "
            "Effective monthly cost: $20 flat regardless of token volume."
        ),
        "agent_id": "shared",
        "memory_type": "semantic",
        "importance": 2.0,
    },
    {
        "content": (
            "Infinite memory system: ChromaDB + all-MiniLM-L6-v2. "
            "Storage: ~/.swarms_memory/ (local persistent files). "
            "Embedder: 384-dim, fast CPU, ~20ms per embed. "
            "Deduplication: MD5 hash of content, no duplicates ever stored. "
            "Recall CLI: python -m core.memory.cli recall 'query'. "
            "Store CLI: python -m core.memory.cli remember 'content'. "
            "Status CLI: python -m core.memory.cli status."
        ),
        "agent_id": "shared",
        "memory_type": "semantic",
        "importance": 2.0,
    },
    {
        "content": (
            "Cekwajar suite: 5 B2C SaaS tools for Indonesian users. "
            "Wajar Slip: payslip verification. "
            "Wajar Gaji: salary fairness checker. "
            "Wajar Hidup: cost-of-living calculator. "
            "Wajar Tanah: land price checker. "
            "Wajar Kabur: emigration calculator. "
            "Tech stack: Next.js 14, TypeScript, Supabase, PDP Law compliant."
        ),
        "agent_id": "shared",
        "memory_type": "semantic",
        "importance": 1.5,
    },
    {
        "content": (
            "Academic research: Assembly action recognition on IKEA ASM dataset. "
            "Task: Multi-task learning for simultaneous pose estimation + activity classification. "
            "Key techniques: FiLM feature-wise linear modulation, "
            "Kendall uncertainty weighting, heatmap-based keypoint detection. "
            "Backbone: ResNet-50. Framework: PyTorch. "
            "Institution: Shibaura Institute of Technology, Japan."
        ),
        "agent_id": "shared",
        "memory_type": "semantic",
        "importance": 1.5,
    },
    {
        "content": (
            "OpenCode MCP tools connected (11 total): "
            "browser-use, crawl4ai, exa, filesystem, gitnexus, "
            "hermes, latex, obsidian, ruflo, sequential-thinking, websearch. "
            "These tools are available inside OpenCode sessions. "
            "OpenCode runs MiniMax M3, context was at 81% (165K/200K) "
            "when memory system was implemented on 2026-05-04."
        ),
        "agent_id": "opencode",
        "memory_type": "semantic",
        "importance": 1.5,
    },
    {
        "content": (
            "Rumahlabuh.com: rental and boarding house platform for Solo, Indonesia. "
            "Real estate data aggregation and marketplace. "
            "Part of the broader Cekwajar/Civora business ecosystem."
        ),
        "agent_id": "shared",
        "memory_type": "semantic",
        "importance": 1.0,
    },
]

print("🌱 Bootstrapping Babas Swarms memory store...\n")
total_stored = 0

for i, item in enumerate(CORE_KNOWLEDGE, 1):
    n = store.remember(**item)
    total_stored += n
    label = item["content"][:70].replace("\n", " ")
    print(f"  [{i}/{len(CORE_KNOWLEDGE)}] +{n} chunks | {label}...")

print("\n✅ Bootstrap complete.")
print(f"   New chunks stored: {total_stored}")
print(f"   Total in DB: {store.count()}")
print(f"   Storage: {store.status()['storage_path']}")
print("\n🧪 Test recall:")
print("   python -m core.memory.cli recall 'what is cekwajar'")