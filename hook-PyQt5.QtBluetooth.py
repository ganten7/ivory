# PyInstaller hook to exclude QtBluetooth framework
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

# Exclude QtBluetooth completely
excludedimports = ['PyQt5.QtBluetooth']

# Don't collect any binaries for QtBluetooth
binaries = []

# Don't collect any data files
datas = []






