"""M2.7 Skeleton-of-Thought Engine — component skeleton generation before implementation.

Generate complete skeletons BEFORE writing any implementation.
For every component, function, module — skeleton first, implementation second.

Reference: imagination-research/sot (ICLR 2024) — "generate skeleton first, then implement"
Reference: M2.7 Full Capability Activation — Technique 3 (SoT)

Usage:
    eng = SoTEngine()
    skel = eng.generate_function_skeleton(
        name="fetch_user",
        args={"user_id": ("int", "Telegram user ID")},
        return_type="User | None",
    )
    print(eng.render_skeleton_md(skel))
    # Builder fills IMPLEMENTATION block after reviewing skeleton
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

# ---------------------------------------------------------------------------
# Enums and models
# ---------------------------------------------------------------------------


class ComponentType(Enum):
    """Categories of components that SoT can skeleton."""

    COMPONENT = "component"       # React/Next.js UI component
    FUNCTION = "function"         # Python function (default)
    MODULE = "module"             # Python module/package
    API_ROUTE = "api_route"       # FastAPI/Next.js API route
    AGENT = "agent"               # AI agent class
    DATABASE = "database"        # DB schema/migration
    TOOL = "tool"                # CLI tool/script
    WORKER = "worker"            # Background worker


@dataclass
class SkeletonBlock:
    """A single labeled section of a skeleton."""

    label: str      # e.g. "PROPS CONTRACT", "SEQUENCE"
    content: str    # The skeleton content for this section
    order: int      # Display order


@dataclass
class ComponentSkeleton:
    """Complete skeleton for a component — fill IMPLEMENTATION before building.

    SoT Protocol:
      1. Generate skeleton with generate_skeleton() / generate_function_skeleton()
      2. Review with render_skeleton_md() — verify all edge cases are covered
      3. Builder fills IMPLEMENTATION block
      4. Never write implementation before skeleton is complete
    """

    name: str
    component_type: ComponentType
    responsibility: str           # Single-sentence description
    blocks: list[SkeletonBlock] = field(default_factory=list)
    edge_cases: list[str] = field(default_factory=list)
    implementation_notes: list[str] = field(default_factory=list)  # Builder's notes

    def add_block(self, label: str, content: str, order: int) -> None:
        """Add a labeled block to the skeleton."""
        self.blocks.append(SkeletonBlock(label=label, content=content, order=order))
        self.blocks.sort(key=lambda b: b.order)

    def to_markdown(self) -> str:
        """Render skeleton as markdown for Bashara review / hand-off to Builder."""
        lines = [
            f"## {self.name} — {self.component_type.value.upper()}",
            f"**Responsibility:** {self.responsibility}",
            "",
        ]
        for block in self.blocks:
            lines.append(f"### {block.label}")
            lines.append(block.content)
            lines.append("")

        if self.edge_cases:
            lines.append("### EDGE CASES")
            for ec in self.edge_cases:
                lines.append(f"- [ ] {ec}")
            lines.append("")

        lines.append("### IMPLEMENTATION")
        lines.append("```")
        lines.append(f"async def {self._to_snake(self.name)}(...):")
        lines.append("    # Implement after skeleton review approval.")
        lines.append("```")

        return "\n".join(lines)

    def to_pydantic(self) -> str:
        """Generate Pydantic BaseModel from skeleton (for function args)."""
        if self.component_type != ComponentType.FUNCTION:
            return ""

        lines = [
            "from pydantic import BaseModel, Field",
            "from __future__ import annotations",
            "",
            "",
            f"class {self._to_pascal(self.name)}Input(BaseModel):",
        ]

        for block in self.blocks:
            if block.label != "PROPS CONTRACT":
                continue
            # Parse props from block.content
            for line in block.content.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Match patterns like "arg_name: type  # description"
                prop_match = re.match(r"(\w+)\s*:\s*(\w+)\s*(?:=\s*([^,]+))?\s*(?:#\s*(.*))?$", line)
                if prop_match:
                    name, ptype, default, desc = prop_match.groups()
                    desc_str = f' = Field(description="{desc}")' if desc else ""
                    if default:
                        lines.append(f"    {name}: {ptype} = {default}{desc_str}")
                    else:
                        lines.append(f"    {name}: {ptype}{desc_str}")

        return "\n".join(lines)

    def _to_snake(self, name: str) -> str:
        """Convert PascalCase/camelCase to snake_case."""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _to_pascal(self, name: str) -> str:
        """Convert snake_case to PascalCase."""
        return "".join(word.capitalize() for word in name.split("_"))


# ---------------------------------------------------------------------------
# SoT Engine
# ---------------------------------------------------------------------------


class SoTEngine:
    """Skeleton-of-Thought generator.

    Call generate_skeleton() BEFORE writing any implementation.
    Pass the result to Builder as the contract to implement against.

    SoT is the discipline that prevents "implementation before thinking" —
    which is the primary failure mode of fast LLM coding.

    Usage:
        eng = SoTEngine()

        # For a Python function:
        skel = eng.generate_function_skeleton(
            name="fetch_user",
            args={"user_id": ("int", "Telegram user ID"), "ctx": ("dict", "bot context")},
            return_type="User | None",
            raises=["ValueError", "TelegramError"],
        )

        # For a React component:
        skel = eng.generate_component_skeleton(
            name="UserCard",
            props={"user": ("User", "user object"), "onSelect": ("() => void", "callback")},
            description="Displays user info with avatar and action buttons",
        )

        # Review the skeleton before implementing:
        print(eng.render_skeleton_md(skel))
    """

    def generate_skeleton(
        self,
        name: str,
        component_type: ComponentType,
        responsibility: str,
        props_or_args: dict[str, tuple[str, str]] | None = None,
        existing_files: list[str] | None = None,
    ) -> ComponentSkeleton:
        """Generate a complete skeleton for any component.

        Auto-detects type and routes to specialized generators.

        Args:
            name: Component name
                - PascalCase for components (UserCard, DashboardStats)
                - snake_case for functions (fetch_user, process_payment)
            component_type: What kind of component this is
            responsibility: One-sentence description of what it does
            props_or_args: For components: {prop: (typescript_type, description)}
                          For functions: {arg: (python_type, description)}
            existing_files: Existing files in the same module (avoid duplication)

        Returns:
            ComponentSkeleton with all sections filled except IMPLEMENTATION.
            Builder fills IMPLEMENTATION after reviewing the skeleton.
        """
        if not name or not name.strip():
            raise ValueError("Component name cannot be empty")

        props_or_args = props_or_args or {}

        if component_type == ComponentType.COMPONENT:
            return self.generate_component_skeleton(
                name=name.strip(),
                props=props_or_args,
                description=responsibility,
            )
        elif component_type in (ComponentType.API_ROUTE, ComponentType.DATABASE):
            return self._generate_module_skeleton(
                name=name.strip(),
                component_type=component_type,
                responsibility=responsibility,
                props_or_args=props_or_args,
            )
        else:
            # Default to function skeleton
            return self.generate_function_skeleton(
                name=name.strip(),
                args=props_or_args,
                return_type="Any",
                raises=None,
            )

    def generate_function_skeleton(
        self,
        name: str,
        args: dict[str, tuple[str, str]],
        return_type: str,
        raises: list[str] | None = None,
        is_async: bool = True,
    ) -> ComponentSkeleton:
        """Specialized skeleton for Python functions.

        Includes SCoT (Structured Chain-of-Thought) blocks:
        - SEQUENCE: initialization → validation → processing → output
        - BRANCH: decision points, guards, error paths
        - LOOP: iteration patterns if any

        Args:
            name: Function name (snake_case)
            args: {arg_name: (type_str, description)}
            return_type: Return type annotation
            raises: List of exception types this function may raise
            is_async: Whether this is an async function
        """
        if not args:
            args = {}

        skel = ComponentSkeleton(
            name=name,
            component_type=ComponentType.FUNCTION,
            responsibility=f"{name} — fill after skeleton review",
        )

        # 1. PROPS CONTRACT
        props_lines = ["```python", f"def {name}("]
        for arg_name, (arg_type, desc) in args.items():
            props_lines.append(f"    {arg_name}: {arg_type},  # {desc}")
        props_lines.append(f") -> {return_type}:")
        if raises:
            props_lines.append(f"    # Raises: {', '.join(raises)}")
        props_lines.append("```")

        skel.add_block(
            label="1. PROPS CONTRACT",
            content="\n".join(props_lines),
            order=1,
        )

        # 2. SEQUENCE (SCoT — initialization → validation → processing → output)
        seq_lines = [
            "```",
            f"def {name}({', '.join(args.keys())}) -> {return_type}:",
            "    # SEQUENCE:",
            "    # 1. [INIT] Validate inputs — early return on invalid",
            "    # 2. [PROCESS] Core logic",
            "    # 3. [OUTPUT] Return result or raise",
            "```",
        ]
        skel.add_block(label="2. SEQUENCE (Initialization → Validation → Processing → Output)", content="\n".join(seq_lines), order=2)

        # 3. BRANCH (decision points, guards)
        branch_lines = [
            "```python",
            f"def {name}({', '.join(args.keys())}) -> {return_type}:",
            "    # BRANCH — decision points:",
            "    if <condition>:",
            "        ...  # path A",
            "    else:",
            "        ...  # path B",
            "",
            "    # GUARD clauses — fail fast:",
            "    if not <valid_input>:",
            "        raise <Exception>  # or return None/error tuple",
            "```",
        ]
        skel.add_block(label="3. BRANCH (Decision Points, Guards, Error Paths)", content="\n".join(branch_lines), order=3)

        # 4. LOOP (iteration patterns)
        loop_lines = [
            "```python",
            f"def {name}({', '.join(args.keys())}) -> {return_type}:",
            "    # LOOP — only if iteration is needed:",
            "    results: list[Something] = []",
            "    for item in collection:",
            "        if <filter_condition>:",
            "            results.append(transform(item))",
            "    return results",
            "",
            "    # Async loop:",
            "    # async for item in async_iterator:",
            "    #     ... ",
            "```",
        ]
        skel.add_block(label="4. LOOP (Iteration Patterns, Async Chains)", content="\n".join(loop_lines), order=4)

        # 5. EDGE CASES
        edge_cases = self._default_edge_cases(args)
        skel.edge_cases = edge_cases
        skel.add_block(
            label="5. EDGE CASES",
            content=self._render_edge_cases_markdown(edge_cases),
            order=5,
        )

        # 6. IMPLEMENTATION (empty — Builder fills this)
        func_keyword = "async def" if is_async else "def"
        impl_lines = [
            "```python",
            f"{func_keyword} {name}({', '.join(self._format_args(args))}) -> {return_type}:",
            "    # REVIEW skeleton above first.",
            "    # Then implement:",
            "    ...",
            "```",
        ]
        skel.add_block(
            label="6. IMPLEMENTATION (Builder fills after skeleton review)",
            content="\n".join(impl_lines),
            order=6,
        )

        return skel

    def generate_component_skeleton(
        self,
        name: str,
        props: dict[str, tuple[str, str]],
        description: str,
    ) -> ComponentSkeleton:
        """Specialized skeleton for React/Next.js components (TypeScript).

        Includes all the UI-specific blocks required for 375px/1280px/dark mode testing.

        Args:
            name: Component name (PascalCase)
            props: {propName: (typescript_type, description)}
            description: One-sentence component description
        """
        if not props:
            props = {}

        skel = ComponentSkeleton(
            name=name,
            component_type=ComponentType.COMPONENT,
            responsibility=description,
        )

        # 1. PROPS CONTRACT — TypeScript interface
        props_interface = [
            f"interface {name}Props {{",
        ]
        for prop_name, (prop_type, desc) in props.items():
            # Convert camelCase prop_name to PascalCase for TS convention if needed
            safe_prop = prop_name
            props_interface.append(f"  /** {desc} */")
            props_interface.append(f"  readonly {safe_prop}: {prop_type};")
        props_interface.append("}")
        props_lines = [
            "```typescript",
            *props_interface,
            "```",
        ]
        skel.add_block(label="1. PROPS CONTRACT (TypeScript)", content="\n".join(props_lines), order=1)

        # 2. STATE REQUIREMENTS
        state_lines = [
            "```typescript",
            f"// {name} State Requirements:",
            "",
            "// Local state:",
            "const [isLoading, setIsLoading] = useState(false);",
            "const [error, setError] = useState<string | null>(null);",
            "",
            "// Server state:",
            "// - data: fetched via useQuery/useSWR (describe query key + fetcher)",
            "// - mutation: useMutation for writes",
            "",
            "// Derived state:",
            "// const isEmpty = data?.length === 0;",
            "// const sortedData = useMemo(() => sort(data), [data]);",
            "```",
        ]
        skel.add_block(label="2. STATE REQUIREMENTS", content="\n".join(state_lines), order=2)

        # 3. SUB-COMPONENTS NEEDED
        sub_lines = [
            "```tsx",
            f"// {name} — Sub-components to build (bottom-up):",
            "",
            "// Child components (build these first):",
            "// - {ChildComponent} — describe what it does",
            "// - {AnotherChild} — describe what it does",
            "",
            "// Composition:",
            f"// <{name}Wrapper>",
            f"//   <{name}Header />",
            f"//   <{name}Body />",
            f"//   <{name}Footer />",
            f"// </{name}Wrapper>",
            "```",
        ]
        skel.add_block(label="3. SUB-COMPONENTS NEEDED (bottom-up)", content="\n".join(sub_lines), order=3)

        # 4. SIDE EFFECTS
        effects_lines = [
            "```typescript",
            f"// {name} — Side Effects:",
            "",
            "useEffect(() => {",
            "    // [WHEN] data loads / prop changes",
            "    // [WHAT] fetch, subscribe, or compute",
            "    // [CLEANUP] return () => unsubscribe / cancel",
            "}, [/* dependency array */]);",
            "",
            "// Keyboard / accessibility:",
            "// useEffect(() => {",
            "//   const handleKeyDown = (e: KeyboardEvent) => { ... };",
            "//   window.addEventListener('keydown', handleKeyDown);",
            "//   return () => window.removeEventListener('keydown', handleKeyDown);",
            "// }, []);",
            "```",
        ]
        skel.add_block(label="4. SIDE EFFECTS (useEffect dependencies)", content="\n".join(effects_lines), order=4)

        # 5. EDGE CASES (UI-specific)
        ui_edge_cases = [
            "Loading state — show Skeleton component while data?.length === undefined",
            "Empty state — data?.length === 0 → show EmptyState message",
            "Error state — error !== null → show ErrorBanner with retry button",
            "Mobile layout (375px) — does component still render without horizontal scroll?",
            "Dark mode — verify colors, borders, shadows in dark theme",
            "Keyboard navigation — can tab through all interactive elements?",
            "Zero data / null data — does component handle empty props gracefully?",
            "Maximum data (100+ items) — does list/virtualization work at scale?",
            "Long text / overflow — truncate with ellipsis or word-break?",
            "Accessibility — aria-labels, role attributes, focus management?",
        ]
        skel.edge_cases = ui_edge_cases
        skel.add_block(
            label="5. EDGE CASES (UI — test at 375px + 1280px + dark mode)",
            content=self._render_edge_cases_markdown(ui_edge_cases),
            order=5,
        )

        # 6. IMPLEMENTATION (empty)
        impl_lines = [
            "```tsx",
            f"export function {name}({{",
        ]
        for prop_name, (prop_type, _) in props.items():
            safe_prop = prop_name
            impl_lines.append(f"  {safe_prop},")
        impl_lines.append(f"}}: {name}Props) {{")
        impl_lines.append("  // Review skeleton above.")
        impl_lines.append("  // Implement after verifying edge cases.")
        impl_lines.append("  return <div>{/* fill implementation */}</div>;")
        impl_lines.append("}")
        impl_lines.append("```")
        skel.add_block(
            label="6. IMPLEMENTATION (Builder fills after skeleton review)",
            content="\n".join(impl_lines),
            order=6,
        )

        return skel

    def _generate_module_skeleton(
        self,
        name: str,
        component_type: ComponentType,
        responsibility: str,
        props_or_args: dict[str, tuple[str, str]],
    ) -> ComponentSkeleton:
        """Skeleton for MODULE, API_ROUTE, DATABASE types."""
        skel = ComponentSkeleton(
            name=name,
            component_type=component_type,
            responsibility=responsibility,
        )

        skel.add_block(
            label="1. RESPONSIBILITY",
            content=f"**{name}** — {responsibility}\n\n"
                    f"Type: {component_type.value}\n\n"
                    "Before implementing, verify:\n"
                    "- [ ] Single responsibility (does one thing well)\n"
                    "- [ ] Fits within existing architecture\n"
                    "- [ ] No circular dependencies with existing modules",
            order=1,
        )

        if component_type == ComponentType.API_ROUTE:
            skel.add_block(
                label="2. ENDPOINT CONTRACT",
                content="```python\n"
                        "# Route: POST /api/{name}\n"
                        "# Request body:\n"
                        "# Response: 200 | 400 | 401 | 500\n"
                        "# Auth: required | optional | none\n"
                        "```",
                order=2,
            )
        elif component_type == ComponentType.DATABASE:
            skel.add_block(
                label="2. SCHEMA CONTRACT",
                content="```sql\n"
                        "-- Table: {name}\n"
                        "-- Indexes: ...\n"
                        "-- Foreign keys: ...\n"
                        "-- RLS policies: ...\n"
                        "```",
                order=2,
            )

        skel.edge_cases = [
            "Module initialization failure — does it fail loudly?",
            "Missing configuration — env vars present at import time?",
            "Circular import risk — does this create dependency cycles?",
            "Graceful degradation — does it work without optional dependencies?",
        ]
        skel.add_block(
            label="3. EDGE CASES",
            content=self._render_edge_cases_markdown(skel.edge_cases),
            order=3,
        )
        skel.add_block(
            label="4. IMPLEMENTATION",
            content="# Builder fills after skeleton review",
            order=4,
        )

        return skel

    def render_skeleton_md(self, skeleton: ComponentSkeleton) -> str:
        """Render a ComponentSkeleton as formatted markdown string.

        This is the output shown to Bashara for review before Builder implements.

        Args:
            skeleton: The skeleton to render

        Returns:
            Markdown string with all blocks expanded
        """
        return skeleton.to_markdown()

    def _default_edge_cases(
        self, args: dict[str, tuple[str, str]]
    ) -> list[str]:
        """Generate default edge cases from function arguments."""
        cases = [
            "Input validation — each arg within valid range?",
            "None / null input — does function handle gracefully?",
            "Empty string / empty collection — defined behavior?",
            "Maximum data — does it scale or OOM at 10k items?",
            "Concurrent calls — race condition or dead lock?",
            "Timeout — long-running function has timeout guard?",
            "Exception during execution — logged with full context?",
            "Async edge cases — cancellation token propagated?",
        ]

        # Add per-arg edge cases
        for arg_name in args:
            cases.append(f"Argument '{arg_name}' = None → defined behavior?")
            cases.append(f"Argument '{arg_name}' = unexpected type → TypeError prevention?")

        return cases[:12]  # Cap at 12 edge cases

    def _render_edge_cases_markdown(self, edge_cases: list[str]) -> str:
        """Render edge cases as a checklist in markdown."""
        lines = ["```", "□ Loading state", "□ Empty state", "□ Error state"]
        for ec in edge_cases:
            stripped = ec.strip()
            if stripped.startswith("["):
                lines.append(f"  {stripped}")
            else:
                lines.append(f"□ {stripped}")
        lines.append("```")
        return "\n".join(lines)

    def _format_args(self, args: dict[str, tuple[str, str]]) -> list[str]:
        """Format args dict as string list for function signature."""
        result = []
        for arg_name, (arg_type, _) in args.items():
            result.append(f"{arg_name}: {arg_type}")
        return result


# ---------------------------------------------------------------------------
# Convenience singleton
# ---------------------------------------------------------------------------

_sot_engine: SoTEngine | None = None


def get_sot_engine() -> SoTEngine:
    """Return global SoTEngine singleton."""
    global _sot_engine
    if _sot_engine is None:
        _sot_engine = SoTEngine()
    return _sot_engine
