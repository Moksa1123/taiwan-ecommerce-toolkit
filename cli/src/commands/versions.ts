import chalk from 'chalk';
import ora from 'ora';
import { logger } from '../utils/logger.js';

const VERSION = '2.5.4';

export async function versionsCommand(): Promise<void> {
  logger.title('Taiwan Invoice Skill - Available Versions');

  const spinner = ora('Fetching versions from npm...').start();

  try {
    const response = await fetch('https://registry.npmjs.org/taiwan-invoice-skill', {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`npm registry error: ${response.status}`);
    }

    const data = await response.json();
    const versions = Object.keys(data.versions || {}).reverse().slice(0, 10);

    spinner.succeed('Fetched versions from npm');

    console.log();
    console.log(chalk.cyan('Available Versions:'));
    console.log();

    if (versions.length === 0) {
      console.log(chalk.dim('  No versions found'));
    } else {
      for (const version of versions) {
        const isCurrent = version === VERSION;
        const marker = isCurrent ? chalk.green(' (current)') : '';
        console.log(`  ${chalk.green(version.padEnd(12))}${marker}`);
      }
    }

    console.log();
  } catch (error) {
    spinner.fail('Failed to fetch versions');

    console.log();
    console.log(chalk.cyan('Current CLI Version:'));
    console.log(chalk.dim(`  ${VERSION}`));
    console.log();
    console.log(chalk.dim('  Unable to fetch remote versions. Check your internet connection.'));
    console.log();
  }
}
