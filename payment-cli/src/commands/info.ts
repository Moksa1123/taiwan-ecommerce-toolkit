import chalk from 'chalk';
import { logger } from '../utils/logger.js';

export function infoCommand(): void {
  logger.title('Taiwan Payment Skill');

  console.log(chalk.cyan('Description:'));
  console.log(chalk.dim('  AI-powered toolkit for Taiwan payment gateway integration'));
  console.log();

  console.log(chalk.cyan('Supported Providers:'));
  console.log(chalk.dim('  • ECPay (綠界科技) - Full support'));
  console.log(chalk.dim('  • NewebPay (藍新金流) - Planned'));
  console.log(chalk.dim('  • PAYUNi (統一金流) - Planned'));
  console.log();

  console.log(chalk.cyan('Payment Methods:'));
  console.log(chalk.dim('  • Credit Card (one-time, installment, recurring)'));
  console.log(chalk.dim('  • ATM Virtual Account'));
  console.log(chalk.dim('  • CVS Code / Barcode'));
  console.log(chalk.dim('  • Apple Pay / TWQR / BNPL'));
  console.log();

  console.log(chalk.cyan('Features:'));
  console.log(chalk.dim('  • Complete API documentation'));
  console.log(chalk.dim('  • Multi-language code examples (PHP, Python, Node.js, C#)'));
  console.log(chalk.dim('  • Error handling guides'));
  console.log(chalk.dim('  • Test connection scripts'));
  console.log();

  console.log(chalk.cyan('Links:'));
  console.log(chalk.dim('  GitHub: https://github.com/Moksa1123/taiwan-ecommerce-toolkit'));
  console.log(chalk.dim('  npm:    https://www.npmjs.com/package/taiwan-payment-skill'));
  console.log();
}
