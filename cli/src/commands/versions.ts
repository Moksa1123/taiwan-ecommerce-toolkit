import chalk from 'chalk';
import ora from 'ora';
import { logger } from '../utils/logger.js';
import { fetchReleases } from '../utils/github.js';

const VERSION = '2.0.0';

export async function versionsCommand(): Promise<void> {
  logger.title('Taiwan Invoice Skill - Available Versions');

  const spinner = ora('Fetching releases from GitHub...').start();

  try {
    const releases = await fetchReleases();
    spinner.succeed('Fetched releases from GitHub');

    console.log();
    console.log(chalk.cyan('Available Versions:'));
    console.log();

    if (releases.length === 0) {
      console.log(chalk.dim('  No releases found'));
    } else {
      for (const release of releases.slice(0, 10)) {
        const date = new Date(release.published_at).toLocaleDateString();
        const isCurrent = release.tag_name === `v${VERSION}`;
        const marker = isCurrent ? chalk.green(' (current)') : '';
        console.log(`  ${chalk.green(release.tag_name.padEnd(12))} ${date}${marker}`);
      }
    }

    console.log();
    console.log(chalk.cyan('Current CLI Version:'));
    console.log(chalk.dim(`  ${VERSION}`));
    console.log();
  } catch (error) {
    spinner.fail('Failed to fetch releases');

    console.log();
    console.log(chalk.cyan('Current CLI Version:'));
    console.log(chalk.dim(`  ${VERSION}`));
    console.log();
    console.log(chalk.dim('  Unable to fetch remote versions. Check your internet connection.'));
    console.log();
  }
}
