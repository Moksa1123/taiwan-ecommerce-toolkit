#!/usr/bin/env node
/**
 * 將 source of truth 的 skill 內容同步到各 CLI 的 assets/。
 *
 * 為什麼需要這支：三個 CLI 的 package.json 都把 `assets` 列入 `files`，
 * 代表 assets 會被一起發布到 npm。過去同步是手動步驟（見 CLAUDE.md
 * Sync Rules），一旦忘記就會把過期的 skill 內容發出去，而且不會有任何
 * 錯誤訊息 —— 使用者安裝到的是舊資料。
 *
 * 因此改為：
 *   - build.js 在打包前自動呼叫本腳本（涵蓋手動 npm publish）
 *   - CI 在發布前以 --check 驗證（涵蓋 tag 觸發的自動發布）
 *
 * 同步兩類內容：
 *   1. 鏡像 assets/taiwan-<skill>/（整個 source of truth 目錄）
 *   2. 由 taiwan-<skill>/SKILL.md 產生 assets/templates/base/skill-content.md
 *      —— 過去這份是手工複製的 SKILL.md，修正常只改到其中一份（例如 PAYUNi 加密
 *      格式在 SKILL.md 修了、模板沒修，使用者安裝到的仍是錯的）；logistics 的模板
 *      甚至把 {{DESCRIPTION}} 蓋在 HCT 註解上。改為自動產生後兩者不可能再分歧。
 * assets/templates/ 其餘檔案（platforms/*.json、quick-reference.md）仍為手工維護。
 *
 * 用法:
 *   node scripts/sync-assets.mjs                 # 同步全部
 *   node scripts/sync-assets.mjs --only invoice  # 只同步單一套件
 *   node scripts/sync-assets.mjs --check         # 只檢查，有落差則 exit 1
 */

import { readdirSync, statSync, mkdirSync, copyFileSync, readFileSync, rmSync, existsSync, writeFileSync } from 'fs';
import { join, relative, dirname } from 'path';
import { fileURLToPath } from 'url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

export const PACKAGES = [
  { key: 'invoice', src: 'taiwan-invoice', cli: 'invoice-cli', pkg: 'taiwan-invoice-skill' },
  { key: 'payment', src: 'taiwan-payment', cli: 'payment-cli', pkg: 'taiwan-payment-skill' },
  { key: 'logistics', src: 'taiwan-logistics', cli: 'logistics-cli', pkg: 'taiwan-logistics-skill' },
];

// 這些是本機產物或作業系統垃圾檔，不該進入發布包
const EXCLUDE_DIRS = new Set(['__pycache__', '.pytest_cache', 'node_modules', '.git']);
const EXCLUDE_FILES = /\.(pyc|pyo|pyd)$|^\.DS_Store$|^Thumbs\.db$/;

function walk(dir, base = dir, out = []) {
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      if (EXCLUDE_DIRS.has(name)) continue;
      walk(full, base, out);
    } else {
      if (EXCLUDE_FILES.test(name)) continue;
      out.push(relative(base, full).split('\\').join('/'));
    }
  }
  return out;
}

/**
 * SKILL.md → 模板：去掉 frontmatter，H1 換成 {{TITLE}}，
 * H1 後的第一段 blockquote 換成 {{DESCRIPTION}}（沒有的話就插入一段）。
 */
export function renderSkillTemplate(skillMd) {
  // 沿用來源的換行字元：Windows 上 autocrlf 會是 CRLF，CI（Linux）則是 LF，
  // 輸出須與同一份工作目錄內的其他檔案一致，否則 --check 會在某一邊誤報
  const eol = skillMd.includes('\r\n') ? '\r\n' : '\n';
  let text = skillMd.replace(/\r\n/g, '\n');
  if (text.startsWith('---\n')) {
    const end = text.indexOf('\n---\n', 4);
    if (end !== -1) text = text.slice(end + 5).replace(/^\n+/, '');
  }
  const lines = text.split('\n');
  const h1 = lines.findIndex((l) => l.startsWith('# '));
  if (h1 === -1) throw new Error('SKILL.md 缺少 H1 標題');
  lines[h1] = '# {{TITLE}}';

  let i = h1 + 1;
  while (i < lines.length && lines[i].trim() === '') i += 1;
  if (i < lines.length && lines[i].startsWith('> ')) {
    lines[i] = '> {{DESCRIPTION}}';
  } else {
    lines.splice(h1 + 1, 0, '', '> {{DESCRIPTION}}');
  }
  return lines.join(eol);
}

function templateTarget({ src, cli }) {
  const path = join(ROOT, cli, 'assets', 'templates', 'base', 'skill-content.md');
  const expected = renderSkillTemplate(readFileSync(join(ROOT, src, 'SKILL.md'), 'utf8'));
  const stale = !existsSync(path) || readFileSync(path, 'utf8') !== expected;
  return { path, expected, stale };
}

