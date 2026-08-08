import chalk from 'chalk';
import { logger } from '../utils/logger.js';
import { getAITypeDescription } from '../utils/detect.js';
import { AI_TYPES } from '../types/index.js';

export async function listCommand(): Promise<void> {
  logger.title('Taiwan Invoice Skill - Supported Platforms');

  console.log(chalk.cyan('Available AI Assistants:'));
  console.log();

  const platforms = [
    { key: 'claude', path: '.claude/skills/taiwan-invoice/' },
    { key: 'cursor', path: '.cursor/skills/taiwan-invoice/' },
    { key: 'windsurf', path: '.windsurf/skills/taiwan-invoice/' },
    { key: 'antigravity', path: '.agent/skills/taiwan-invoice/' },
    { key: 'copilot', path: '.github/skills/taiwan-invoice/' },
    { key: 'kiro', path: '.kiro/skills/taiwan-invoice/' },
    { key: 'codex', path: '.codex/skills/taiwan-invoice/' },
    { key: 'qoder', path: '.qoder/skills/taiwan-invoice/' },
    { key: 'cline', path: '.cline/skills/taiwan-invoice/' },
    { key: 'gemini', path: '.gemini/skills/taiwan-invoice/' },
    { key: 'trae', path: '.trae/skills/taiwan-invoice/' },
    { key: 'opencode', path: '.opencode/skills/taiwan-invoice/' },
    { key: 'continue', path: '.continue/skills/taiwan-invoice/' },
    { key: 'codebuddy', path: '.codebuddy/skills/taiwan-invoice/' },
  ];

  for (const platform of platforms) {
    const desc = getAITypeDescription(platform.key as any);
    const name = desc.split(' (')[0];
    console.log(`  ${chalk.green(platform.key.padEnd(15))} ${name}`);
    console.log(chalk.dim(`                    ${platform.path}`));
  }

  console.log();
  console.log(chalk.cyan('Installation:'));
  console.log(chalk.dim('  taiwan-invoice init --ai claude'));
  console.log(chalk.dim('  taiwan-invoice init --ai cursor'));
  console.log(chalk.dim('  taiwan-invoice init --ai windsurf'));
  console.log(chalk.dim('  taiwan-invoice init --ai copilot'));
  console.log(chalk.dim('  taiwan-invoice init --ai all'));
  console.log();
  console.log(chalk.cyan('Other Commands:'));
  console.log(chalk.dim('  taiwan-invoice versions    List available versions'));
  console.log(chalk.dim('  taiwan-invoice update      Update to latest version'));
  console.log();
}
