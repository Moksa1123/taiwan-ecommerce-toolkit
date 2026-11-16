# evals 結果

最新的在最上面。題目與評分標準見 `cases.json`，評分程式 `grade.py`。

## 2026-11-15 第 1 輪（現行題組）

4 題沒 skill 也答對（`jkopay-digest-header`、`shopline-webhook-sign`、`ezpay-padding-32`、`ecpay-10100058`），已在 `cases.json` 標 `retired`；剩下 10 題都有鑑別度。

| 項目 | 有 skill | 沒有 skill |
|---|---|---|
| 計分題答對率（10 題） | **10/10（100.0%）** | 0/10（0.0%） |
| 全部題目（14 題） | 14/14 | 4/14 |
| 模型 | claude-opus-5-5 | claude-opus-5-5 |
| 作答方式 | subagent 讀 SKILL.md、用 search.py 查 | subagent 不用任何工具查資料，憑記憶作答 |
| 答案檔 | `evals/runs/2026-11-15-with-skill.json` | `evals/runs/2026-11-15-without-skill.json` |

| 題目 | 可信度 | 有 skill | 沒有 skill | 備註 |
|---|---|---|---|---|
| `sunpay-rsa-chunk` | 官方文件 | ✅ | ❌ |  |
| `pchomepay-notify-ip` | 官方文件 | ✅ | ❌ |  |
| `jkopay-digest-header` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |
| `shopline-webhook-sign` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |
| `ezpay-twqr-apiid` | 官方文件 | ✅ | ❌ |  |
| `ezpay-padding-32` | 實測 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |
| `sunpay-error-22` | 官方文件 | ✅ | ❌ |  |
| `pchomepay-error-50009` | 官方文件 | ✅ | ❌ |  |
| `jkopay-error-307` | 官方文件 | ✅ | ❌ |  |
| `shopline-error-4407` | 官方文件 | ✅ | ❌ |  |
| `paynow-error-r033` | 官方文件 | ✅ | ❌ |  |
| `linepay-error-1193` | 官方文件 | ✅ | ❌ |  |
| `paynow-bootstrap-key` | 官方文件 | ✅ | ❌ |  |
| `ecpay-10100058` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |

