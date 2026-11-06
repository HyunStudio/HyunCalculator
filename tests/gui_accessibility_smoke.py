"""Interactive Tk accessibility smoke: use xvfb-run -a python tests/gui_accessibility_smoke.py.

No network or saved account setting changes; temporary appearance path only.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont, ttk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hyuncalculator.gui import run_gui
from hyuncalculator.appearance import PALETTES, AppearancePreferences, load_preferences


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        pref_path = Path(tmp) / 'appearance.json'
        root = run_gui('en', start_mainloop=False, appearance_path=pref_path)
        try:
            root.update_idletasks()
            assert isinstance(root, tk.Tk)
            theme = root.hyuncalculator_theme_choice
            size = root.hyuncalculator_size_choice
            theme.set('high-contrast')
            size.set('175%')
            root.hyuncalculator_apply_preferences()
            root.update_idletasks()
            self_prefs = load_preferences(pref_path)
            assert self_prefs == AppearancePreferences('high-contrast', 1.75), self_prefs
            texts = [w for w in descendants(root) if isinstance(w, tk.Text)]
            assert len(texts) >= 3, [w.winfo_class() for w in texts]
            assert all(w.cget('foreground').lower() == '#ffffff' for w in texts), 'High contrast text palette mismatch'
            assert all(w.cget('background').lower() == '#101010' for w in texts), 'High contrast editor background mismatch'
            notebook = next(w for w in descendants(root) if isinstance(w, ttk.Notebook))
            assert notebook.index('end') == 10, f'Expected ten calculator tabs, got {notebook.index("end")}'
            # Font increase should exceed the baseline editor size and not compound after repeated calls.
            sizes = [tkfont.Font(root=root, font=w.cget('font')).actual()['size'] for w in texts]
            root.hyuncalculator_apply_preferences()
            again = [tkfont.Font(root=root, font=w.cget('font')).actual()['size'] for w in texts]
            assert sizes == again, f'Font size compounded: {sizes} -> {again}'
            theme.set('dark')
            size.set('100%')
            root.hyuncalculator_apply_preferences()
            assert load_preferences(pref_path) == AppearancePreferences('dark', 1.0)
            root.update_idletasks()
            for w in texts:
                assert w.cget('foreground').lower() == PALETTES['dark']['foreground'].lower()
            print('PASS Tk: 10 tabs; high-contrast; 175% font; persistence; no font compounding; dark-theme toggle', flush=True)
        finally:
            root.destroy()


if __name__ == '__main__':
    main()
