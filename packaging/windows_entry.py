"""PyInstaller entry point with Unicode-safe Windows console output."""
import sys
from hyuncalculator.__main__ import main
if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    main()