const TEMPLATE_LABEL = 'templates/base/skill-content.md（由 SKILL.md 產生）';

function sameContent(a, b) {
  if (!existsSync(b)) return false;
  return readFileSync(a).equals(readFileSync(b));
}

/** 回傳這個套件的落差清單（不修改任何檔案） */
function diffPackage({ src, cli }) {
  const srcDir = join(ROOT, src);
  const dstDir = join(ROOT, cli, 'assets', src);

  const srcFiles = walk(srcDir);
  const dstFiles = walk(dstDir);
  const dstSet = new Set(dstFiles);

  const added = [];
  const changed = [];
  for (const rel of srcFiles) {
    if (!dstSet.has(rel)) added.push(rel);
    else if (!sameContent(join(srcDir, rel), join(dstDir, rel))) changed.push(rel);
  }

  const srcSet = new Set(srcFiles);
  const removed = dstFiles.filter((rel) => !srcSet.has(rel));

  if (templateTarget({ src, cli }).stale) changed.push(TEMPLATE_LABEL);

  return { srcDir, dstDir, added, changed, removed };
}

function syncPackage(target) {
  const { srcDir, dstDir, added, changed, removed } = diffPackage(target);

  for (const rel of [...added, ...changed]) {
    if (rel === TEMPLATE_LABEL) {
      const { path, expected } = templateTarget(target);
      writeFileSync(path, expected);
      continue;
    }
    const to = join(dstDir, rel);
    mkdirSync(dirname(to), { recursive: true });
    copyFileSync(join(srcDir, rel), to);
  }
  // 鏡像語意：來源已刪除的檔案也要從 assets 移除，否則會發布出早已不存在的內容
  for (const rel of removed) {
    rmSync(join(dstDir, rel), { force: true });
  }

  return { added, changed, removed };
}

/**
 * 供各 CLI 的 build.js 呼叫：同步指定套件的 assets。
 * 在打包前執行，確保 prepublishOnly 觸發的手動發布也帶到最新內容。
 */
export function syncOne(key) {
  const target = PACKAGES.find((p) => p.key === key);
  if (!target) throw new Error(`未知的套件: ${key}`);

  const { added, changed, removed } = syncPackage(target);
  const total = added.length + changed.length + removed.length;
  console.log(total === 0 ? '  assets 已是最新' : `  assets 已同步（新增 ${added.length} / 變更 ${changed.length} / 移除 ${removed.length}）`);
  return { added, changed, removed };
}

function describe(label, { added, changed, removed }) {
  const total = added.length + changed.length + removed.length;
  if (total === 0) return `  ${label.padEnd(10)} 已同步`;

  const parts = [];
  if (added.length) parts.push(`新增 ${added.length}`);
  if (changed.length) parts.push(`變更 ${changed.length}`);
  if (removed.length) parts.push(`移除 ${removed.length}`);

  const files = [...added.map((f) => `+ ${f}`), ...changed.map((f) => `~ ${f}`), ...removed.map((f) => `- ${f}`)];
  const shown = files.slice(0, 10).map((f) => `      ${f}`).join('\n');
  const more = files.length > 10 ? `\n      … 另有 ${files.length - 10} 個檔案` : '';

  return `  ${label.padEnd(10)} ${parts.join(' / ')}\n${shown}${more}`;
}

function main() {
  const args = process.argv.slice(2);
  const check = args.includes('--check');
  const onlyIdx = args.indexOf('--only');
  const only = onlyIdx !== -1 ? args[onlyIdx + 1] : null;

  let targets = PACKAGES;
  if (only) {
    targets = PACKAGES.filter((p) => p.key === only);
    if (targets.length === 0) {
      console.error(`未知的套件: ${only}（可用：${PACKAGES.map((p) => p.key).join(', ')}）`);
      process.exit(2);
    }
  }

  console.log(check ? '檢查 CLI assets 是否與 source of truth 同步…' : '同步 CLI assets…');

  let drifted = 0;
  for (const target of targets) {
    const result = check ? diffPackage(target) : syncPackage(target);
    const total = result.added.length + result.changed.length + result.removed.length;
    if (total > 0) drifted += 1;
    console.log(describe(target.key, result));
  }

  if (check && drifted > 0) {
    console.error(
      `\n有 ${drifted} 個套件的 assets 與來源不一致。\n` +
        '執行 `node scripts/sync-assets.mjs` 後 commit，再重新發布。'
    );
    process.exit(1);
  }

  console.log(check ? '\n全部已同步。' : '\n完成。');
}

// 被 build.js import 時不執行 main
if (process.argv[1] && process.argv[1].endsWith('sync-assets.mjs')) {
  main();
}
