"""
Generate stub Jinja2 prompt templates for all agents that don't yet have one.
Run from project root: python scripts/generate_prompts.py
"""

from __future__ import annotations

from pathlib import Path
import yaml

STUB_TEMPLATE = """\
{{# prompts/role/{department}/{name}.j2 — auto-generated stub #}}
{{# Customize this template with {role}-specific instructions #}}
{{% extends "../../base.j2" %}}
"""

def main() -> None:
    dept_file = Path("config/departments.yaml")
    if not dept_file.exists():
        print("config/departments.yaml not found")
        return

    with dept_file.open() as f:
        departments = yaml.safe_load(f)

    created = 0
    for dept_name, dept_cfg in departments.items():
        for agent_name in dept_cfg.get("agents", {}):
            tmpl_path = Path(f"prompts/role/{dept_name}/{agent_name}.j2")
            if not tmpl_path.exists():
                tmpl_path.parent.mkdir(parents=True, exist_ok=True)
                role_display = agent_name.replace("_", " ").title()
                tmpl_path.write_text(
                    STUB_TEMPLATE.format(
                        department=dept_name,
                        name=agent_name,
                        role=role_display,
                    )
                )
                print(f"  created {tmpl_path}")
                created += 1
            else:
                print(f"  exists  {tmpl_path}")

    print(f"\n✓ Created {created} stub templates")


if __name__ == "__main__":
    main()
