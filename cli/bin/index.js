#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');

const VERSION = '2.0.0';
const SKILL_NAME = 'taiwan-invoice';

// ANSI colors
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  dim: '\x1b[2m'
};

function log(msg, color = '') {
  console.log(color ? `${color}${msg}${colors.reset}` : msg);
}

function success(msg) { log(`[OK] ${msg}`, colors.green); }
function warn(msg) { log(`[WARNING] ${msg}`, colors.yellow); }
function error(msg) { log(`[ERROR] ${msg}`, colors.red); }
function info(msg) { log(msg, colors.cyan); }

// Platform configurations
const platforms = {
  claude: {
    name: 'Claude Code',
    projectPath: '.claude/skills',
    globalPath: path.join(os.homedir(), '.claude', 'skills')
  },
  cursor: {
    name: 'Cursor',
    projectPath: '.cursor/skills',
    globalPath: path.join(os.homedir(), '.cursor', 'skills')
  },
  antigravity: {
    name: 'Google Antigravity',
    projectPath: '.agent/skills',
    globalPath: path.join(os.homedir(), '.gemini', 'antigravity', 'global_skills')
  }
};

function showHelp() {
  console.log(`
${colors.cyan}Taiwan Invoice Skill CLI v${VERSION}${colors.reset}

${colors.dim}An AI skill for Taiwan E-Invoice API integration${colors.reset}

Usage:
  taiwan-invoice init --ai <platform>   Install skill for specified platform
  taiwan-invoice init --ai all          Install for all platforms
  taiwan-invoice --version              Show version
  taiwan-invoice --help                 Show this help

Platforms:
  claude        Claude Code (.claude/skills/)
  cursor        Cursor (.cursor/skills/)
  antigravity   Google Antigravity (.agent/skills/)
  all           All platforms

Options:
  --global      Install to global directory instead of current project

Examples:
  taiwan-invoice init --ai claude
  taiwan-invoice init --ai cursor --global
  taiwan-invoice init --ai all
`);
}

function showVersion() {
  console.log(`taiwan-invoice-skill v${VERSION}`);
}

function copyRecursive(src, dest) {
  if (!fs.existsSync(src)) {
    return false;
  }

  const stat = fs.statSync(src);

  if (stat.isDirectory()) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }

    const files = fs.readdirSync(src);
    for (const file of files) {
      copyRecursive(path.join(src, file), path.join(dest, file));
    }
  } else {
    fs.copyFileSync(src, dest);
  }

  return true;
}

function installSkill(platform, useGlobal = false) {
  const config = platforms[platform];
  if (!config) {
    error(`Unknown platform: ${platform}`);
    return false;
  }

  const targetBase = useGlobal ? config.globalPath : path.join(process.cwd(), config.projectPath);
  const targetPath = path.join(targetBase, SKILL_NAME);

  // Find assets directory
  const assetsPath = path.join(__dirname, '..', 'assets', SKILL_NAME);

  if (!fs.existsSync(assetsPath)) {
    error(`Assets not found at: ${assetsPath}`);
    error('Please reinstall the package: npm install -g taiwan-invoice-skill');
    return false;
  }

  // Create target directory
  if (!fs.existsSync(targetBase)) {
    fs.mkdirSync(targetBase, { recursive: true });
  }

  // Remove existing installation
  if (fs.existsSync(targetPath)) {
    warn(`${config.name} target directory exists, overwriting...`);
    fs.rmSync(targetPath, { recursive: true, force: true });
  }

  // Copy files
  if (copyRecursive(assetsPath, targetPath)) {
    success(`${config.name} installed to ${targetPath}`);
    return true;
  } else {
    error(`Failed to install ${config.name}`);
    return false;
  }
}

function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    showHelp();
    return;
  }

  if (args.includes('--version') || args.includes('-v')) {
    showVersion();
    return;
  }

  // Parse arguments
  const command = args[0];
  const aiIndex = args.indexOf('--ai');
  const useGlobal = args.includes('--global');

  if (command !== 'init') {
    error(`Unknown command: ${command}`);
    showHelp();
    process.exit(1);
  }

  if (aiIndex === -1 || !args[aiIndex + 1]) {
    error('Missing --ai argument');
    console.log('Usage: taiwan-invoice init --ai <platform>');
    process.exit(1);
  }

  const platform = args[aiIndex + 1].toLowerCase();

  console.log(`
${colors.cyan}Taiwan Invoice Skill Installer${colors.reset}
${'='.repeat(40)}
`);

  let success_count = 0;

  if (platform === 'all') {
    for (const p of Object.keys(platforms)) {
      if (installSkill(p, useGlobal)) success_count++;
    }
  } else {
    if (installSkill(platform, useGlobal)) success_count++;
  }

  console.log(`
${'='.repeat(40)}
${colors.green}[DONE] Installation complete!${colors.reset}

Quick Start:
  Claude Code / Cursor: Type /taiwan-invoice or mention e-invoice topics
  Antigravity: Mention e-invoice topics (auto-activates)

Documentation:
  https://github.com/Moksa1123/taiwan-invoice
`);
}

main();
