import { readFile, mkdir, writeFile, cp, access } from 'node:fs/promises';
import { join } from 'node:path';
import type { PlatformConfig } from '../types/index.js';

// Get the assets directory - uses __dirname which is available in CJS bundle
function getAssetsDir(): string {
  // When bundled to CJS, __dirname points to dist/
  // Assets are at ../assets relative to dist/
  return join(__dirname, '..', 'assets');
}

const AI_TO_PLATFORM: Record<string, string> = {
  claude: 'claude',
  cursor: 'cursor',
  windsurf: 'windsurf',
  antigravity: 'agent',
  copilot: 'copilot',
  kiro: 'kiro',
  codex: 'codex',
  qoder: 'qoder',
  roocode: 'roocode',
  gemini: 'gemini',
  trae: 'trae',
  opencode: 'opencode',
  continue: 'continue',
  codebuddy: 'codebuddy',
};

async function exists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

export async function loadPlatformConfig(aiType: string): Promise<PlatformConfig> {
  const platformName = AI_TO_PLATFORM[aiType];
  if (!platformName) {
    throw new Error(`Unknown AI type: ${aiType}`);
  }

  const configPath = join(getAssetsDir(), 'templates', 'platforms', `${platformName}.json`);
  const content = await readFile(configPath, 'utf-8');
  return JSON.parse(content) as PlatformConfig;
}

async function loadTemplate(templateName: string): Promise<string> {
  const templatePath = join(getAssetsDir(), 'templates', templateName);
  return readFile(templatePath, 'utf-8');
}

function renderFrontmatter(frontmatter: Record<string, string> | null): string {
  if (!frontmatter) return '';

  const lines = ['---'];
  for (const [key, value] of Object.entries(frontmatter)) {
    if (value.includes(':') || value.includes('"') || value.includes('\n')) {
      lines.push(`${key}: "${value.replace(/"/g, '\\"')}"`);
    } else {
      lines.push(`${key}: ${value}`);
    }
  }
  lines.push('---', '');
  return lines.join('\n');
}

export async function renderSkillFile(config: PlatformConfig): Promise<string> {
  let content = await loadTemplate('base/skill-content.md');

  const frontmatter = renderFrontmatter(config.frontmatter);

  content = content
    .replace(/\{\{TITLE\}\}/g, config.title)
    .replace(/\{\{DESCRIPTION\}\}/g, config.description);

  // Include quick reference section for Claude (or other platforms that support it)
  if (config.sections.quickReference) {
    try {
      const quickRef = await loadTemplate('base/quick-reference.md');
      // Insert quick reference before the main content
      content = quickRef + '\n' + content;
    } catch {
      // Skip if quick-reference.md doesn't exist
    }
  }

  return frontmatter + content;
}

async function copyTaiwanInvoiceAssets(targetSkillDir: string, sections: PlatformConfig['sections']): Promise<void> {
  const sourceDir = join(getAssetsDir(), 'taiwan-invoice');

  // Copy EXAMPLES.md if enabled
  if (sections.examples && await exists(join(sourceDir, 'EXAMPLES.md'))) {
    await cp(join(sourceDir, 'EXAMPLES.md'), join(targetSkillDir, 'EXAMPLES.md'));
  }

  // Copy references if enabled
  if (sections.references && await exists(join(sourceDir, 'references'))) {
    const refsTarget = join(targetSkillDir, 'references');
    await mkdir(refsTarget, { recursive: true });
    await cp(join(sourceDir, 'references'), refsTarget, { recursive: true });
  }

  // Copy scripts if enabled
  if (sections.scripts && await exists(join(sourceDir, 'scripts'))) {
    const scriptsTarget = join(targetSkillDir, 'scripts');
    await mkdir(scriptsTarget, { recursive: true });
    await cp(join(sourceDir, 'scripts'), scriptsTarget, { recursive: true });
  }

  // Copy data if enabled (CSV data files for search engine)
  if (sections.scripts && await exists(join(sourceDir, 'data'))) {
    const dataTarget = join(targetSkillDir, 'data');
    await mkdir(dataTarget, { recursive: true });
    await cp(join(sourceDir, 'data'), dataTarget, { recursive: true });
  }
}

