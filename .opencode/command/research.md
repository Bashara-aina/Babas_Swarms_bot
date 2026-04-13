# /research — Research and Document

Research the topic below and write a wiki article with findings.

## Steps
1. Check if already researched: grep -r "[topic]" .wiki/ --include="*.md" -l
   If found: read existing article, update if new info → do not duplicate
2. Read .wiki/raw/ for any relevant source files: find .wiki/raw/ -name "*[topic]*"
3. Research the topic using available code, configs, and raw/ sources
4. Write findings to .wiki/[type]/[slug].md following SCHEMA.md
5. Minimum: 300 words for research articles
6. Add to .wiki/INDEX.md under correct section

Verify: wc -w .wiki/[type]/[slug].md → must be >300
Verify: python3 -c "import yaml; yaml.safe_load(open('.wiki/[file]').read().split('---')[1]); print('YAML VALID')"

Topic to research: