import { build } from 'esbuild';
import { writeFileSync, readFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const distDir = join(__dirname, '..', 'dist');

async function main() {
  console.log('Building taiwan-invoice-skill CLI...');

  // Ensure dist directory exists
  if (!existsSync(distDir)) {
    mkdirSync(distDir, { recursive: true });
  }

  // Build with esbuild - CommonJS format for better compatibility
  await build({
    entryPoints: [join(__dirname, '..', 'src', 'index.ts')],
    bundle: true,
    platform: 'node',
    format: 'cjs',
    outfile: join(distDir, 'index.js'),
    external: [],
    target: 'node18',
  });

  // Read the generated file and prepend shebang
  const outputPath = join(distDir, 'index.js');
  let content = readFileSync(outputPath, 'utf-8');

  // Remove any existing shebangs (in case source had one)
  content = content.replace(/^#!.*\n/gm, '');

  // Add proper shebang at the beginning
  const withShebang = '#!/usr/bin/env node\n' + content;
  writeFileSync(outputPath, withShebang);

  console.log('Build complete!');
  console.log('  dist/index.js');
}

main().catch(err => {
  console.error('Build failed:', err);
  process.exit(1);
});
