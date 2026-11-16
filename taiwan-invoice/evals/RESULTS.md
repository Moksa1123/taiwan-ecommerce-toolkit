# evals 結果

最新的在最上面。題目與評分標準見 `cases.json`，評分程式 `grade.py`。

## 2026-11-15 現行題組（第 1 輪留下 5 題＋第 2 輪新題 7 題）

第 1 輪有 7 題沒 skill 也答對，已在 `cases.json` 標 `retired`；第 2 輪補 7 題新題（Amego、ezPay、SmilePay 錯誤碼、綠界 4000004、PayNow POS 端點）。
第 1 輪後收緊了 `smilepay-error-10022` 的評分規則（原規則讓沒 skill 的錯答過關），兩邊同規則重評。

| 項目 | 有 skill | 沒有 skill |
|---|---|---|
| 計分題答對率（12 題） | **12/12（100.0%）** | 0/12（0.0%） |
| 全部題目（12 題） | 12/12 | 0/12 |
| 模型 | claude-opus-5-5 | claude-opus-5-5 |
| 作答方式 | subagent 讀 SKILL.md、用 search.py 查 | subagent 不用任何工具查資料，憑記憶作答 |
| 答案檔 | `evals/runs/2026-11-15-r1+r2-with-skill.json` | `evals/runs/2026-11-15-r1+r2-without-skill.json` |

| 題目 | 可信度 | 有 skill | 沒有 skill | 備註 |
|---|---|---|---|---|
| `sunpay-inv-prod-domain` | 官方文件 | ✅ | ❌ |  |
| `amego-error-3050131` | 官方文件 | ✅ | ❌ |  |
| `smilepay-error-10033` | 官方文件 | ✅ | ❌ |  |
| `ezpay-error-key10007` | 官方文件 | ✅ | ❌ |  |
| `smilepay-error-10022` | 官方文件 | ✅ | ❌ |  |
| `amego-error-4040133` | 官方文件 | ✅ | ❌ |  |
| `ezpay-error-lib10009` | 官方文件 | ✅ | ❌ |  |
| `ezpay-error-clc10004` | 官方文件 | ✅ | ❌ |  |
| `smilepay-error-10057` | 官方文件 | ✅ | ❌ |  |
| `smilepay-error-100411` | 官方文件 | ✅ | ❌ |  |
| `ecpay-inv-4000004` | 官方文件 | ✅ | ❌ |  |
| `paynow-pos-invoice-numbers` | 官方文件 | ✅ | ❌ |  |

## 2026-11-15 第 1 輪（舊題組）

表格是當時的評分輸出；標「不計分」的 7 題已淘汰。

| 項目 | 有 skill | 沒有 skill |
|---|---|---|
| 計分題答對率（5 題） | **5/5（100.0%）** | 0/5（0.0%） |
| 全部題目（12 題） | 12/12 | 7/12 |
| 模型 | claude-opus-5-5 | claude-opus-5-5 |
| 作答方式 | subagent 讀 SKILL.md、用 search.py 查 | subagent 不用任何工具查資料，憑記憶作答 |
| 答案檔 | `evals/runs/2026-11-15-with-skill.json` | `evals/runs/2026-11-15-without-skill.json` |

| 題目 | 可信度 | 有 skill | 沒有 skill | 備註 |
|---|---|---|---|---|
| `sunpay-inv-prod-domain` | 官方文件 | ✅ | ❌ |  |
| `sunpay-validate-token` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |
| `sunpay-three-sales-amounts` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |
| `opay-timestamp-window` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |
| `opay-b2b-modes` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |
| `amego-sign-formula` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |
| `amego-error-3050131` | 官方文件 | ✅ | ❌ |  |
| `smilepay-error-10033` | 官方文件 | ✅ | ❌ |  |
| `smilepay-account-field` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |
| `ezpay-error-key10007` | 官方文件 | ✅ | ❌ |  |
| `smilepay-error-10022` | 官方文件 | ✅ | ❌ |  |
| `opay-donation-print` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |

