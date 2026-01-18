@echo off
echo Installing/updating PyInstaller...
python -m pip install --upgrade pyinstaller

echo Building KidLangIDE executable...
pyinstaller --onefile --windowed --name KidLangIDE kidlang_ide.py

echo Build complete! Check the dist folder for KidLangIDE.exe