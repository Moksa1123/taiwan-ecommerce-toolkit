export type AIType =
  | 'claude'
  | 'cursor'
  | 'windsurf'
  | 'antigravity'
  | 'copilot'
  | 'kiro'
  | 'codex'
  | 'qoder'
  | 'roocode'
  | 'gemini'
  | 'trae'
  | 'opencode'
  | 'continue'
  | 'codebuddy'
  | 'all';

export type InstallType = 'full' | 'reference' | 'workflow';

// GitHub Release API types
export interface Asset {
  name: string;
  browser_download_url: string;
  size: number;
  download_count: number;
}

export interface Release {
  tag_name: string;
  name: string;
  published_at: string;
  html_url: string;
  assets: Asset[];
}

export interface PlatformConfig {
  platform: string;
  displayName: string;
  installType: InstallType;
  folderStructure: {
    root: string;
    skillPath: string;
    filename: string;
    sharedRoot?: string;
    sharedPath?: string;
  };
  scriptPath?: string;
  frontmatter: Record<string, string> | null;
  sections: {
    examples: boolean;
    references: boolean;
    scripts: boolean;
    quickReference?: boolean;
  };
  title: string;
  description: string;
  skillOrWorkflow?: string;
}

export const AI_TYPES: AIType[] = [
  'claude',
  'cursor',
  'windsurf',
  'antigravity',
  'copilot',
  'kiro',
  'codex',
  'qoder',
  'roocode',
  'gemini',
  'trae',
  'opencode',
  'continue',
  'codebuddy',
  'all'
];

export const AI_FOLDERS: Record<Exclude<AIType, 'all'>, string[]> = {
  claude: ['.claude'],
  cursor: ['.cursor'],
  windsurf: ['.windsurf'],
  antigravity: ['.agent', '.shared'],
  copilot: ['.github'],
  kiro: ['.kiro'],
  codex: ['.codex'],
  qoder: ['.qoder'],
  roocode: ['.roo'],
  gemini: ['.gemini'],
  trae: ['.trae'],
  opencode: ['.opencode'],
  continue: ['.continue'],
  codebuddy: ['.codebuddy'],
};
