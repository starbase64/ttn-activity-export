@echo off
rem Compatibility launcher for existing shortcuts.
call "%~dp0Start-TTN-Activity-Export.cmd" %*
exit /b %errorlevel%
