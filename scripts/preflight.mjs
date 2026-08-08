#!/usr/bin/env node
/**
 * 本機試跑：執行與 .github/workflows/publish.yml 相同的所有驗證，但不發布。
 *
 * 用途有二：
 *   1. workflow 尚未進入預設分支時，GitHub 的 workflow_dispatch 按不到，
 *      這支可在本機得到等價結果
 *   2. 打 tag 之前先確認會過，避免用 tag 當試錯工具（tag 推上去才失敗，
 *      得刪 tag 重來）
 *
 * 唯一無法在本機驗證的是最後的 npm publish（需要 GitHub OIDC 憑證）。
 *
 * 用法:
 *   node scripts/preflight.mjs                 # 檢查全部三個套件
 *   node scripts/preflight.mjs payment         # 只檢查 payment
 *   node scripts/preflight.mjs payment 1.4.0   # 另外驗證 tag 版號
 */

import { execFileSync, execSync } from 'child_process';
import { existsSync, readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

const PACKAGES = {
  invoice: { dir: 'invoice-cli', src: 'taiwan-invoice', pkg: 'taiwan-invoice-skill' },
  payment: { dir: 'payment-cli', src: 'taiwan-payment', pkg: 'taiwan-payment-skill' },
  logistics: { dir: 'logistics-cli', src: 'taiwan-logistics', pkg: 'taiwan-logistics-skill' },
};

const IS_WIN = process.platform === 'win32';
const PYTHON = IS_WIN ? 'python' : 'python3';

let failed = 0;

function run(label, cmd, args, opts = {}) {
  process.stdout.write(`  ${label} … `);
  try {
    const out = execFileSync(cmd, args, {
      cwd: opts.cwd ? join(ROOT, opts.cwd) : ROOT,
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    });
    console.log('OK');
    return { ok: true, out };
  } catch (err) {
    console.log('FAIL');
    const detail = [err.stdout, err.stderr].filter(Boolean).join('\n').trim();
    if (detail) console.log(detail.split('\n').map((l) => `      ${l}`).join('\n'));
    failed += 1;
    return { ok: false, out: detail };
  }
}

/**
 * npm 在 Windows 是 npm.cmd，而 Node 20+ 為修補 CVE-2024-27980 禁止不經 shell
 * 執行 .cmd（會回 EINVAL），因此 npm 一律走 shell。
 * 這裡刻意把整串命令當單一字串傳入而非另外給 args 陣列 —— 後者會觸發
 * Node 的 DEP0190 警告（參數以字串串接、未跳脫）。本檔的命令皆為靜態字面值，
 * 不含任何外部輸入。
 */
function runShell(label, command, cwd) {
  process.stdout.write(`  ${label} … `);
  try {
    execSync(command, {
      cwd: join(ROOT, cwd),
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    console.log('OK');
    return { ok: true };
  } catch (err) {
    console.log('FAIL');
    const detail = [err.stdout, err.stderr].filter(Boolean).join('\n').trim();
    if (detail) console.log(detail.split('\n').map((l) => `      ${l}`).join('\n'));
    failed += 1;
    return { ok: false };
  }
}

function check(label, condition, detail) {
  process.stdout.write(`  ${label} … `);
  if (condition) {
    console.log('OK');
  } else {
    console.log('FAIL');
    if (detail) console.log(`      ${detail}`);
    failed += 1;
  }
  return condition;
}

const [key, tagVersion] = process.argv.slice(2);
const targets = key ? [key] : Object.keys(PACKAGES);

if (key && !PACKAGES[key]) {
  console.error(`未知的套件: ${key}（可用：${Object.keys(PACKAGES).join(', ')}）`);
  process.exit(2);
}

/** 目前工作區狀態，用來比對建置前後 */
function gitState() {
  try {
    return execFileSync('git', ['status', '--porcelain'], { cwd: ROOT, encoding: 'utf-8' });
  } catch {
    return '';
  }
}

console.log('本機試跑 —— 與 publish.yml 相同的驗證（不含發布）\n');

const stateBeforeBuild = gitState();

console.log('共用檢查');
run('assets 同步', 'node', ['scripts/sync-assets.mjs', '--check']);
run('資料檔完整性', PYTHON, ['scripts/validate-data.py']);
run('推薦回歸（invoice）', PYTHON, ['taiwan-invoice/scripts/test_recommend.py']);
run('推薦回歸（payment）', PYTHON, ['taiwan-payment/scripts/test_recommend.py']);

for (const k of targets) {
  const { dir, pkg } = PACKAGES[k];
  const version = JSON.parse(readFileSync(join(ROOT, dir, 'package.json'), 'utf-8')).version;
  console.log(`\n${pkg} @ ${version}`);

  if (tagVersion && key === k) {
    check(
      `tag 版號一致（${tagVersion}）`,
      version === tagVersion,
      `package.json 為 ${version}，與 tag 的 ${tagVersion} 不符`
    );
  }

  check('lockfile 版號一致', (() => {
    const lockPath = join(ROOT, dir, 'package-lock.json');
    if (!existsSync(lockPath)) return false;
    const lock = JSON.parse(readFileSync(lockPath, 'utf-8'));
    return lock.version === version && lock.packages?.['']?.version === version;
  })(), 'package-lock.json 版號與 package.json 不符，npm ci 會失敗');

  runShell('建置', 'npm run build', dir);
  runShell('打包內容', 'npm pack --dry-run', dir);
}

// CI 的 checkout 是乾淨的，所以 workflow 直接用 `git diff --quiet` 即可；
// 但在本機準備發版時工作區本來就有未 commit 的改動，直接判斷「是否乾淨」
// 會永遠失敗。這裡改為比較建置前後的差異，只有建置「新造成」的變動才算問題。
console.log('\n建置後工作區');
check(
  '建置未產生新變動',
  gitState() === stateBeforeBuild,
  '建置改動了已追蹤的檔案 —— 代表 assets 與 source of truth 不同步且尚未 commit'
);

const dirty = gitState().trim();
if (dirty) {
  const count = dirty.split('\n').length;
  console.log(`\n  提醒：工作區有 ${count} 個未 commit 的變動，記得先 commit 再打 tag`);
}

console.log('\n' + '─'.repeat(60));
if (failed > 0) {
  console.log(`[FAIL] ${failed} 項未通過 —— 修正後再打 tag`);
  process.exit(1);
}
console.log('[DONE] 全部通過 —— 可以打 tag 發布');
console.log('       實際發布另需 npm Trusted Publisher 已設定（見 RELEASING.md）');
