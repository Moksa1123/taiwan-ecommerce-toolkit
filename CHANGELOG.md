# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-01-28

### Added

- Cursor 支援：新增 `.cursor/skills/taiwan-invoice/` 目錄（符合 Cursor Skills 規範）
- Google Antigravity 支援：新增 `.agent/skills/taiwan-invoice/` 目錄
- 專業 GitHub 檔案：LICENSE (MIT)、CONTRIBUTING.md
- EXAMPLES.md 移入 `taiwan-invoice/` 目錄

### Changed

- 全面重寫以符合三個平台的官方規範
  - Claude Code: `.claude/skills/` 自動發現機制
  - Cursor: `.cursor/skills/` SKILL.md 格式（非 .mdc）
  - Antigravity: `.agent/skills/` + `~/.gemini/antigravity/global_skills/` 全域路徑
- SKILL.md frontmatter 新增 `user-invocable: true`
- 安裝腳本修正各平台正確路徑
- Claude Code 呼叫方式更正為 `/taiwan-invoice`（非 `@taiwan-invoice`）
- README.md 重寫為專業格式，整合多份文檔
- CHANGELOG.md 改用 Keep a Changelog 格式
- API 參考文檔中的 emoji 標記替換為純文字（Y/N）
- 程式碼範例中的 emoji 替換為文字標記（[OK], [ERROR], [PASS] 等）

### Removed

- `.claude/settings.json`（錯誤格式，Claude Code 不需要）
- `.cursor/settings.json`（錯誤格式，已改用 `.cursor/skills/`）
- `.cursor/rules/taiwan-invoice.mdc`（Cursor 使用 SKILL.md 而非 .mdc）
- 根目錄重複的 API 參考文檔（正本已在 `taiwan-invoice/references/`）
- `taiwan-invoice-development.md`（舊版，已被 SKILL.md 取代）
- 多個冗餘文檔：QUICK_START.md、STRUCTURE.md、PROJECT_SUMMARY.md、USAGE_GUIDE.md
- `taiwan-invoice/README.md`（與 SKILL.md 重複）
- 所有檔案中的 emoji 字元

### Fixed

- Cursor 安裝路徑：從 `.cursor/skills/`（正確）取代 `.cursor/rules/`（錯誤）
- Antigravity 全域路徑：使用 `global_skills/`（正確）取代 `skills/`（錯誤）
- `taiwan-invoice/references/*.md` 從縮寫指標改為完整內容

## [1.0.0] - 2026-01-28

### Added

- 初始版本
- 台灣電子發票 Skill 定義（SKILL.md）
- 三家服務商 API 參考文檔（ECPay、SmilePay、Amego）
- 程式碼範例集
- 金額計算測試腳本
- 服務商實作生成腳本
- 安裝腳本（macOS/Linux/Windows）
- 多平台支援文檔

[Unreleased]: https://github.com/Moksa1123/taiwan-invoice/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/Moksa1123/taiwan-invoice/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/Moksa1123/taiwan-invoice/releases/tag/v1.0.0
