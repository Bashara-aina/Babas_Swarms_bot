---
description: Perform janitorial tasks on C#/.NET code including cleanup, modernization, and tech debt remediation.
model: minimax-coding-plan/MiniMax-M2.7
temperature: 0.2
maxSteps: 30
permissions:
  edit: allow
  bash: allow
---
# .NET Upgrade Collection .NET Framework upgrade specialist for comprehensive project migration **Tags:** dotnet, upgrade, migration, framework, modernization ## Collection Usage ### .NET Upgrade Chat Mode Discover and plan your .NET upgrade journey! ```markdown, upgrade-analysis.prompt.md --- mode: dotnet-upgrade title: Analyze current .NET framework versions and create upgrade plan --- Analyze the repository and list each project's current TargetFramework along with the latest available LTS version from Microsoft's release schedule. Create an upgrade strategy prioritizing least-dependent projects first. ``` The upgrade chat mode automatically adapts to your repository's current .NET version and provides context-aware upgrade guidance to the next stable version. It will help you: - Auto-detect current .NET versions across all projects - Generate optimal upgrade sequences - Identify breaking changes and modernization opportunities - Create per-project upgrade flows --- ### .NET Upgrade Instructions Execute comprehensive .NET framework upgrades with structured guidance! The instructions provide: - Sequential upgrade strategies - Dependency analysis and sequencing - Framework targeting and code adjustments - NuGet and dependency management - CI/CD pipeline updates - Testing and validation procedures Use these instructions when implementing upgrade plans to ensure proper execution and validation. --- ### .NET Upgrade Prompts Quick access to specialized upgrade analysis prompts! The

[... truncated]