import chalk from 'chalk';
import prompts from 'prompts';
import * as path from 'path';
import * as os from 'os';
import type { AIType } from '../types/index.js';
import { AI_TYPES } from '../types/index.js';
import { generatePlatformFiles, generateAllPlatformFiles, loadPlatformConfig } from '../utils/template.js';
import { detectAIType, getAITypeDescription } from '../utils/detect.js';
import { logger } from '../utils/logger.js';
import { getLatestRelease, downloadRelease, getSourceZipUrl } from '../utils/github.js';
import { installFromZip, cleanup } from '../utils/extract.js';
import { InstallProgress, INSTALL_STEPS, OFFLINE_STEPS, animatedDelay } from '../utils/progress.js';

interface InitOptions {
  ai?: AIType;
  force?: boolean;
  global?: boolean;
  offline?: boolean;
}

async function tryGitHubDownload(
  aiType: Exclude<AIType, 'all'>,
  targetDir: string,
  progress: InstallProgress
): Promise<{ success: boolean; folders: string[] }> {
  try {
    // Step 1: Check for updates
    const release = await getLatestRelease();
    if (!release) {
      return { success: false, folders: [] };
    }

    progress.nextStep(`Found ${release.tag_name}`);
    await animatedDelay(200);

    // Step 2: Download
    const zipUrl = getSourceZipUrl(release);
    const tempDir = os.tmpdir();
    const zipPath = path.join(tempDir, `taiwan-invoice-${release.tag_name}.zip`);

    await downloadRelease(zipUrl, zipPath);
    progress.nextStep();
    await animatedDelay(200);

    // Step 3: Extract
    const { copiedFolders, tempDir: extractedDir } = await installFromZip(zipPath, targetDir, aiType);
    progress.nextStep();
    await animatedDelay(200);

    // Clean up
    cleanup(extractedDir, zipPath);

    if (copiedFolders.length > 0) {
      // Steps 4-7: Individual file installations
      progress.nextStep(); // skill files
      await animatedDelay(150);
      progress.nextStep(); // references
      await animatedDelay(150);
      progress.nextStep(); // scripts
      await animatedDelay(150);
      progress.nextStep(); // data files
      await animatedDelay(150);

      return { success: true, folders: copiedFolders };
    } else {
      return { success: false, folders: [] };
    }
  } catch {
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
  let usedGitHub = false;

  try {
    // Try GitHub download first (unless offline mode)
    if (!options.offline && aiType !== 'all') {
      const progress = new InstallProgress(INSTALL_STEPS);
      progress.start();

      const result = await tryGitHubDownload(aiType, targetDir, progress);
      if (result.success) {
        copiedFolders = result.folders;
        usedGitHub = true;
        progress.complete();
      } else {
        progress.fail('GitHub unavailable, switching to offline mode...');
        await animatedDelay(500);
      }
    }

    // Fall back to bundled assets
    if (!usedGitHub) {
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
    }

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
