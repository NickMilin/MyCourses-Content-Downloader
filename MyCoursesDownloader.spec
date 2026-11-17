# PyInstaller build recipe. Build with:  pyinstaller MyCoursesDownloader.spec
# Output: dist/MyCoursesDownloader (dist/MyCoursesDownloader.exe on Windows)
from PyInstaller.utils.hooks import collect_all

datas = [("static", "static")]
binaries = []
hiddenimports = []

# nicegui ships its web assets as data files, and selenium ships the
# selenium-manager helper that downloads the matching chromedriver.
for package in ("nicegui", "selenium"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MyCoursesDownloader",
    console=True,  # keep the console: it shows progress and any errors
    upx=False,
)
