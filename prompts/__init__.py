"""Prompts repository for the SwarmBot multi-agent orchestration system.

This module contains prompt templates and master prompts used across all agents
in the Babas Agency Swarm (Legion Swarm). It is organized as follows:

- ``base.j2``: Jinja2 base template inherited by all role-specific agent prompts.
  Defines the common structure: role identity, core competencies, task approach,
  context injection, available tools, and JSON response format.

- ``master_v4.md``: The authoritative master prompt for Legion Swarm V4. Defines the
  core identity of the Legion autonomous AI coworker, the 5-layer reasoning
  cascade, coding excellence standards, research protocol, computer use agentic
  loop, agent roster with routing logic, memory & learning injection order,
  quality checklists, emergency protocols, and operational modes (/think, /swarm,
  /do, /research).

- ``role/``: Directory of role-specific prompt templates organized by department
  (creative, design, engineering, legal_compliance, marketing, operations,
  product, research, vision_multimodal). Each department contains Jinja2
  templates that extend ``base.j2`` with department-specific role descriptions
  and capabilities.

Agents consume these prompts at runtime through the LLM client. The master_v4.md
is used as the top-level system prompt, while role-specific templates are rendered
with per-agent parameters (role name, department, capabilities, context, tools,
task) via the base.j2 template.
"""
