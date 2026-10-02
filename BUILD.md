# Building Momentum Standalone Executable (.exe)

This guide provides instructions to build a standalone, double-clickable Windows `.exe` that runs on any machine without requiring Python.

---

## 1. Set Up Environment
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. Run in Dev Mode
Verify the app launches properly in dev mode:
```cmd
python main.py
```

---

## 3. Build Standalone .exe with PyInstaller
Run the following build command:
```cmd
pyinstaller --noconfirm --onefile --windowed --name "Momentum" --icon=assets/icon.ico --add-data "assets;assets" main.py
```

### Explanation of Flags:
- `--noconfirm`: Overwrite existing output directories (`build` and `dist`) without asking.
- `--onefile`: Bundles the Python interpreter, modules, and assets into a single self-contained executable.
- `--windowed`: Suppresses the terminal/console window so only the GUI appears.
- `--name "Momentum"`: Sets the output filename to `Momentum.exe`.
- `--icon=assets/icon.ico`: Applies the custom branding icon in Windows File Explorer and taskbar.
- `--add-data "assets;assets"`: Packages the `assets/` folder (including app icons) inside the bundle runtime.

---

## 4. Verification & Testing
1. Navigate to the generated `dist/` directory.
2. Copy ONLY `Momentum.exe` to an external directory (e.g., Desktop or a test folder).
3. Double-click `Momentum.exe` and verify:
   - App launches cleanly without a black console window.
   - All 7 screens (Dashboard, Habit Tracker, Calendar, To-Do, Analytics, Plan Builder, Settings) are accessible and functional.
   - Interactive toggles, modals, and CRUD persist across app restarts.
   - The database file is created and updated in the user-writable location:
     `%LOCALAPPDATA%\Momentum\momentum.db`

---

## 5. Troubleshooting
- **Missing Module Warning**: Add `--hidden-import <modulename>` (e.g. `--hidden-import PIL._tkinter_finder`) if any dynamic import is missed.
- **Antivirus False Positive**: Standard Windows Defender warnings on unsigned onefile PyInstaller executables are common. Add a temporary exception or sign the executable.
- **Custom Icon**: Replace `assets/icon.ico` with your preferred multi-size icon before building.
