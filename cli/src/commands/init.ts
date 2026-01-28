import chalk from 'chalk';
import ora from 'ora';
import prompts from 'prompts';
import * as path from 'path';
import * as os from 'os';
import type { AIType } from '../types/index.js';
import { AI_TYPES } from '../types/index.js';
import { generatePlatformFiles, generateAllPlatformFiles } from '../utils/template.js';
import { detectAIType, getAITypeDescription } from '../utils/detect.js';
import { logger } from '../utils/logger.js';
import { getLatestRelease, downloadRelease, getSourceZipUrl } from '../utils/github.js';
import { installFromZip, cleanup } from '../utils/extract.js';

interface InitOptions {
  ai?: AIType;
  force?: boolean;
  global?: boolean;
  offline?: boolean;
}

async function tryGitHubDownload(aiType: Exclude<AIType, 'all'>, targetDir: string): Promise<{ success: boolean; folders: string[] }> {
  const spinner = ora('Checking for latest release on GitHub...').start();

  try {
    const release = await getLatestRelease();
    if (!release) {
      spinner.info('No releases found, using bundled assets');
      return { success: false, folders: [] };
    }

    spinner.text = `Found release: ${release.tag_name}`;

    // Download source ZIP
    const zipUrl = getSourceZipUrl(release);
    const tempDir = os.tmpdir();
    const zipPath = path.join(tempDir, `taiwan-invoice-${release.tag_name}.zip`);

    spinner.text = 'Downloading release...';
    await downloadRelease(zipUrl, zipPath);

    spinner.text = 'Extracting and installing...';
    const { copiedFolders, tempDir: extractedDir } = await installFromZip(zipPath, targetDir, aiType);

    // Clean up
    cleanup(extractedDir, zipPath);

    if (copiedFolders.length > 0) {
      spinner.succeed(`Installed from GitHub release ${release.tag_name}`);
      return { success: true, folders: copiedFolders };
    } else {
      spinner.info('No matching folders in release, using bundled assets');
      return { success: false, folders: [] };
    }
  } catch (error) {
    spinner.info('GitHub download failed, using bundled assets');
    return { success: false, folders: [] };
  }
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

  const cwd = process.cwd();
  let copiedFolders: string[] = [];
  let usedGitHub = false;

  try {
    // Try GitHub download first (unless offline mode)
    if (!options.offline && aiType !== 'all') {
      const result = await tryGitHubDownload(aiType, cwd);
      if (result.success) {
        copiedFolders = result.folders;
        usedGitHub = true;
      }
    }

    // Fall back to bundled assets
    if (!usedGitHub) {
      const spinner = ora('Generating skill files from bundled templates...').start();

      if (aiType === 'all') {
        copiedFolders = await generateAllPlatformFiles(cwd);
      } else {
        copiedFolders = await generatePlatformFiles(cwd, aiType);
      }

      spinner.succeed('Generated from bundled templates!');
    }

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
    logger.error('Installation failed');
    if (error instanceof Error) {
      logger.error(error.message);
    }
    process.exit(1);
  }
}