export async function renderWorkflowFile(config: PlatformConfig): Promise<string> {
  const frontmatter = renderFrontmatter(config.frontmatter);
  const sharedPath = config.folderStructure.sharedPath || 'taiwan-invoice';

  const content = `# ${config.title}

${config.description}

## Prerequisites

Check if Python is installed:

\`\`\`bash
python3 --version || python --version
\`\`\`

---

## How to Use This Workflow

When user requests Taiwan E-Invoice work (issue, void, allowance, print, query), follow this workflow:

### Step 1: Analyze User Requirements

Extract key information:
- **Provider**: ECPay, SmilePay, or Amego
- **Invoice type**: B2C (二聯式) or B2B (三聯式)
- **Operation**: issue, void, allowance, print, query

### Step 2: Recommend Provider (Optional)

\`\`\`bash
python3 .shared/${sharedPath}/scripts/recommend.py "<keywords>"
\`\`\`

Example:
\`\`\`bash
python3 .shared/${sharedPath}/scripts/recommend.py "電商 高交易量 穩定"
\`\`\`

### Step 3: Search for Information

\`\`\`bash
python3 .shared/${sharedPath}/scripts/search.py "<keyword>" --domain <domain>
\`\`\`

Available domains:
| Domain | Description |
|--------|-------------|
| provider | Provider comparison |
| operation | API endpoints |
| error | Error codes |
| field | Field mappings |
| tax | Tax rules |
| troubleshoot | Troubleshooting |

### Step 4: Generate Service Code

\`\`\`bash
python3 .shared/${sharedPath}/scripts/generate-invoice-service.py <Provider> --output ts
\`\`\`

### Step 5: Initialize Project Config (Optional)

\`\`\`bash
python3 .shared/${sharedPath}/scripts/persist.py init <Provider>
\`\`\`

---

## Quick Reference

### B2C Invoice (二聯式)
- Amount: **Tax-inclusive**
- BuyerIdentifier: \`0000000000\`
- TaxAmount: \`0\`
- Can use carrier/donation

### B2B Invoice (三聯式)
- Amount: **Tax-exclusive**
- Must fill 8-digit tax ID
- Calculate tax: \`TaxAmount = round(Total - Total/1.05)\`
- **Cannot** use carrier/donation

---

## Test Credentials

### ECPay
\`\`\`
MerchantID: 2000132
HashKey: ejCk326UnaZWKisg
HashIV: q9jcZX8Ib9LM8wYk
\`\`\`

### SmilePay
\`\`\`
Grvc: SEI1000034
Verify_key: 9D73935693EE0237FABA6AB744E48661
\`\`\`

### Amego
\`\`\`
Invoice: 12345678
App Key: sHeq7t8G1wiQvhAuIM27
\`\`\`

---

*Generated by Taiwan Invoice Skill*
`;

  return frontmatter + content;
}

export async function generatePlatformFiles(
  targetDir: string,
  aiType: string
): Promise<string[]> {
  const config = await loadPlatformConfig(aiType);
  const createdFolders: string[] = [];

  // Handle workflow type (e.g., Antigravity)
  if (config.installType === 'workflow') {
    // Create workflow file in .agent/workflows/
    const workflowDir = join(
      targetDir,
      config.folderStructure.root,
      config.folderStructure.skillPath
    );
    await mkdir(workflowDir, { recursive: true });

    const workflowContent = await renderWorkflowFile(config);
    const workflowFilePath = join(workflowDir, config.folderStructure.filename);
    await writeFile(workflowFilePath, workflowContent, 'utf-8');
    createdFolders.push(config.folderStructure.root);

    // Copy assets to .shared/taiwan-invoice/
    if (config.folderStructure.sharedRoot && config.folderStructure.sharedPath) {
      const sharedDir = join(
        targetDir,
        config.folderStructure.sharedRoot,
        config.folderStructure.sharedPath
      );
      await mkdir(sharedDir, { recursive: true });
      await copyTaiwanInvoiceAssets(sharedDir, config.sections);
      createdFolders.push(config.folderStructure.sharedRoot);
    }

    return createdFolders;
  }

  // Standard skill installation
  const skillDir = join(
    targetDir,
    config.folderStructure.root,
    config.folderStructure.skillPath
  );

  await mkdir(skillDir, { recursive: true });

  const skillContent = await renderSkillFile(config);
  const skillFilePath = join(skillDir, config.folderStructure.filename);
  await writeFile(skillFilePath, skillContent, 'utf-8');
  createdFolders.push(config.folderStructure.root);

  // Copy additional assets
  await copyTaiwanInvoiceAssets(skillDir, config.sections);

  return createdFolders;
}

export async function generateAllPlatformFiles(targetDir: string): Promise<string[]> {
  const allFolders = new Set<string>();

  for (const aiType of Object.keys(AI_TO_PLATFORM)) {
    try {
      const folders = await generatePlatformFiles(targetDir, aiType);
      folders.forEach(f => allFolders.add(f));
    } catch {
      // Skip if generation fails
    }
  }

  return Array.from(allFolders);
}

export function getSupportedAITypes(): string[] {
  return Object.keys(AI_TO_PLATFORM);
}
