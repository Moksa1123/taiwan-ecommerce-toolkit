# Taiwan Logistics Skill - CLI Architecture

## Directory Structure

```
claude-skills/
├── invoice-cli/                # Taiwan Logistics Skill CLI (npm: taiwan-logistics-skill)
├── payment-cli/                # Taiwan Payment Skill CLI (npm: taiwan-payment-skill)
├── logistics-cli/              # Taiwan Logistics Skill CLI (npm: taiwan-logistics-skill)
├── taiwan-logistics/             # Invoice skill core content (Source of Truth)
├── taiwan-payment/             # Payment skill core content (Source of Truth)
└── taiwan-logistics/           # Logistics skill core content (Source of Truth)
```

## Logistics CLI Structure

```
logistics-cli/
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
│   ├── taiwan-logistics/       # Core skill content (synced from ../taiwan-logistics/)
│   │   ├── SKILL.md            # 2300+ lines
│   │   ├── EXAMPLES.md         # 3100+ lines
│   │   ├── references/         # API documentation
│   │   ├── scripts/            # Python intelligent tools
│   │   ├── examples/           # Production-ready Python examples
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
├── package-lock.json           # Locked dependencies (will be generated)
├── tsconfig.json               # TypeScript configuration
└── README.md                   # CLI documentation

```

## Three NPM Packages

1. **taiwan-logistics-skill** (invoice-cli/)
   - E-Invoice integration for ECPay, SmilePay, Amego
   - Install: `npm install -g taiwan-logistics-skill`
   - Usage: `taiwan-logistics init --ai claude`

2. **taiwan-payment-skill** (payment-cli/)
   - Payment gateway integration for ECPay, NewebPay, PAYUNi
   - Install: `npm install -g taiwan-payment-skill`
   - Usage: `taiwan-payment init --ai claude`

3. **taiwan-logistics-skill** (logistics-cli/)
   - Logistics integration for ECPay, NewebPay, PAYUNi
   - Install: `npm install -g taiwan-logistics-skill`
   - Usage: `taiwan-logistics init --ai claude`

## Sync Workflow

### Source of Truth: `taiwan-logistics/`

Before publishing to NPM:

```bash
# 1. Update core content in taiwan-logistics/
# Edit: SKILL.md, EXAMPLES.md, references/, scripts/, examples/, data/

# 2. Sync to CLI assets
cp -r taiwan-logistics/* logistics-cli/assets/taiwan-logistics/

# 3. Update version
cd logistics-cli
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
- @types/cli-progress: Type definitions for cli-progress
- @types/prompts: Type definitions for prompts

## Installation Flow

1. User runs: `taiwan-logistics init --ai claude`
2. CLI detects platform (or uses specified)
3. Determines install path (`.claude/skills/taiwan-logistics/` or `~/.claude/skills/taiwan-logistics/`)
4. Copies assets from `assets/taiwan-logistics/`
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

## Production-Ready Python Examples

The logistics skill includes high-quality Python examples following strict coding standards:

- **ECPay CVS**: Complete C2C logistics with store map
- **NewebPay CVS**: newebpay-logistics-cvs-example.py
- **PAYUNi CVS**: payuni-logistics-cvs-example.py

All examples include:
- Dataclass structures with type hints
- Complete docstrings with Args/Returns/Raises/Example
- Comprehensive error handling
- Professional usage examples
- Test credentials

---

**Last Updated**: 2026-01-29
