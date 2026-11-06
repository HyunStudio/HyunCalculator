"""Portable packager for the shared Windows, Linux and macOS application."""
import os
import subprocess
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--name','HyunCalculator','--paths',str(root),'--collect-all','matplotlib','--collect-all','webview','--add-data',str(root/'hyuncalculator'/'webui')+os.pathsep+'hyuncalculator/webui','--distpath',str(root/'dist'),'--workpath',str(root/'work'/'pyinstaller'),'--specpath',str(root/'work')]
if sys.platform=='darwin':command+=['--windowed']
command+=[str(root/'packaging'/'windows_entry.py')]
subprocess.run(command,cwd=root,check=True)
