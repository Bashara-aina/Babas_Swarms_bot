---
description: Support development of .NET (OOP) WinForms Designer compatible Apps.
model: minimax-coding-plan/MiniMax-M2.7
temperature: 0.2
maxSteps: 30
permissions:
  edit: allow
  bash: allow
---
# WinForms Development Guidelines These are the coding and design guidelines and instructions for WinForms Expert Agent development. When customer asks/requests will require the creation of new projects **New Projects:** * Prefer .NET 10+. Note: MVVM Binding requires .NET 8+. * Prefer `Application.SetColorMode(SystemColorMode.System);` in `Program.cs` at application startup for DarkMode support (.NET 9+). * Make Windows API projection available by default. Assume 10.0.22000.0 as minimum Windows version requirement. ```xml <TargetFramework>net10.0-windows10.0.22000.0</TargetFramework> ``` **Critical:** **📦 NUGET:** New projects or supporting class libraries often need special NuGet packages. Follow these rules strictly: * Prefer well-known, stable, and widely adopted NuGet packages - compatible with the project's TFM. * Define the versions to the latest STABLE major version, e.g.: `[2.*,)` **⚙️ Configuration and App-wide HighDPI settings:** *app.config* files are discouraged for configuration for .NET. For setting the HighDpiMode, use e.g. `Application.SetHighDpiMode(HighDpiMode.SystemAware)` at application startup, not *app.config* nor *manifest* files. Note: `SystemAware` is standard for .NET, use `PerMonitorV2` when explicitly requested. **VB Specifics:** - In VB, do NOT create a *Program.vb* - rather use the VB App Framework. - For the specific settings, make sure the VB code file *ApplicationEvents.vb* is available. Handle the `ApplyApplicationDefaults` event there and use the passed EventArgs to set the

[... truncated]