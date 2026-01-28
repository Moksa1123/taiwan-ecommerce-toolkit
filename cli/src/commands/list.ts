import chalk from 'chalk';
import { logger } from '../utils/logger.js';
import { getAITypeDescription } from '../utils/detect.js';
import { AI_TYPES } from '../types/index.js';

export async function listCommand(): Promise<void> {
  logger.title('Taiwan Invoice Skill - Supported Platforms');

  console.log(chalk.cyan('Available AI Assistants:'));
  console.log();

  const platforms = [
    { key: 'claude', project: '.claude/skills/taiwan-invoice/', global: '~/.claude/skills/' },
    { key: 'cursor', project: '.cursor/skills/taiwan-invoice/', global: '~/.cursor/skills/' },
    { key: 'antigravity', project: '.agent/skills/taiwan-invoice/', global: '~/.gemini/antigravity/global_skills/' },
  ];

  for (const platform of platforms) {
    const desc = getAITypeDescription(platform.key as any);
    console.log(`  ${chalk.green(platform.key.padEnd(15))} ${desc.split(' ')[0]} ${desc.split(' ')[1] || ''}`);
    console.log(chalk.dim(`                    Project: ${platform.project}`));
    console.log(chalk.dim(`                    Global:  ${platform.global}`));
    console.log();
  }

  console.log(chalk.cyan('Installation:'));
  console.log(chalk.dim('  taiwan-invoice init --ai claude'));
  console.log(chalk.dim('  taiwan-invoice init --ai cursor'));
  console.log(chalk.dim('  taiwan-invoice init --ai antigravity'));
  console.log(chalk.dim('  taiwan-invoice init --ai all'));
  console.log();
}
