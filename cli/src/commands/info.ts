import chalk from 'chalk';
import { logger } from '../utils/logger.js';

const VERSION = '2.0.0';

export async function infoCommand(): Promise<void> {
  logger.title('Taiwan Invoice Skill');

  console.log(chalk.cyan('Skill Information:'));
  console.log();
  console.log(`  ${chalk.dim('Name:')}        taiwan-invoice`);
  console.log(`  ${chalk.dim('Version:')}     ${VERSION}`);
  console.log(`  ${chalk.dim('Providers:')}   ECPay, SmilePay, Amego`);
  console.log(`  ${chalk.dim('Features:')}    Issue, Void, Allowance, Query, Print`);
  console.log(`  ${chalk.dim('Platforms:')}   Claude Code, Cursor, Antigravity`);
  console.log(`  ${chalk.dim('License:')}     MIT`);
  console.log();
  console.log(chalk.cyan('Links:'));
  console.log(`  ${chalk.dim('GitHub:')}      https://github.com/Moksa1123/taiwan-invoice`);
  console.log(`  ${chalk.dim('npm:')}         https://www.npmjs.com/package/taiwan-invoice-skill`);
  console.log(`  ${chalk.dim('Support:')}     https://paypal.me/cccsubcom`);
  console.log();
}
