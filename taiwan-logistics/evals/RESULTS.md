# evals 結果

最新的在最上面。題目與評分標準見 `cases.json`，評分程式 `grade.py`。

## 2026-11-15 第 1 輪（現行題組）

2 題沒 skill 也答對（`lalamove-quote-ttl`、`lalamove-change-driver`），已在 `cases.json` 標 `retired`；剩下 11 題都有鑑別度。

| 項目 | 有 skill | 沒有 skill |
|---|---|---|
| 計分題答對率（11 題） | **11/11（100.0%）** | 0/11（0.0%） |
| 全部題目（13 題） | 13/13 | 2/13 |
| 模型 | claude-opus-5-5 | claude-opus-5-5 |
| 作答方式 | subagent 讀 SKILL.md、用 search.py 查 | subagent 不用任何工具查資料，憑記憶作答 |
| 答案檔 | `evals/runs/2026-11-15-with-skill.json` | `evals/runs/2026-11-15-without-skill.json` |

| 題目 | 可信度 | 有 skill | 沒有 skill | 備註 |
|---|---|---|---|---|
| `paynow-3des-key` | 官方文件 | ✅ | ❌ |  |
| `lalamove-quote-ttl` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |
| `lalamove-change-driver` | 官方文件 | ✅ | ✅ | 沒 skill 也對：不計分，要換題 |
| `ezship-param-naming` | 官方文件 | ✅ | ❌ |  |
| `ecpay-status-7020` | 官方文件 | ✅ | ❌ |  |
| `payuni-lgr03014` | 官方文件 | ✅ | ❌ |  |
| `payuni-shipstatus-81` | 官方文件 | ✅ | ❌ |  |
| `pchomepay-ssnd` | 官方文件 | ✅ | ❌ |  |
| `smilepay-00022` | 官方文件 | ✅ | ❌ |  |
| `paynow-7204` | 官方文件 | ✅ | ❌ |  |
| `newebpay-1111` | 官方文件 | ✅ | ❌ |  |
| `ezship-s06` | 官方文件 | ✅ | ❌ |  |
| `ezship-711` | 官方文件 | ✅ | ❌ |  |

