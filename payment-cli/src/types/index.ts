export const AI_TYPES = [
  'claude',
  'cursor',
  'windsurf',
  'antigravity',
  'copilot',
  'kiro',
  'codex',
  'qoder',
  'cline',
  'gemini',
  'trae',
  'opencode',
  'continue',
  'codebuddy',
  'all',
] as const;

export type AIType = (typeof AI_TYPES)[number];

export type InstallType = 'full' | 'reference' | 'workflow';

export interface PlatformConfig {
  name: string;
  title: string;
  description: string;
  folderStructure: {
    root: string;
    skillPath: string;
    filename: string;
    sharedPath?: string;
    globalRoot?: string;
  };
  frontmatter: Record<string, string> | null;
  sections: {
    quickReference: boolean;
    examples: boolean;
    references: boolean;
    scripts: boolean;
    data: boolean;
  };
}

export const AI_FOLDERS: Record<string, string> = {
  claude: '.claude',
  cursor: '.cursor',
  windsurf: '.windsurf',
  antigravity: '.agent',
  copilot: '.github',
  kiro: '.kiro',
  codex: '.codex',
  qoder: '.qoder',
  cline: '.cline',
  gemini: '.gemini',
  trae: '.trae',
  opencode: '.opencode',
  continue: '.continue',
  codebuddy: '.codebuddy',
};
