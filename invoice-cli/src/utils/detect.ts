import { existsSync } from 'node:fs';
import { join } from 'node:path';
import type { AIType } from '../types/index.js';

interface DetectionResult {
  detected: AIType[];
  suggested: AIType | null;
}

export function detectAIType(cwd: string = process.cwd()): DetectionResult {
  const detected: AIType[] = [];

  if (existsSync(join(cwd, '.claude'))) {
    detected.push('claude');
  }
  if (existsSync(join(cwd, '.cursor'))) {
    detected.push('cursor');
  }
  if (existsSync(join(cwd, '.windsurf'))) {
    detected.push('windsurf');
  }
  if (existsSync(join(cwd, '.agent'))) {
    detected.push('antigravity');
  }
  if (existsSync(join(cwd, '.github'))) {
    detected.push('copilot');
  }
  if (existsSync(join(cwd, '.kiro'))) {
    detected.push('kiro');
  }
  if (existsSync(join(cwd, '.codex'))) {
    detected.push('codex');
  }
  if (existsSync(join(cwd, '.qoder'))) {
    detected.push('qoder');
  }
  if (existsSync(join(cwd, '.cline'))) {
    detected.push('cline');
  }
  if (existsSync(join(cwd, '.gemini'))) {
    detected.push('gemini');
  }
  if (existsSync(join(cwd, '.trae'))) {
    detected.push('trae');
  }
  if (existsSync(join(cwd, '.opencode'))) {
    detected.push('opencode');
  }
  if (existsSync(join(cwd, '.continue'))) {
    detected.push('continue');
  }
  if (existsSync(join(cwd, '.codebuddy'))) {
    detected.push('codebuddy');
  }

  let suggested: AIType | null = null;
  if (detected.length === 1) {
    suggested = detected[0];
  } else if (detected.length > 1) {
    suggested = 'all';
  }

  return { detected, suggested };
}

export function getAITypeDescription(aiType: AIType): string {
  switch (aiType) {
    case 'claude':
      return 'Claude Code (.claude/skills/)';
    case 'cursor':
      return 'Cursor (.cursor/skills/)';
    case 'windsurf':
      return 'Windsurf (.windsurf/skills/)';
    case 'antigravity':
      return 'Antigravity (.agent/skills/)';
    case 'copilot':
      return 'GitHub Copilot (.github/skills/)';
    case 'kiro':
      return 'Kiro (.kiro/skills/)';
    case 'codex':
      return 'Codex CLI (.codex/skills/)';
    case 'qoder':
      return 'Qoder (.qoder/skills/)';
    case 'cline':
      return 'Cline (.cline/skills/)';
    case 'gemini':
      return 'Gemini CLI (.gemini/skills/)';
    case 'trae':
      return 'Trae (.trae/skills/)';
    case 'opencode':
      return 'OpenCode (.opencode/skills/)';
    case 'continue':
      return 'Continue (.continue/skills/)';
    case 'codebuddy':
      return 'CodeBuddy (.codebuddy/skills/)';
    case 'all':
      return 'All AI assistants';
  }
}
