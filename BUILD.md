# Building Momentum

## 1. Set up environment
```
python -m venv venv
venv\Scripts\activate          (Windows)
pip install -r requirements.txt
```

## 2. Run in dev mode first to verify everything works
```
python main.py
```

## 3. Build the standalone exe
```
pyinstaller --noconfirm --onefile --windowed --name "Momentum" --icon=assets/icon.ico --add-data "assets;assets" main.py
```

### What each flag does
- `--onefile`: bundles everything (Python interpreter, libraries, assets) into a single .exe file
- `--windowed`: suppresses the console/terminal window since this is a GUI app (without this, a black console window would appear behind the app)
- `--name "Momentum"`: sets the output exe's filename
- `--icon=assets/icon.ico`: sets the custom app icon shown in the taskbar/title bar instead of the default Python icon
- `--add-data "assets;assets"`: bundles the assets folder (icon, any images/fonts) into the exe so they're available at runtime, not just in the dev folder
  (on macOS/Linux the separator is a colon: `"assets:assets"`)

## 4. Test the exe properly (do not skip this step)
- Go to the `dist/` folder created by PyInstaller
- Copy ONLY the Momentum.exe file (not the whole project folder) to a completely different location, e.g. Desktop or a USB drive folder
- Double-click it there and confirm:
  - It launches without any console window or error popup
  - All screens are visible and functional
  - You can add/edit/delete data and it persists if you close and reopen the exe
  - The database file was created in the correct writable location (check %LOCALAPPDATA%\Momentum)

## 5. If it fails
- "Missing module" errors: add `--hidden-import modulename` to the PyInstaller command
- "File not found" errors for assets: double check `get_asset_path()` is used everywhere instead of relative paths
- Antivirus flags the exe: this is common and expected for PyInstaller onefile builds; it's a false positive, not a real issue with the code

## Path resolution note (why it works in the exe)
`utils/path_helper.py` distinguishes dev mode from frozen mode:
- `get_base_path()` → `sys._MEIPASS` when frozen (bundled read-only assets)
- `get_writable_data_path()` → `%LOCALAPPDATA%\Momentum` when frozen (DB never written into the bundle)
- `get_db_path()` / `get_asset_path()` are used everywhere instead of hardcoded relative paths

## Icon
`assets/icon.ico` is a generated placeholder (progress-ring motif).
Replace it with a real designed icon before final submission — a custom icon
makes the final exe feel far more professional than the default Python icon.
