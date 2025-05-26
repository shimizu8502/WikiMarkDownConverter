@echo off
setlocal enabledelayedexpansion

echo ====================================
echo PukiWiki to Markdown Converter �Z�b�g�A�b�v
echo ====================================

:: Python���C���X�g�[������Ă��邩�m�F
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [�G���[] Python��������܂���B
    echo Python 3.x��https://www.python.org/downloads/����C���X�g�[�����Ă��������B
    pause
    exit /b 1
)

:: Python�̃o�[�W�������m�F
for /f "tokens=2" %%a in ('python --version 2^>^&1') do set "python_version=%%a"
echo [���] Python %python_version% �����o����܂����B

:: ���z���̍쐬�i�I�v�V�����j
if exist venv (
    echo [���] �����̉��z����������܂����B
) else (
    echo [���] ���z�����쐬���Ă��܂�...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [�x��] ���z���̍쐬�Ɏ��s���܂����B�O���[�o�������g�p���܂��B
    ) else (
        echo [���] ���z�����쐬����܂����B
    )
)

:: �K�v�ȃf�B���N�g���̍쐬
if not exist logs (
    mkdir logs
    echo [���] ���O�f�B���N�g�����쐬���܂����B
)

echo.
echo ====================================
echo �Z�b�g�A�b�v���������܂����I
echo �urun_converter.bat�v�����s���ăA�v���P�[�V�������N�����Ă��������B
echo ====================================
pause 