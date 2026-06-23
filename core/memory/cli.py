"""
Memory management CLI.
Usage:
  python -m core.memory.infinite.cli status
  python -m core.memory.infinite.cli recall "how does legion work"
  python -m core.memory.infinite.cli remember "OpenCode session: implemented X"
"""
import argparse


def main():
    from .store import MemoryStore

    store = MemoryStore()

    parser = argparse.ArgumentParser(prog="memory", description="Swarms Memory CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show memory store stats")

    rc = sub.add_parser("recall", help="Search memories")
    rc.add_argument("query")
    rc.add_argument("--agent", default=None)
    rc.add_argument("--top_k", type=int, default=10)
    rc.add_argument("--min_score", type=float, default=0.25)

    rm = sub.add_parser("remember", help="Store a memory")
    rm.add_argument("content")
    rm.add_argument("--agent", default="shared")
    rm.add_argument("--type", dest="memory_type", default="semantic")

    args = parser.parse_args()

    if args.cmd == "status":
        s = store.status()
        print("\n🧠 Memory Store Status")
        print("─" * 40)
        for k, v in s.items():
            print(f"  {k}: {v}")

    elif args.cmd == "recall":
        print(f"\n🔍 Recalling: '{args.query}'\n")
        results = store.recall(
            args.query,
            agent_id=args.agent,
            top_k=args.top_k,
            min_score=args.min_score,
        )
        if not results:
            print("  No memories found.")
        for i, r in enumerate(results, 1):
            print(f"  [{i}] {r[:200]}{'...' if len(r) > 200 else ''}")

    elif args.cmd == "remember":
        n = store.remember(
            args.content,
            agent_id=args.agent,
            memory_type=args.memory_type,
        )
        print(f"✅ Stored {n} new chunk(s) (0 = duplicate, already known)")


if __name__ == "__main__":
    main()
