@echo off
REM Taiwan Invoice Claude Skills - 安裝腳本 (Windows)
setlocal enabledelayedexpansion

echo ============================================
echo Taiwan Invoice Claude Skills 安裝程式
echo ============================================
echo.

REM 確認來源目錄存在
if not exist "taiwan-invoice" (
    echo [ERROR] 找不到 taiwan-invoice 目錄，請在專案根目錄執行此腳本
    exit /b 1
)

REM 詢問安裝位置
echo 請選擇安裝位置：
echo 1) Claude Code 全域 (%%USERPROFILE%%\.claude\skills\)
echo 2) 當前專案 - Claude Code (.\.claude\skills\)
echo 3) Cursor - 專案 (.\.cursor\skills\)
echo 4) Google Antigravity - 專案 (.\.agent\skills\)
echo 5) Google Antigravity - 全域 (%%USERPROFILE%%\.gemini\antigravity\global_skills\)
echo 6) 全部安裝（Claude Code + Cursor + Antigravity）
echo 7) 自訂路徑
echo.

set /p choice="請選擇 [1-7]: "

if "%choice%"=="6" goto install_all

if "%choice%"=="1" (
    set "INSTALL_DIR=%USERPROFILE%\.claude\skills\taiwan-invoice"
) else if "%choice%"=="2" (
    set "INSTALL_DIR=%CD%\.claude\skills\taiwan-invoice"
) else if "%choice%"=="3" (
    set "INSTALL_DIR=%CD%\.cursor\skills\taiwan-invoice"
) else if "%choice%"=="4" (
    set "INSTALL_DIR=%CD%\.agent\skills\taiwan-invoice"
) else if "%choice%"=="5" (
    set "INSTALL_DIR=%USERPROFILE%\.gemini\antigravity\global_skills\taiwan-invoice"
) else if "%choice%"=="7" (
    set /p CUSTOM_DIR="請輸入安裝路徑: "
    set "INSTALL_DIR=!CUSTOM_DIR!\taiwan-invoice"
) else (
    echo [ERROR] 無效的選擇
    exit /b 1
)

echo.
echo 安裝路徑: %INSTALL_DIR%
echo.

set /p confirm="確定要安裝嗎？ [y/N]: "
if /i not "%confirm%"=="y" (
    echo [CANCEL] 安裝已取消
    exit /b 0
)

echo.
echo 開始安裝...

call :install_single "%INSTALL_DIR%" "taiwan-invoice"
goto finish

:install_all
echo.
echo 將安裝到以下位置：
echo    - Claude Code:  .\.claude\skills\taiwan-invoice
echo    - Cursor:       .\.cursor\skills\taiwan-invoice
echo    - Antigravity:  .\.agent\skills\taiwan-invoice
echo.

set /p confirm="確定要安裝嗎？ [y/N]: "
if /i not "%confirm%"=="y" (
    echo [CANCEL] 安裝已取消
    exit /b 0
)

echo.
echo 開始安裝...

call :install_single "%CD%\.claude\skills\taiwan-invoice" "Claude Code"
call :install_single "%CD%\.cursor\skills\taiwan-invoice" "Cursor"
call :install_single "%CD%\.agent\skills\taiwan-invoice" "Antigravity"
goto finish

:install_single
set "TARGET_DIR=%~1"
set "TARGET_NAME=%~2"

REM 建立父目錄
for %%I in ("%TARGET_DIR%") do set "PARENT_DIR=%%~dpI"
if not exist "%PARENT_DIR%" mkdir "%PARENT_DIR%"

REM 刪除舊版本
if exist "%TARGET_DIR%" (
    echo [WARNING] %TARGET_NAME% 目標目錄已存在，將會覆蓋
    rmdir /s /q "%TARGET_DIR%"
)

REM 複製檔案
xcopy /E /I /Y "taiwan-invoice" "%TARGET_DIR%" >nul

if %errorlevel% neq 0 (
    echo [ERROR] %TARGET_NAME% 檔案複製失敗
    exit /b 1
)

echo [OK] %TARGET_NAME% 安裝完成
exit /b 0

:finish
echo.
echo ============================================
echo [DONE] 安裝完成！
echo ============================================
echo.
echo 快速開始：
echo.
echo 1. 在 Claude Code 中使用：
echo    輸入 /taiwan-invoice 或在對話中提及電子發票相關主題，Skill 會自動啟用
echo.
echo 2. 在 Cursor 中使用：
echo    輸入 /taiwan-invoice 或在對話中提及電子發票相關主題，Skill 會自動啟用
echo.
echo 3. 在 Google Antigravity 中使用：
echo    直接輸入發票相關指令，Agent 會自動偵測並載入 taiwan-invoice skill
echo.
echo 4. 測試金額計算：
echo    python taiwan-invoice\scripts\test-invoice-amounts.py
echo.
echo 完整文檔：
echo    - README.md - 專案說明與安裝指南
echo    - taiwan-invoice\SKILL.md - Skill 核心定義
echo    - taiwan-invoice\EXAMPLES.md - 程式碼範例
echo.

pause
