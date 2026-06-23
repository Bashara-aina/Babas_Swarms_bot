"""
Ruflo hook: auto-compress context before large tasks.
Triggered via: ruflo hooks_trigger pre_task_large
"""
import json
import sys

sys.path.insert(0, "/home/newadmin/swarm-bot/tools")
from context_maximizer import compress, count_tokens

LARGE_TASK_THRESHOLD = 20000

def pre_task_hook(task_context: dict) -> dict:
    content = task_context.get("context", "")
    tokens = count_tokens(content)

    if tokens < LARGE_TASK_THRESHOLD:
        return task_context

    task_type = task_context.get("type", "general")
    ratios = {
        "security_audit":  0.7,
        "full_feature":    0.5,
        "research":        0.4,
        "refactor":        0.6,
        "documentation":   0.5,
        "general":         0.55,
    }
    ratio = ratios.get(task_type, 0.55)

    result = compress(
        content,
        ratio=ratio,
        question=task_context.get("objective", ""),
    )

    task_context["context"] = result["compressed"]
    task_context["compression_meta"] = {
        "original_tokens": result["original_tokens"],
        "compressed_tokens": result["compressed_tokens"],
        "savings_pct": result["savings_pct"],
        "ratio_kept": ratio,
        "method": result["method"],
    }
    return task_context

if __name__ == "__main__":
    data = json.loads(sys.stdin.read())
    print(json.dumps(pre_task_hook(data), indent=2))
