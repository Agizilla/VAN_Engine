@echo off
echo ============================================================
echo 3D Face Avatar - Python 3.13 Compatibility Fix
echo ============================================================
echo.

echo Checking Python version...
python --version
echo.

echo Running automatic fix...
python fix_python313.py

echo.
echo ============================================================
echo Fix complete!
echo.
echo To run the application, use:
echo   python face_avatar_3d.py
echo ============================================================
echo.
pause
