Write-Host "Installing/updating PyInstaller..."
python -m pip install --upgrade pyinstaller

Write-Host "Building KidLangIDE executable..."
pyinstaller --onefile --windowed --name KidLangIDE kidlang_ide.py

Write-Host "Build complete! Check the dist folder for KidLangIDE.exe"