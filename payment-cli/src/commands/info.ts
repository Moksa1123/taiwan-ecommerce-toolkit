import chalk from 'chalk';
import { logger } from '../utils/logger.js';
import { VERSION } from '../version.js';

export async function infoCommand(): Promise<void> {
  logger.title('Taiwan Payment Skill');

  console.log(chalk.cyan('Skill Information:'));
  console.log();
  console.log(`  ${chalk.dim('Name:')}        taiwan-payment`);
  console.log(`  ${chalk.dim('Version:')}     ${VERSION}`);
  console.log(`  ${chalk.dim('Providers:')}   ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, ezPay, PayNow, Shopline, LINE Pay, TapPay, O'Pay, JKOPAY, SunPay, GoMyPay`);
  console.log(`  ${chalk.dim('Features:')}    Checkout, Callback verification, Query, Refund, Recurring`);
  console.log(`  ${chalk.dim('Platforms:')}   14 AI assistants (Claude, Cursor, Windsurf, Copilot, etc.)`);
  console.log(`  ${chalk.dim('License:')}     MIT`);
  console.log();
  console.log(chalk.cyan('Links:'));
  console.log(`  ${chalk.dim('GitHub:')}      https://github.com/Moksa1123/taiwan-ecommerce-toolkit`);
  console.log(`  ${chalk.dim('npm:')}         https://www.npmjs.com/package/taiwan-payment-skill`);
  console.log(`  ${chalk.dim('Support:')}     https://paypal.me/cccsubcom`);
  console.log();
}
