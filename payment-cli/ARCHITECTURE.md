# Taiwan Payment Skill - CLI Architecture

## Directory Structure

```
claude-skills/
├── cli/                        # Taiwan Payment Skill CLI (npm: taiwan-payment-skill)
├── payment-cli/                # Taiwan Payment Skill CLI (npm: taiwan-payment-skill)
├── taiwan-payment/             # Invoice skill core content (Source of Truth)
├── taiwan-payment/             # Payment skill core content (Source of Truth)
└── taiwan-logistics/           # Logistics skill core content (Source of Truth)
```

## Payment CLI Structure

```
payment-cli/
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
│   ├── taiwan-payment/         # Core skill content (synced from ../taiwan-payment/)
│   │   ├── SKILL.md            # 857 lines
│   │   ├── EXAMPLES.md         # 1425 lines
│   │   ├── references/         # API documentation
│   │   ├── scripts/            # Python intelligent tools
│   │   └── data/               # 7 CSV data files
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
│   └── index.js                # Single bundled file (556KB)
├── package.json                # NPM package configuration
├── tsconfig.json               # TypeScript configuration
└── README.md                   # CLI documentation

```

## Three NPM Packages

1. **taiwan-payment-skill** (cli/)
   - E-Invoice integration for ECPay, SmilePay, Amego
   - Install: `npm install -g taiwan-payment-skill`
   - Usage: `taiwan-payment init --ai claude`

2. **taiwan-payment-skill** (payment-cli/)
   - Payment gateway integration for ECPay, NewebPay, PAYUNi
   - Install: `npm install -g taiwan-payment-skill`
   - Usage: `taiwan-payment init --ai claude`

3. **taiwan-logistics-skill** (future)
   - Logistics integration for major Taiwan carriers
   - Install: `npm install -g taiwan-logistics-skill`
   - Usage: `taiwan-logistics init --ai claude`

## Sync Workflow

### Source of Truth: `taiwan-payment/`

Before publishing to NPM:

```bash
# 1. Update core content in taiwan-payment/
# Edit: SKILL.md, EXAMPLES.md, references/, scripts/, data/

# 2. Sync to CLI assets
cp -r taiwan-payment/* payment-cli/assets/taiwan-payment/

# 3. Update version
cd payment-cli
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
| Roo Code | `.roo` | `~/.roo` |
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
# Compiles TypeScript to single dist/index.js (556KB)
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

1. User runs: `taiwan-payment init --ai claude`
2. CLI detects platform (or uses specified)
3. Determines install path (`.claude/skills/taiwan-payment/` or `~/.claude/skills/taiwan-payment/`)
4. Copies assets from `assets/taiwan-payment/`
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
