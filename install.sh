#!/bin/bash
# Taiwan Invoice Claude Skills - 安裝腳本
# 支援 macOS / Linux

set -e

echo "Taiwan Invoice Claude Skills 安裝程式"
echo "=========================================="
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢測作業系統
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=Linux;;
    Darwin*)    PLATFORM=Mac;;
    *)          PLATFORM="UNKNOWN:${OS}"
esac

echo "偵測到作業系統: $PLATFORM"
echo ""

# 確認來源目錄存在
if [ ! -d "./taiwan-invoice" ]; then
    echo -e "${RED}[ERROR] 找不到 taiwan-invoice 目錄，請在專案根目錄執行此腳本${NC}"
    exit 1
fi

# 詢問安裝位置
echo "請選擇安裝位置："
echo "1) Claude Code 全域 (~/.claude/skills/)"
echo "2) 當前專案 - Claude Code (./.claude/skills/)"
echo "3) Cursor - 專案 (./.cursor/skills/)"
echo "4) Google Antigravity - 專案 (./.agent/skills/)"
echo "5) Google Antigravity - 全域 (~/.gemini/antigravity/global_skills/)"
echo "6) 全部安裝（Claude Code + Cursor + Antigravity）"
echo "7) 自訂路徑"
echo ""
read -p "請選擇 [1-7]: " choice

install_skill_dir() {
    local dir="$1"
    local name="$2"

    mkdir -p "$(dirname "$dir")"

    if [ -d "$dir" ]; then
        echo -e "${YELLOW}[WARNING] $name 目標目錄已存在，將會覆蓋${NC}"
        rm -rf "$dir"
    fi

    cp -r ./taiwan-invoice "$dir"
    echo -e "${GREEN}[OK] $name 安裝完成${NC}"

    if [ -d "$dir/scripts" ]; then
        chmod +x "$dir/scripts"/*.py 2>/dev/null || true
    fi
}

case $choice in
    1)
        INSTALL_DIR="$HOME/.claude/skills/taiwan-invoice"
        ;;
    2)
        INSTALL_DIR="./.claude/skills/taiwan-invoice"
        ;;
    3)
        INSTALL_DIR="./.cursor/skills/taiwan-invoice"
        ;;
    4)
        INSTALL_DIR="./.agent/skills/taiwan-invoice"
        ;;
    5)
        INSTALL_DIR="$HOME/.gemini/antigravity/global_skills/taiwan-invoice"
        ;;
    6)
        INSTALL_ALL=true
        ;;
    7)
        read -p "請輸入安裝路徑: " CUSTOM_DIR
        INSTALL_DIR="$CUSTOM_DIR/taiwan-invoice"
        ;;
    *)
        echo -e "${RED}[ERROR] 無效的選擇${NC}"
        exit 1
        ;;
esac

if [ "$INSTALL_ALL" = true ]; then
    echo ""
    echo "將安裝到以下位置："
    echo "   - Claude Code:  ./.claude/skills/taiwan-invoice"
    echo "   - Cursor:       ./.cursor/skills/taiwan-invoice"
    echo "   - Antigravity:  ./.agent/skills/taiwan-invoice"
    echo ""

    read -p "確定要安裝嗎？ [y/N]: " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}[CANCEL] 安裝已取消${NC}"
        exit 0
    fi

    echo ""
    echo "開始安裝..."

    install_skill_dir "./.claude/skills/taiwan-invoice" "Claude Code"
    install_skill_dir "./.cursor/skills/taiwan-invoice" "Cursor"
    install_skill_dir "./.agent/skills/taiwan-invoice" "Antigravity"

else
    echo ""
    echo "安裝路徑: $INSTALL_DIR"
    echo ""

    read -p "確定要安裝嗎？ [y/N]: " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}[CANCEL] 安裝已取消${NC}"
        exit 0
    fi

    echo ""
    echo "開始安裝..."

    install_skill_dir "$INSTALL_DIR" "taiwan-invoice"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}[DONE] 安裝完成！${NC}"
echo "=========================================="
echo ""
echo "快速開始："
echo ""
echo "1. 在 Claude Code 中使用："
echo "   輸入 /taiwan-invoice 或在對話中提及電子發票相關主題，Skill 會自動啟用"
echo ""
echo "2. 在 Cursor 中使用："
echo "   輸入 /taiwan-invoice 或在對話中提及電子發票相關主題，Skill 會自動啟用"
echo ""
echo "3. 在 Google Antigravity 中使用："
echo "   直接輸入發票相關指令，Agent 會自動偵測並載入 taiwan-invoice skill"
echo ""
echo "4. 測試金額計算："
echo "   python taiwan-invoice/scripts/test-invoice-amounts.py"
echo ""
echo "完整文檔："
echo "   - README.md - 專案說明與安裝指南"
echo "   - taiwan-invoice/SKILL.md - Skill 核心定義"
echo "   - taiwan-invoice/EXAMPLES.md - 程式碼範例"
echo ""
