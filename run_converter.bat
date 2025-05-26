@echo off
setlocal enabledelayedexpansion

echo ====================================
echo PukiWiki to Markdown Converter 起動
echo ====================================

:: 仮想環境があれば有効化
if exist venv (
    echo [情報] 仮想環境を有効化しています...
    call venv\Scripts\activate.bat
    if %errorlevel% neq 0 (
        echo [警告] 仮想環境の有効化に失敗しました。グローバル環境を使用します。
    ) else (
        echo [情報] 仮想環境が有効化されました。
    )
)

:: Pythonがインストールされているか確認
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [エラー] Pythonが見つかりません。
    echo setup_environment.batを先に実行してください。
    pause
    exit /b 1
)

:: メインプログラムを実行
echo [情報] PukiWiki to Markdown Converterを起動しています...
echo.
python pukiwiki_to_markdown.py
if %errorlevel% neq 0 (
    echo.
    echo [エラー] プログラムの実行中にエラーが発生しました。
    echo エラーコード: %errorlevel%
) else (
    echo.
    echo [情報] プログラムが正常終了しました。
)

:: 仮想環境を使用していた場合は無効化
if exist venv (
    if defined VIRTUAL_ENV (
        call venv\Scripts\deactivate.bat
    )
)

echo.
echo ====================================
echo 終了するには何かキーを押してください。
echo ====================================
pause 