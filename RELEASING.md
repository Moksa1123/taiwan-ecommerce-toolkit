# 發布流程

本 repo 有三個各自獨立版號的 npm 套件：

| 套件 | 目錄 | tag 前綴 |
|---|---|---|
| `taiwan-invoice-skill` | `invoice-cli/` | `invoice-v` |
| `taiwan-payment-skill` | `payment-cli/` | `payment-v` |
| `taiwan-logistics-skill` | `logistics-cli/` | `logistics-v` |

推送符合前綴的 tag 即觸發 `.github/workflows/publish.yml` 發布對應套件。

## 一次性設定：npm Trusted Publishing

發布採 OIDC（Trusted Publishing），**repo 不存放任何 npm token**。需先在 npm 網站為**三個套件各做一次**設定：

1. 登入 npmjs.com → 進入套件頁 → **Settings** → **Trusted Publisher**
2. 選擇 GitHub Actions，填入：

   | 欄位 | 值 |
   |---|---|
   | Organization or user | `Moksa1123` |
   | Repository | `taiwan-ecommerce-toolkit` |
   | Workflow filename | `publish.yml` |
   | Environment | 留空 |

3. 三個套件都填**同一個 workflow filename**（本 repo 只有一支發布 workflow）

設定完成後即可移除既有的 npm token（若有）。

> 若之後改用 NPM_TOKEN，需在 workflow 的 publish 步驟加上
> `env: NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}`，並可移除 `id-token: write` 權限。

## 發布步驟

以 payment 從 1.3.4 發到 1.3.5 為例：

```bash
# 1. 確認在 main 且是最新的
git checkout main && git pull

# 2. 更新版號
cd payment-cli && npm version 1.3.5 --no-git-tag-version && cd ..

# 3. 本機驗證（build 會自動同步 assets）
node scripts/sync-assets.mjs
python scripts/validate-data.py
python taiwan-payment/scripts/test_recommend.py
cd payment-cli && npm run build && npm pack --dry-run && cd ..

# 4. commit 版號與同步後的 assets
git add -A
git commit -m "chore(payment): bump to 1.3.5"
git push

# 5. 打 tag 觸發發布
git tag payment-v1.3.5
git push origin payment-v1.3.5
```

**tag 版號必須與 `package.json` 一致**，workflow 會驗證，不一致直接失敗。

## workflow 會擋下什麼

| 檢查 | 擋下的情況 |
|---|---|
| tag 版本 vs `package.json` | 忘記更新版號、或 tag 打錯 |
| `sync-assets.mjs --check` | **assets 落後於 source of truth** |
| `validate-data.py` | CSV 欄位錯位、主鍵重複、必填欄為空 |
| `test_recommend.py` | 推薦系統行為退化 |
| 建置後 `git diff` | commit 的 assets 不是最新的 |

第二項是這套流程最主要的目的。三個套件的 `package.json` 都把 `assets` 列入 `files`，代表 **skill 內容會隨套件一起發布**。過去同步是手動步驟，一旦忘記就會發出過期的內容，而且**沒有任何錯誤訊息**——使用者安裝到舊資料卻不會察覺。

## 試跑（不實際發布）

### 方式一：本機（隨時可用，推薦）

```bash
node scripts/preflight.mjs                 # 檢查全部三個套件
node scripts/preflight.mjs payment         # 只檢查 payment
node scripts/preflight.mjs payment 1.4.0   # 另外驗證 tag 版號會不會過
```

執行與 workflow 相同的所有驗證，唯一不含最後的 `npm publish`（需 GitHub OIDC 憑證）。通過回 exit 0，任一項失敗回 exit 1 並指出原因。

**打 tag 前先跑這個**——否則 tag 推上去才失敗，得刪 tag 重來：

```bash
git tag -d payment-v1.4.0
git push origin :refs/tags/payment-v1.4.0
```

### 方式二：GitHub Actions

Actions → Publish to npm → **Run workflow**，選套件並保持 `dry_run` 勾選。

> ⚠️ **這個按鈕要等 workflow 進入預設分支（`main`）才會出現。** GitHub 的
> `workflow_dispatch` 只讀取預設分支上的 workflow 定義，在 feature 分支上
> 推 commit 不會讓它出現在 Actions 頁面。合併前請用方式一。

## 舊 tag

改用前綴規則之前的 tag 保留不動，不會觸發 workflow：

```
v2.5.2  v2.5.3  v2.5.4  v2.6.4      # 裸版號（invoice）
v1.1.4-payment   v1.1.4-logistics   # 舊的後綴格式
```
