import { Command } from 'commander';
import { readFileSync } from 'fs';
import { join } from 'path';
import { initCommand } from './commands/init.js';
import { listCommand } from './commands/list.js';
import { infoCommand } from './commands/info.js';
import type { AIType } from './types/index.js';
import { AI_TYPES } from './types/index.js';

const VERSION = '2.0.0';

const program = new Command();

program
  .name('taiwan-invoice')
  .description('CLI to install Taiwan E-Invoice skill for AI coding assistants')
  .version(VERSION);

program
  .command('init')
  .description('Install Taiwan Invoice skill to current project')
  .option('-a, --ai <type>', `AI assistant type (${AI_TYPES.join(', ')})`)
  .option('-f, --force', 'Overwrite existing files')
  .option('-g, --global', 'Install to global directory')
  .action(async (options) => {
    if (options.ai && !AI_TYPES.includes(options.ai)) {
      console.error(`Invalid AI type: ${options.ai}`);
      console.error(`Valid types: ${AI_TYPES.join(', ')}`);
      process.exit(1);
    }
    await initCommand({
      ai: options.ai as AIType | undefined,
      force: options.force,
      global: options.global,
    });
  });

program
  .command('list')
  .description('List supported AI platforms')
  .action(listCommand);

program
  .command('info')
  .description('Show skill information')
  .action(infoCommand);

program.parse();
