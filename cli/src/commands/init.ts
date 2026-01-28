import chalk from 'chalk';
import ora from 'ora';
import prompts from 'prompts';
import type { AIType } from '../types/index.js';
import { AI_TYPES } from '../types/index.js';
import { generatePlatformFiles, generateAllPlatformFiles } from '../utils/template.js';
import { detectAIType, getAITypeDescription } from '../utils/detect.js';
import { logger } from '../utils/logger.js';

interface InitOptions {
  ai?: AIType;
  force?: boolean;
  global?: boolean;
}

export async function initCommand(options: InitOptions): Promise<void> {
  logger.title('Taiwan Invoice Skill Installer');

  let aiType = options.ai;

  // Auto-detect or prompt for AI type
  if (!aiType) {
    const { detected, suggested } = detectAIType();

    if (detected.length > 0) {
      logger.info(`Detected: ${detected.map(t => chalk.cyan(t)).join(', ')}`);
    }

    const response = await prompts({
      type: 'select',
      name: 'aiType',
      message: 'Select AI assistant to install for:',
      choices: AI_TYPES.map(type => ({
        title: getAITypeDescription(type),
        value: type,
      })),
      initial: suggested ? AI_TYPES.indexOf(suggested) : 0,
    });

    if (!response.aiType) {
      logger.warn('Installation cancelled');
      return;
    }

    aiType = response.aiType as AIType;
  }

  logger.info(`Installing for: ${chalk.cyan(getAITypeDescription(aiType))}`);

  const spinner = ora('Generating skill files from templates...').start();
  const cwd = process.cwd();
  let copiedFolders: string[] = [];

  try {
    if (aiType === 'all') {
      copiedFolders = await generateAllPlatformFiles(cwd);
    } else {
      copiedFolders = await generatePlatformFiles(cwd, aiType);
    }

    spinner.succeed('Generated from templates!');

    // Summary
    console.log();
    logger.info('Installed folders:');
    copiedFolders.forEach(folder => {
      console.log(`  ${chalk.green('+')} ${folder}`);
    });

    console.log();
    logger.success('Taiwan Invoice Skill installed successfully!');

    // Next steps
    console.log();
    console.log(chalk.bold('Next steps:'));
    console.log(chalk.dim('  1. Restart your AI coding assistant'));
    console.log(chalk.dim('  2. Try: "Help me integrate ECPay invoice API"'));
    console.log();
  } catch (error) {
    spinner.fail('Installation failed');
    if (error instanceof Error) {
      logger.error(error.message);
    }
    process.exit(1);
  }
}
