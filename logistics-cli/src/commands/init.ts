import chalk from 'chalk';
import prompts from 'prompts';
import * as os from 'os';
import type { AIType } from '../types/index.js';
import { AI_TYPES } from '../types/index.js';
import { generatePlatformFiles, generateAllPlatformFiles, loadPlatformConfig } from '../utils/template.js';
import { detectAIType, getAITypeDescription } from '../utils/detect.js';
import { logger } from '../utils/logger.js';
import { InstallProgress, INSTALL_STEPS, animatedDelay } from '../utils/progress.js';

interface InitOptions {
  ai?: AIType;
  force?: boolean;
  global?: boolean;
}

export async function initCommand(options: InitOptions): Promise<void> {
  logger.title('Taiwan Logistics Skill Installer');

  let aiType = options.ai;

  // Auto-detect or prompt for AI type
  if (!aiType) {
    const { detected, suggested } = detectAIType();

    if (detected.length > 0) {
      logger.info(`Detected: ${detected.map(t => chalk.cyan(t)).join(', ')}`);
    }

    const response = await prompts([
      {
        type: 'select',
        name: 'aiType',
        message: '你想裝在哪個 AI 助手？',
        choices: AI_TYPES.map(type => ({
          title: getAITypeDescription(type),
          value: type,
        })),
        initial: suggested ? AI_TYPES.indexOf(suggested) : 0,
      },
      {
        type: (prev) => prev !== 'all' && prev !== 'windsurf' ? 'toggle' : null,
        name: 'global',
        message: '要全域安裝嗎？（所有專案都能用）',
        initial: false,
        active: '要',
        inactive: '不要',
      },
      {
        type: 'toggle',
        name: 'force',
        message: '檔案如果已經存在要覆蓋嗎？',
        initial: false,
        active: '要',
        inactive: '不要',
      },
    ]);

    if (!response.aiType) {
      logger.warn('Installation cancelled');
      return;
    }

    aiType = response.aiType as AIType;

    // Override options with interactive responses if not already set
    if (options.global === undefined && response.global !== undefined) {
      options.global = response.global;
    }
    if (options.force === undefined && response.force !== undefined) {
      options.force = response.force;
    }
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
    const progress = new InstallProgress(INSTALL_STEPS);
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
      console.log(`  ${chalk.green('●')} ${folder}`);
    });

    console.log();

    // Success box
    logger.box(
      `台灣物流技能包安裝成功！\n\n` +
      `已安裝到: ${chalk.cyan(copiedFolders[0])}\n\n` +
      `下一步：\n` +
      ` 1. 重新啟動你的 AI 助手\n` +
      ` 2. 試試看：「幫我整合綠界物流 API」`
    );

    console.log();

    // Interactive tutorial
    const tutorialResponse = await prompts({
      type: 'toggle',
      name: 'showTutorial',
      message: '要看快速上手指南嗎？',
      initial: true,
      active: '要',
      inactive: '不用',
    });

    if (tutorialResponse.showTutorial) {
      console.log();
      console.log(chalk.bold.cyan('快速上手指南'));
      console.log();
      console.log(chalk.yellow('支援的物流平台：'));
      console.log(chalk.dim('  • 綠界物流 (ECPay)'));
      console.log(chalk.dim('  • 藍新物流 (NewebPay)'));
      console.log(chalk.dim('  • 統一物流 (PAYUNi)'));
      console.log();
      console.log(chalk.yellow('常見使用範例：'));
      console.log(chalk.dim('  1. 「幫我整合綠界超商取貨 API」'));
      console.log(chalk.dim('  2. 「我要實作物流訂單查詢功能」'));
      console.log(chalk.dim('  3. 「產生物流 B2C 寄件單」'));
      console.log();
      console.log(chalk.yellow('技能包內容：'));
      console.log(chalk.dim('  • API 文件參考 (references/)'));
      console.log(chalk.dim('  • 程式碼範例 (EXAMPLES.md)'));
      console.log(chalk.dim('  • 測試工具 (scripts/)'));
      console.log();
      console.log(chalk.green('提示：重啟 AI 助手後，直接用中文描述你要做什麼就可以了！'));
      console.log();
    }

    console.log();
  } catch (error) {
    logger.error('Installation failed');
    if (error instanceof Error) {
      logger.error(error.message);
    }
    process.exit(1);
  }
}
