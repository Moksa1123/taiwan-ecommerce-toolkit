import chalk from 'chalk';
import prompts from 'prompts';
import * as os from 'os';
import type { AIType } from '../types/index.js';
import { AI_TYPES } from '../types/index.js';
import { generatePlatformFiles, generateAllPlatformFiles, loadPlatformConfig } from '../utils/template.js';
import { detectAIType, getAITypeDescription } from '../utils/detect.js';
import { logger } from '../utils/logger.js';
import { InstallProgress, OFFLINE_STEPS, animatedDelay } from '../utils/progress.js';

interface InitOptions {
  ai?: AIType;
  force?: boolean;
  global?: boolean;
  offline?: boolean;
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

  // Determine target directory
  let targetDir = process.cwd();

  if (options.global && aiType !== 'all') {
    try {
      const config = await loadPlatformConfig(aiType);
      if (config.folderStructure.globalRoot) {
        // Expand ~ to home directory
        const globalRoot = config.folderStructure.globalRoot.replace(/^~/, os.homedir());
        targetDir = globalRoot;
        logger.info(`Installing globally to: ${chalk.cyan(targetDir)}`);
      } else {
        logger.warn(`Global installation not supported for ${aiType}, using project directory`);
      }
    } catch {
      logger.warn('Failed to load platform config, using project directory');
    }
  }

  logger.info(`Installing for: ${chalk.cyan(getAITypeDescription(aiType))}${options.global ? ' (global)' : ''}`);

  let copiedFolders: string[] = [];

  try {
    // Generate skill files from bundled templates
    const progress = new InstallProgress(OFFLINE_STEPS);
    progress.start();

    // Step 1: Loading templates
    await animatedDelay(300);
    progress.nextStep();

    // Step 2: Generating skill files
    if (aiType === 'all') {
      copiedFolders = await generateAllPlatformFiles(targetDir);
    } else {
      copiedFolders = await generatePlatformFiles(targetDir, aiType, options.global);
    }
    progress.nextStep();
    await animatedDelay(200);

    // Step 3-5: File installation steps
    progress.nextStep(); // references
    await animatedDelay(150);
    progress.nextStep(); // scripts
    await animatedDelay(150);
    progress.nextStep(); // data files
    await animatedDelay(150);

    progress.complete();

    // Summary
    console.log();
    logger.info('Installed folders:');
    copiedFolders.forEach(folder => {
      console.log(`  ${chalk.green('✓')} ${folder}`);
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
    logger.error('Installation failed');
    if (error instanceof Error) {
      logger.error(error.message);
    }
    process.exit(1);
  }
}
