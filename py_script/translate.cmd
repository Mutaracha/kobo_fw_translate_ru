@echo off
setlocal
pushd "%~dp0.." || exit /b 1
py -3 -c "import sys" >nul 2>&1
if errorlevel 1 goto python
py -3 "py_script\translate_menu.py"
goto end
:python
python -c "import sys; sys.exit(sys.version_info.major != 3)" >nul 2>&1
if errorlevel 1 goto missing
python "py_script\translate_menu.py"
:end
set "rc=%errorlevel%"
popd
exit /b %rc%
:missing
echo Python 3 is required. Install Python and run this launcher again.
pause
popd
exit /b 1
