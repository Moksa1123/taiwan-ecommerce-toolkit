export type AIType = 'claude' | 'cursor' | 'antigravity' | 'all';

export type InstallType = 'full' | 'reference';

export interface PlatformConfig {
  platform: string;
  displayName: string;
  installType: InstallType;
  folderStructure: {
    root: string;
    skillPath: string;
    filename: string;
  };
  frontmatter: Record<string, string> | null;
  sections: {
    examples: boolean;
    references: boolean;
    scripts: boolean;
  };
  title: string;
  description: string;
}

export const AI_TYPES: AIType[] = ['claude', 'cursor', 'antigravity', 'all'];

export const AI_FOLDERS: Record<Exclude<AIType, 'all'>, string[]> = {
  claude: ['.claude'],
  cursor: ['.cursor'],
  antigravity: ['.agent'],
};
