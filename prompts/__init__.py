"""Prompts repository for the SwarmBot multi-agent orchestration system.

This module contains prompt templates and master prompts used across all agents
in the Babas Agency Swarm (Legion Swarm). It is organized as follows:

- ``base.j2``: Jinja2 base template inherited by all role-specific agent prompts.
  Defines the common structure: role identity, core competencies, task approach,
  context injection, available tools, and JSON response format.

- ``role/``: Directory of role-specific prompt templates organized by department
  (creative, design, engineering, legal_compliance, marketing, operations,
  product, research, vision_multimodal). Each department contains Jinja2
  templates that extend ``base.j2`` with department-specific role descriptions
  and capabilities.

Agents consume these prompts at runtime through the LLM client. Role-specific
templates are rendered with per-agent parameters (role name, department,
capabilities, context, tools, task) via the base.j2 template.
"""
