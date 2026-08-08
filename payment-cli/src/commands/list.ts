import chalk from 'chalk';
import { logger } from '../utils/logger.js';
import { detectAIType, getAITypeDescription } from '../utils/detect.js';

interface Platform {
  name: string;
  folder: string;
  description: string;
}

const PLATFORMS: Platform[] = [
  { name: 'claude', folder: '.claude', description: 'Claude Code (Anthropic)' },
  { name: 'cursor', folder: '.cursor', description: 'Cursor Editor' },
  { name: 'windsurf', folder: '.windsurf', description: 'Windsurf (Codeium)' },
  { name: 'antigravity', folder: '.agent', description: 'Antigravity (Google)' },
  { name: 'copilot', folder: '.github', description: 'GitHub Copilot' },
  { name: 'kiro', folder: '.kiro', description: 'Kiro (AWS)' },
  { name: 'codex', folder: '.codex', description: 'Codex CLI (OpenAI)' },
  { name: 'qoder', folder: '.qoder', description: 'Qodo (Qoder)' },
  { name: 'cline', folder: '.cline', description: 'Cline' },
  { name: 'gemini', folder: '.gemini', description: 'Gemini CLI' },
  { name: 'trae', folder: '.trae', description: 'Trae (ByteDance)' },
  { name: 'opencode', folder: '.opencode', description: 'OpenCode' },
  { name: 'continue', folder: '.continue', description: 'Continue.dev' },
  { name: 'codebuddy', folder: '.codebuddy', description: 'CodeBuddy' },
];

export function listCommand(): void {
  logger.title('Supported AI Platforms');

  const { detected } = detectAIType();

  console.log();
  console.log(`  ${chalk.dim('Platform'.padEnd(15))} ${chalk.dim('Folder'.padEnd(12))} ${chalk.dim('Status')}`);
  console.log(`  ${chalk.dim('─'.repeat(45))}`);

  for (const platform of PLATFORMS) {
    const isDetected = detected.includes(platform.name);
    const status = isDetected ? chalk.green('● Detected') : chalk.dim('Available');
    const name = isDetected ? chalk.cyan(platform.name.padEnd(15)) : platform.name.padEnd(15);

    console.log(`  ${name} ${chalk.dim(platform.folder.padEnd(12))} ${status}`);
  }

  console.log();
  console.log(chalk.dim('  Use: taiwan-payment init --ai <platform>'));
  console.log(chalk.dim('  Or:  taiwan-payment init --ai all'));
  console.log();
}
