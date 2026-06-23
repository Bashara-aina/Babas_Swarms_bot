'''core/incremental_summary.py — GAP-08: Incremental summary tracking.

Maintains a running summary of key session decisions, file changes, and context.
This is updated after each assistant turn and injected before compaction
to prevent the model from losing track of project state.
'''
import time

_decisions: list[str] = []
_file_changes: list[str] = []
_pain_points: list[str] = []
_next_moves: list[str] = []
_sticky_files: list[str] = []
_structural_snippets: dict[str, list[str]] = {}  # file_path -> list of structural items


def track_decision(decision: str) -> None:
    ts = time.strftime("%H:%M")
    _decisions.append(f"[{ts}] {decision}")
    if len(_decisions) > 50:
        _decisions[:] = _decisions[-50:]


def track_file_change(file_path: str, change: str) -> None:
    _file_changes.append(f"{file_path}: {change}")
    if file_path not in _sticky_files:
        _sticky_files.append(file_path)
    if len(_file_changes) > 100:
        _file_changes[:] = _file_changes[-100:]


def track_pain_point(point: str) -> None:
    _pain_points.append(point)
    if len(_pain_points) > 20:
        _pain_points[:] = _pain_points[-20:]


def track_next_move(move: str) -> None:
    if move not in _next_moves:
        _next_moves.insert(0, move)
    if len(_next_moves) > 10:
        _next_moves[:] = _next_moves[:10]


def add_sticky_file(file_path: str) -> None:
    if file_path not in _sticky_files:
        _sticky_files.append(file_path)


def get_summary() -> str:
    if not any([_decisions, _file_changes, _pain_points, _next_moves]):
        return ""

    lines = ["[INCREMENTAL SUMMARY — maintained across compactions]"]
    if _decisions:
        lines.append(f"\n## Decisions ({len(_decisions)})")
        for d in _decisions[-10:]:
            lines.append(f"- {d}")
    if _file_changes:
        lines.append(f"\n## File Changes ({len(_file_changes)})")
        for f in _file_changes[-10:]:
            lines.append(f"- {f}")
    if _pain_points:
        lines.append(f"\n## Pain Points ({len(_pain_points)})")
        for p in _pain_points[-5:]:
            lines.append(f"- {p}")
    if _next_moves:
        lines.append(f"\n## Next Moves ({len(_next_moves)})")
        for m in _next_moves[:5]:
            lines.append(f"- {m}")
    if _sticky_files:
        lines.append(f"\n## Sticky Files ({len(_sticky_files)})")
        lines.append(", ".join(_sticky_files[-10:]))
        # GAP-09: Include structural snippets for top sticky files
        for fp in _sticky_files[-3:]:
            snippet = get_structural_snippet(fp)
            if snippet:
                lines.append(f"  [{fp.split('/')[-1]}]: {snippet}")

    lines.append(f"\n[Last updated: {time.strftime('%H:%M:%S')} UTC]")
    return "\n".join(lines)


def inject_into_messages(messages: list[dict]) -> list[dict]:
    summary = get_summary()
    if not summary:
        return messages

    system_idx = None
    for i, m in enumerate(messages):
        if m.get("role") == "system":
            system_idx = i
            break

    if system_idx is not None:
        existing = messages[system_idx].get("content", "")
        messages[system_idx] = {
            **messages[system_idx],
            "content": f"{existing}\n\n{summary}"
        }
    else:
        messages.insert(0, {"role": "system", "content": summary})
    return messages


def reset() -> None:
    _decisions.clear()
    _file_changes.clear()
    _pain_points.clear()
    _next_moves.clear()
    _sticky_files.clear()
    _structural_snippets.clear()


def get_sticky_files() -> list[str]:
    return list(_sticky_files)


def extract_structural_snippet(file_path: str) -> str:
    """GAP-09: Extract structural items from a file (functions, classes, imports).

    Uses regex-based extraction as lightweight alternative to tree-sitter.
    For Python files: top-level def, class, import, from statements.
    """
    try:
        with open(file_path) as f:
            source = f.read()
    except Exception:
        return ""

    snippets: list[str] = []
    lines = source.split("\n")

    # Track indentation to detect top-level definitions
    for line in lines:
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)

        # Only top-level (indent 0) or module-level (indent 4, module body)
        if indent > 8:
            continue

        if stripped.startswith("def "):
            name = stripped[4:].split("(")[0]
            snippets.append(f"def {name}(...)")
        elif stripped.startswith("class "):
            name = stripped[6:].split("(")[0].split(":")[0]
            snippets.append(f"class {name}")
        elif stripped.startswith("from ") and " import " in stripped:
            snippets.append(stripped.split(" import ")[0].strip())
        elif stripped.startswith("import "):
            snippets.append(stripped.strip())

    snippet_text = " | ".join(snippets[:10])
    if snippet_text:
        _structural_snippets[file_path] = snippets
    return snippet_text


def get_structural_snippet(file_path: str) -> str:
    """Return cached or freshly-extracted structural snippet for a file."""
    cached = _structural_snippets.get(file_path)
    if cached:
        return " | ".join(cached[:8])
    return extract_structural_snippet(file_path)


async def incremental_summary_pre_compact_hook(ctx: dict) -> dict:
    """GAP-10: pre_compact hook — inject incremental summary + self-critique prompt.

    Two-pass compaction:
    1. Inject accumulated summary so model doesn't lose context
    2. Ask model to self-critique before summarizing
    """
    messages = ctx.get("messages", [])
    if messages:
        messages = inject_into_messages(messages)
        critique_prompt = (
            "\n[BEFORE COMPACTION — SELF-CRITIQUE]\n"
            "Review the conversation above and identify:\n"
            "1. Are we still on track to solve the original task?\n"
            "2. What files are we actively modifying? (mark as sticky)\n"
            "3. What is the single most important next step?\n"
            "This helps maintain context through compaction."
        )
        messages.append({"role": "user", "content": critique_prompt})
        ctx["messages"] = messages
    return ctx
