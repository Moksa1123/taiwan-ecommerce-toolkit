import chalk from 'chalk';
import { logger } from '../utils/logger.js';
import { getAITypeDescription } from '../utils/detect.js';
import { AI_TYPES } from '../types/index.js';

export async function listCommand(): Promise<void> {
  logger.title('Taiwan Logistics Skill - Supported Platforms');

  console.log(chalk.cyan('Available AI Assistants:'));
  console.log();

  const platforms = [
    { key: 'claude', path: '.claude/skills/taiwan-logistics/' },
    { key: 'cursor', path: '.cursor/skills/taiwan-logistics/' },
    { key: 'windsurf', path: '.windsurf/skills/taiwan-logistics/' },
    { key: 'antigravity', path: '.agent/skills/taiwan-logistics/' },
    { key: 'copilot', path: '.github/skills/taiwan-logistics/' },
    { key: 'kiro', path: '.kiro/skills/taiwan-logistics/' },
    { key: 'codex', path: '.codex/skills/taiwan-logistics/' },
    { key: 'qoder', path: '.qoder/skills/taiwan-logistics/' },
    { key: 'cline', path: '.cline/skills/taiwan-logistics/' },
    { key: 'gemini', path: '.gemini/skills/taiwan-logistics/' },
    { key: 'trae', path: '.trae/skills/taiwan-logistics/' },
    { key: 'opencode', path: '.opencode/skills/taiwan-logistics/' },
    { key: 'continue', path: '.continue/skills/taiwan-logistics/' },
    { key: 'codebuddy', path: '.codebuddy/skills/taiwan-logistics/' },
  ];

  for (const platform of platforms) {
    const desc = getAITypeDescription(platform.key as any);
    const name = desc.split(' (')[0];
    console.log(`  ${chalk.green(platform.key.padEnd(15))} ${name}`);
    console.log(chalk.dim(`                    ${platform.path}`));
  }

  console.log();
  console.log(chalk.cyan('Installation:'));
  console.log(chalk.dim('  taiwan-logistics init --ai claude'));
  console.log(chalk.dim('  taiwan-logistics init --ai cursor'));
  console.log(chalk.dim('  taiwan-logistics init --ai windsurf'));
  console.log(chalk.dim('  taiwan-logistics init --ai copilot'));
  console.log(chalk.dim('  taiwan-logistics init --ai all'));
  console.log();
  console.log(chalk.cyan('Other Commands:'));
  console.log(chalk.dim('  taiwan-logistics versions    List available versions'));
  console.log(chalk.dim('  taiwan-logistics update      Update to latest version'));
  console.log();
}
