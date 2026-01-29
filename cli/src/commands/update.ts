import chalk from 'chalk';
import ora from 'ora';
import { logger } from '../utils/logger.js';

const VERSION = '2.5.4';

export async function updateCommand(): Promise<void> {
  logger.title('Taiwan Invoice Skill - Update');

  console.log(chalk.cyan('Current Version:'));
  console.log(chalk.dim(`  ${VERSION}`));
  console.log();

  const spinner = ora('Checking for updates...').start();

  try {
    const response = await fetch('https://registry.npmjs.org/taiwan-invoice-skill/latest', {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`npm registry error: ${response.status}`);
    }

    const data = await response.json();
    const latestVersion = data.version;

    if (latestVersion === VERSION) {
      spinner.succeed('You are already on the latest version!');
    } else {
      spinner.info(`New version available: ${latestVersion}`);
      console.log();
      console.log(chalk.cyan('To update, run:'));
      console.log(chalk.dim('  npm install -g taiwan-invoice-skill@latest'));
    }
  } catch (error) {
    spinner.warn('Unable to check for updates');
    console.log();
    console.log(chalk.cyan('To update manually, run:'));
    console.log(chalk.dim('  npm install -g taiwan-invoice-skill@latest'));
  }

  console.log();
}
