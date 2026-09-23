# Taiwan Invoice Skill - CLI Architecture

## Directory Structure

```
claude-skills/
├── invoice-cli/                # Taiwan Invoice Skill CLI (npm: taiwan-invoice-skill)
├── payment-cli/                # Taiwan Payment Skill CLI (npm: taiwan-payment-skill)
├── logistics-cli/              # Taiwan Logistics Skill CLI (npm: taiwan-logistics-skill)
├── taiwan-invoice/             # Invoice skill core content (Source of Truth)
├── taiwan-payment/             # Payment skill core content (Source of Truth)
└── taiwan-logistics/           # Logistics skill core content (Source of Truth)
```

## Invoice CLI Structure

```
invoice-cli/
├── src/                        # TypeScript source code
│   ├── index.ts                # Main CLI entry point
│   ├── commands/               # CLI commands
│   │   ├── init.ts             # Installation command
│   │   ├── list.ts             # List AI platforms
│   │   ├── info.ts             # Show skill info
│   │   ├── versions.ts         # List available versions
│   │   └── update.ts           # Check for updates
│   ├── utils/                  # Utility functions
│   │   ├── template.ts         # Template rendering engine
│   │   ├── logger.ts           # Logging utilities
│   │   ├── detect.ts           # AI platform detection
│   │   └── github.ts           # GitHub release utilities
│   └── types/                  # TypeScript type definitions
│       └── index.ts
├── assets/                     # Bundled assets
│   ├── taiwan-invoice/         # Core skill content (synced from ../taiwan-invoice/)
│   │   ├── SKILL.md            # 1100+ lines
│   │   ├── EXAMPLES.md         # 1500+ lines
│   │   ├── references/         # API documentation
│   │   ├── scripts/            # Python intelligent tools
│   │   └── data/               # CSV data files
│   └── templates/
│       ├── base/
│       │   ├── skill-content.md
│       │   └── quick-reference.md
│       └── platforms/          # 14 platform configurations
│           ├── claude.json
│           ├── cursor.json
│           ├── windsurf.json
│           └── ... (11 more)
├── scripts/                    # Build scripts
│   └── build.js                # esbuild configuration
├── dist/                       # Compiled output
│   └── index.js                # Single bundled file
├── .gitignore                  # Git ignore patterns
├── .npmignore                  # NPM ignore patterns
├── package.json                # NPM package configuration
├── package-lock.json           # Locked dependencies
├── tsconfig.json               # TypeScript configuration
└── README.md                   # CLI documentation

```

## Three NPM Packages

1. **taiwan-invoice-skill** (invoice-cli/)
   - E-Invoice integration for ECPay, SmilePay, Amego, ezPay, PayNow, O'Pay, SunPay
   - Install: `npm install -g taiwan-invoice-skill`
   - Usage: `taiwan-invoice init --ai claude`

2. **taiwan-payment-skill** (payment-cli/)
   - Payment gateway integration for 14 providers (see taiwan-payment/README.md)
   - Install: `npm install -g taiwan-payment-skill`
   - Usage: `taiwan-payment init --ai claude`

3. **taiwan-logistics-skill** (logistics-cli/)
   - Logistics integration for 7 aggregators, HCT direct and on-demand delivery
   - Install: `npm install -g taiwan-logistics-skill`
   - Usage: `taiwan-logistics init --ai claude`

## Sync Workflow

### Source of Truth: `taiwan-invoice/`

Before publishing to NPM:

```bash
# 1. Update core content in taiwan-invoice/
# Edit: SKILL.md, EXAMPLES.md, references/, scripts/, data/

# 2. Sync to CLI assets
cp -r taiwan-invoice/* invoice-cli/assets/taiwan-invoice/

# 3. Update version
cd invoice-cli
# Edit package.json version

# 4. Build
npm run build

# 5. Test
npm test

# 6. Publish
npm publish
```

## Supported AI Platforms (14)

| Platform | Folder | Global Path |
|----------|--------|-------------|
| Claude Code | `.claude` | `~/.claude` |
| Cursor | `.cursor` | `~/.cursor` |
| Windsurf | `.windsurf` | - |
| Antigravity | `.agent` | `~/.gemini/antigravity` |
| GitHub Copilot | `.github` | - |
| Kiro | `.kiro` | `~/.kiro` |
| Codex | `.codex` | `~/.codex` |
| Qoder | `.qoder` | `~/.qoder` |
| Cline | `.cline` | `~/.cline` |
| Gemini | `.gemini` | `~/.gemini` |
| Trae | `.trae` | `~/.trae` |
| OpenCode | `.opencode` | `~/.opencode` |
| Continue | `.continue` | `~/.continue` |
| CodeBuddy | `.codebuddy` | `~/.codebuddy` |

## Key Files

- **package.json**: NPM package configuration, dependencies, bin entry
- **src/index.ts**: CLI entry point with Commander.js
- **src/commands/init.ts**: Installation logic with template rendering
- **src/utils/template.ts**: Template engine with variable substitution
- **assets/templates/base/skill-content.md**: Base skill template
- **scripts/build.js**: esbuild configuration for single-file output

## Build Process

Uses esbuild for fast bundling:

```bash
npm run build
# Compiles TypeScript to single dist/index.js
# Bundles all dependencies except chalk, ora, prompts, cli-progress
# Adds shebang #!/usr/bin/env node
# Makes executable with chmod +x
```

## Dependencies

### Runtime (included in bundle)
- commander: CLI framework
- chalk: Terminal colors
- ora: Loading spinners
- prompts: Interactive prompts
- cli-progress: Progress bars

### Dev Dependencies
- typescript: Type checking
- esbuild: Fast bundler
- @types/node: Node.js type definitions

## Installation Flow

1. User runs: `taiwan-invoice init --ai claude`
2. CLI detects platform (or uses specified)
3. Determines install path (`.claude/skills/taiwan-invoice/` or `~/.claude/skills/taiwan-invoice/`)
4. Copies assets from `assets/taiwan-invoice/`
5. Renders templates with platform-specific variables
6. Creates directory structure
7. Displays success message with activation instructions

## Template Variables

Templates use Mustache-style syntax:

- `{{TITLE}}`: Platform display name
- `{{DESCRIPTION}}`: Skill description
- `{{SKILL_NAME}}`: Internal skill name
- `{{VERSION}}`: Skill version

Example:
```markdown
# {{TITLE}}

{{DESCRIPTION}}

Version: {{VERSION}}
```

---

**Last Updated**: 2026-01-29
