#!/usr/bin/env node
/**
 * Obsidian MCP Wrapper - Fixes tags handling
 * 
 * This wrapper intercepts calls to save_knowledge_note and save_code_snippet
 * and converts string tags to arrays before passing to the original handler.
 */

import { spawn } from 'child_process';
import { Readable } from 'stream';

const server = spawn('npx', ['-y', '@iflow-mcp/kynlos-obsidian-mcp-server', '/home/newadmin/swarm-bot/.wiki'], {
  stdio: ['pipe', 'pipe', 'pipe']
});

let buffer = '';

server.stdout.on('data', (data) => {
  buffer += data.toString();
  // Process complete JSON lines
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';
  
  for (const line of lines) {
    if (line.trim()) {
      // Check if this is a tool call request
      try {
        const msg = JSON.parse(line);
        if (msg.method === 'tools/call' && msg.params?.name) {
          const args = msg.params.arguments || {};
          
          // Fix tags for save_knowledge_note
          if (msg.params.name === 'save_knowledge_note' && args.tags) {
            if (typeof args.tags === 'string') {
              args.tags = [args.tags];
              console.error('[OBSIDIAN-WRAPPER] Fixed tags for save_knowledge_note:', JSON.stringify(args.tags));
            }
          }
          
          // Fix tags for save_code_snippet
          if (msg.params.name === 'save_code_snippet' && args.tags) {
            if (typeof args.tags === 'string') {
              args.tags = [args.tags];
              console.error('[OBSIDIAN-WRAPPER] Fixed tags for save_code_snippet:', JSON.stringify(args.tags));
            }
          }
        }
      } catch (e) {
        // Not JSON, passthrough
      }
    }
    process.stdout.write(line + '\n');
  }
});

server.stderr.on('data', (data) => {
  process.stderr.write(data);
});

server.on('close', (code) => {
  process.exit(code);
});

// Pipe stdin to server
process.stdin.pipe(server.stdin);
