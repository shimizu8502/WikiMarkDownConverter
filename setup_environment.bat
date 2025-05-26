@echo off
setlocal enabledelayedexpansion

echo ====================================
echo PukiWiki to Markdown Converter セットアップ
echo ====================================

:: Pythonがインストールされているか確認
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [エラー] Pythonが見つかりません。
    echo Python 3.xをhttps://www.python.org/downloads/からインストールしてください。
    pause
    exit /b 1
)

:: Pythonのバージョンを確認
for /f "tokens=2" %%a in ('python --version 2^>^&1') do set "python_version=%%a"
echo [情報] Python %python_version% が検出されました。

:: 仮想環境の作成（オプション）
if exist venv (
    echo [情報] 既存の仮想環境が見つかりました。
) else (
    echo [情報] 仮想環境を作成しています...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [警告] 仮想環境の作成に失敗しました。グローバル環境を使用します。
    ) else (
        echo [情報] 仮想環境が作成されました。
    )
)

:: 必要なディレクトリの作成
if not exist logs (
    mkdir logs
    echo [情報] ログディレクトリを作成しました。
)

echo.
echo ====================================
echo セットアップが完了しました！
echo 「run_converter.bat」を実行してアプリケーションを起動してください。
echo ====================================
pause 