import sys

from cx_Freeze import Executable, setup

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"
	
includefiles = [('Logs\\', 'Logs\\'), ('Images\\', 'Images\\'), ('UI\\', 'UI\\'), ('Library\\', 'Library\\'), 
				 'Plots\\', 'Reports\\' ,'requirements.txt', 'qt.conf']
includes = ['atexit', 'PyQt5']
excludes = ['Tkinter', 'PyQt5.uic.port_v2']
packages = ['idna', 'requests', 'plotly','pkg_resources', 'packaging']


import os
os.environ['TCL_LIBRARY'] = r'C:\Users\ALF\Anaconda3\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\ALF\Anaconda3\tcl\tk8.6'
setup(  name = "TempReaderApp",
		author="ALF",
		author_email="alf@this.com",
        version = "0.1",
        description = "Reagent Carousel Temperature Reader",
        options = {'build_exe': {'includes':includes,'excludes':excludes,'packages':packages,'include_files':includefiles}},
		executables = [Executable("TempReaderApp.py", icon='Images\\ThermometerIcon.ico', base = "Win32GUI")])
		
# cxfreeze hello.py --target-dir dist --icon=ICON
# python setup.py bdist_msi
# options = {"build_exe": build_exe_options},
# python.exe cxfreeze-postinstall
# remove port_V2 from uic from uic
#options = {
#   'build_exe': {'includes': ['atexit', 'PyQt5'], 'excludes': 'PyQt5.uic.port_v2',
#				  'packages': ['idna', 'requests', 'plotly','pkg_resources', 'packaging'],
#				  'include_files': [('Logs\\', 'Logs\\'), ('Images\\', 'Images\\'), ('UI\\', 'UI\\'), ('Library\\', 'Library\\'), 
#				  'Plots\\', 'Reports\\' ,'requirements.txt', 'qt.conf']
#	}
#}