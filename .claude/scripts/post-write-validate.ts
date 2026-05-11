#!/usr/bin/env node

/**
 * PostToolUse Hook — obsidian-mind
 *
 * Runs after writing a .md file. Validates frontmatter and checks wikilinks.
 */

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const VAULT_ROOT = process.cwd();
const WIKI_DIR = join(VAULT_ROOT, '.wiki');

// Required frontmatter by template type
const REQUIRED_FIELDS: Record<string, string[]> = {
  'work': ['date', 'description', 'project', 'status'],
  'decision': ['date', 'description', 'status', 'owner'],
  'incident': ['date', 'ticket', 'severity', 'role'],
  '1-1': ['date', 'person', 'key-takeaways'],
  'competency': ['date', 'description', 'current-level', 'target-level']
};

function parseFrontmatter(content: string): Record<string, string> {
  const fm: Record<string, string> = {};
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (match) {
    for (const line of match[1].split('\n')) {
      const [key, ...valueParts] = line.split(':');
      if (key && valueParts.length) {
        fm[key.trim()] = valueParts.join(':').trim();
      }
    }
  }
  return fm;
}

function checkWikilinks(content: string): { valid: string[]; broken: string[] } {
  const valid: string[] = [];
  const broken: string[] = [];

  // Find all wikilinks
  const wikilinkPattern = /\[\[([^\]]+)\]\]/g;
  let match;
  while ((match = wikilinkPattern.exec(content)) !== null) {
    const link = match[1];
    // Skip external links and anchors
    if (link.includes('://') || link.startsWith('#')) continue;

    // Check if linked file exists (without extension)
    const notePath = join(WIKI_DIR, link.replace(/\.md$/, '') + '.md');
    if (existsSync(notePath)) {
      valid.push(link);
    } else {
      broken.push(link);
    }
  }

  return { valid, broken };
}

function validateNote(filePath: string): { valid: boolean; errors: string[]; warnings: string[] } {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!existsSync(filePath)) {
    errors.push(`File does not exist: ${filePath}`);
    return { valid: false, errors, warnings };
  }

  const content = readFileSync(filePath, 'utf-8');
  const frontmatter = parseFrontmatter(content);

  // Check for frontmatter
  if (!content.startsWith('---')) {
    errors.push('Missing frontmatter');
  }

  // Check wikilinks
  const { valid, broken } = checkWikilinks(content);
  if (broken.length > 0) {
    warnings.push(`Broken wikilinks: ${broken.join(', ')}`);
  }

  // Detect template type from path or content
  const relativePath = filePath.replace(WIKI_DIR + '/', '');
  let templateType = 'unknown';

  if (relativePath.startsWith('work/active/') || relativePath.startsWith('work/archive/')) {
    templateType = 'work';
  } else if (relativePath.startsWith('brain/Key Decisions')) {
    templateType = 'decision';
  } else if (relativePath.startsWith('work/incidents/')) {
    templateType = 'incident';
  } else if (relativePath.startsWith('work/1-1/')) {
    templateType = '1-1';
  } else if (relativePath.startsWith('perf/competencies/')) {
    templateType = 'competency';
  }

  // Check required fields
  if (templateType !== 'unknown' && REQUIRED_FIELDS[templateType]) {
    for (const field of REQUIRED_FIELDS[templateType]) {
      if (!frontmatter[field]) {
        errors.push(`Missing required field: ${field}`);
      }
    }
  }

  // Warn about notes without links
  if (valid.length === 0 && broken.length === 0 && !relativePath.includes('templates/')) {
    warnings.push('Note has no wikilinks — orphan candidate');
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}

async function main() {
  const filePath = process.argv[2] || '';

  if (!filePath || !filePath.endsWith('.md')) {
    console.log(JSON.stringify({ valid: true, errors: [], warnings: [] }));
    return;
  }

  const result = validateNote(filePath);
  console.log(JSON.stringify(result));

  if (!result.valid) {
    process.exit(1);
  }
}

main().catch(console.error);
