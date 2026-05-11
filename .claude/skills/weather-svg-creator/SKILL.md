---
name: weather-svg-creator
description: Creates an SVG weather card showing the current temperature for Dubai. Writes the SVG to orchestration-workflow/weather.svg and updates orchestration-workflow/output.md.
---

# Weather SVG Creator Skill

Creates a visual SVG weather card for Dubai, UAE and writes the output files.

## Task

You will receive a temperature value and unit (Celsius or Fahrenheit) from the calling context. Create an SVG weather card and write both the SVG and a markdown summary.

## Instructions

1. **Create SVG** — Use the SVG template below, replacing placeholders with actual values
2. **Write SVG file** — Write to `orchestration-workflow/weather.svg`
3. **Write summary** — Write to `orchestration-workflow/output.md`

## SVG Template

```svg
<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="skyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#87CEEB;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#E0F6FF;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="400" height="300" fill="url(#skyGradient)" rx="20" ry="20"/>
  <text x="200" y="80" font-family="Arial, sans-serif" font-size="24" fill="#333" text-anchor="middle">Dubai Weather</text>
  <text x="200" y="150" font-family="Arial, sans-serif" font-size="72" fill="#FF6B35" text-anchor="middle">[TEMP]°[UNIT]</text>
  <text x="200" y="200" font-family="Arial, sans-serif" font-size="18" fill="#666" text-anchor="middle">Current Temperature</text>
  <text x="200" y="250" font-family="Arial, sans-serif" font-size="14" fill="#888" text-anchor="middle">Updated: [TIMESTAMP]</text>
</svg>
```

## Summary Template

```markdown
# Dubai Weather Report

- **Temperature**: [TEMP]°[UNIT]
- **Location**: Dubai, UAE
- **Timestamp**: [TIMESTAMP]

## SVG Card

SVG weather card saved to `orchestration-workflow/weather.svg`
```

## Rules

- Use the exact temperature value and unit provided — do not re-fetch or modify
- The SVG must be self-contained and valid
- Both output files go in the `orchestration-workflow/` directory
- Create the `orchestration-workflow/` directory if it doesn't exist