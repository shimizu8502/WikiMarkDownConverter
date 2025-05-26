@echo off
setlocal enabledelayedexpansion

echo ====================================
echo PukiWiki to Markdown Converter �N��
echo ====================================

:: ���z��������ΗL����
if exist venv (
    echo [���] ���z����L�������Ă��܂�...
    call venv\Scripts\activate.bat
    if %errorlevel% neq 0 (
        echo [�x��] ���z���̗L�����Ɏ��s���܂����B�O���[�o�������g�p���܂��B
    ) else (
        echo [���] ���z�����L��������܂����B
    )
)

:: Python���C���X�g�[������Ă��邩�m�F
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [�G���[] Python��������܂���B
    echo setup_environment.bat���Ɏ��s���Ă��������B
    pause
    exit /b 1
)

:: ���C���v���O���������s
echo [���] PukiWiki to Markdown Converter���N�����Ă��܂�...
echo.
python pukiwiki_to_markdown.py
if %errorlevel% neq 0 (
    echo.
    echo [�G���[] �v���O�����̎��s���ɃG���[���������܂����B
    echo �G���[�R�[�h: %errorlevel%
) else (
    echo.
    echo [���] �v���O����������I�����܂����B
)

:: ���z�����g�p���Ă����ꍇ�͖�����
if exist venv (
    if defined VIRTUAL_ENV (
        call venv\Scripts\deactivate.bat
    )
)

echo.
echo ====================================
echo �I������ɂ͉����L�[�������Ă��������B
echo ====================================
pause 