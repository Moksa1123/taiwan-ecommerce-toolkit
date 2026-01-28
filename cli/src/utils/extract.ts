import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';
import type { AIType } from '../types';
import { AI_FOLDERS } from '../types';

/**
 * Extract ZIP file to destination directory
 * Uses platform-native tools (PowerShell on Windows, unzip on Unix)
 */
export async function extractZip(zipPath: string, destDir: string): Promise<void> {
  // Ensure destination exists
  if (!fs.existsSync(destDir)) {
    fs.mkdirSync(destDir, { recursive: true });
  }

  const isWindows = process.platform === 'win32';

  if (isWindows) {
    // Use PowerShell's Expand-Archive
    const psCommand = `Expand-Archive -Path "${zipPath}" -DestinationPath "${destDir}" -Force`;
    execSync(`powershell -Command "${psCommand}"`, { stdio: 'pipe' });
  } else {
    // Use unzip command
    execSync(`unzip -o "${zipPath}" -d "${destDir}"`, { stdio: 'pipe' });
  }
}

/**
 * Copy folders from extracted source to target directory
 */
export async function copyFolders(
  sourceDir: string,
  targetDir: string,
  aiType: Exclude<AIType, 'all'>
): Promise<string[]> {
  const copiedFolders: string[] = [];
  const foldersToCheck = AI_FOLDERS[aiType];

  for (const folder of foldersToCheck) {
    const sourcePath = path.join(sourceDir, folder);
    const targetPath = path.join(targetDir, folder);

    if (fs.existsSync(sourcePath)) {
      copyDirRecursive(sourcePath, targetPath);
      copiedFolders.push(folder);
    }
  }

  return copiedFolders;
}

/**
 * Recursively copy directory
 */
function copyDirRecursive(src: string, dest: string): void {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }

  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDirRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

/**
 * Find extracted folder (GitHub ZIP usually creates a subfolder)
 */
export function findExtractedFolder(destDir: string): string | null {
  const entries = fs.readdirSync(destDir, { withFileTypes: true });
  const dirs = entries.filter(e => e.isDirectory());

  // Look for folder matching pattern like "taiwan-invoice-v1.0.0"
  const releaseDir = dirs.find(d =>
    d.name.includes('taiwan-invoice') ||
    d.name.startsWith('taiwan-invoice')
  );

  return releaseDir ? path.join(destDir, releaseDir.name) : null;
}

/**
 * Install from ZIP file
 */
export async function installFromZip(
  zipPath: string,
  targetDir: string,
  aiType: Exclude<AIType, 'all'>
): Promise<{ copiedFolders: string[]; tempDir: string }> {
  const tempDir = path.join(path.dirname(zipPath), 'taiwan-invoice-extracted');

  // Clean up any existing temp directory
  if (fs.existsSync(tempDir)) {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }

  // Extract ZIP
  await extractZip(zipPath, tempDir);

  // Find the extracted folder
  const extractedDir = findExtractedFolder(tempDir) || tempDir;

  // Copy folders for the specified AI type
  const copiedFolders = await copyFolders(extractedDir, targetDir, aiType);

  return { copiedFolders, tempDir };
}

/**
 * Clean up temporary files
 */
export function cleanup(tempDir: string, zipPath?: string): void {
  if (tempDir && fs.existsSync(tempDir)) {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
  if (zipPath && fs.existsSync(zipPath)) {
    fs.unlinkSync(zipPath);
  }
}
