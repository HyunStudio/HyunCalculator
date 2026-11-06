"""Accessible, local-only appearance settings for the Tk desktop frontend.

This module does not alter finance functions or execute generated user code.
Settings are optional and are validated before applying to Tk widgets.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import font as tkfont, ttk

THEMES = ('dark', 'light', 'high-contrast')
SCALES = (1.0, 1.25, 1.5, 1.75)

PALETTES = {
    'dark': {
        'background': '#0B1627', 'surface': '#14243A', 'field': '#1C3047',
        'foreground': '#F3F7FF', 'secondary': '#CDD9E8', 'border': '#52728C',
        'accent': '#64E3CC', 'accent_foreground': '#08261F',
        'selected': '#315A78', 'focus': '#FFE58B', 'grid': '#6D90A8',
    },
    'light': {
        'background': '#EEF3F9', 'surface': '#FFFFFF', 'field': '#FFFFFF',
        'foreground': '#16283C', 'secondary': '#324A60', 'border': '#73879B',
        'accent': '#005D69', 'accent_foreground': '#FFFFFF',
        'selected': '#D5ECF3', 'focus': '#9A4B00', 'grid': '#6F8497',
    },
    'high-contrast': {
        'background': '#000000', 'surface': '#000000', 'field': '#101010',
        'foreground': '#FFFFFF', 'secondary': '#FFFFFF', 'border': '#FFFFFF',
        'accent': '#FFE500', 'accent_foreground': '#000000',
        'selected': '#363600', 'focus': '#FFE500', 'grid': '#FFFFFF',
    },
}


@dataclass(frozen=True)
class AppearancePreferences:
    theme: str = 'dark'
    font_scale: float = 1.25

    @classmethod
    def parse(cls, value: object) -> 'AppearancePreferences':
        if not isinstance(value, dict):
            return cls()
        theme = value.get('theme')
        scale = value.get('font_scale')
        if theme not in THEMES:
            theme = cls.theme
        if isinstance(scale, bool) or not isinstance(scale, (float, int)):
            scale = cls.font_scale
        elif not math.isfinite(scale) or not any(abs(scale - v) < 1e-9 for v in SCALES):
            scale = cls.font_scale
        return cls(theme, float(scale))


def settings_path() -> Path:
    return Path.home() / '.hyuncalculator' / 'appearance.json'


def load_preferences(path: Path | None = None) -> AppearancePreferences:
    target = path if path is not None else settings_path()
    try:
        if target.stat().st_size > 4096:
            return AppearancePreferences()
        return AppearancePreferences.parse(json.loads(target.read_text(encoding='utf-8')))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return AppearancePreferences()


def save_preferences(prefs: AppearancePreferences, path: Path | None = None) -> None:
    """Atomically persist only allowlisted appearance values to a local file."""
    checked = AppearancePreferences.parse({'theme': prefs.theme, 'font_scale': prefs.font_scale})
    target = path if path is not None else settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=target.parent, prefix='.appearance-',
                                         suffix='.tmp', delete=False) as handle:
            temp_path = Path(handle.name)
            json.dump({'theme': checked.theme, 'font_scale': checked.font_scale}, handle,
                      sort_keys=True, ensure_ascii=False)
            handle.write('\n')
        if os.name != 'nt':
            temp_path.chmod(0o600)
        temp_path.replace(target)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG relative luminance contrast, for palette regression testing."""
    def luminance(value: str) -> float:
        s = value.lstrip('#')
        if len(s) != 6 or any(c not in '0123456789abcdefABCDEF' for c in s):
            raise ValueError('Expected a six-digit hex color')
        rgb = [int(s[i:i+2], 16) / 255 for i in (0, 2, 4)]
        linear = [x / 12.92 if x <= 0.04045 else ((x+0.055)/1.055)**2.4 for x in rgb]
        return 0.2126*linear[0] + 0.7152*linear[1] + 0.0722*linear[2]
    a, b = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (a + 0.05)/(b + 0.05)


def _walk(widget: tk.Misc):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


def _set_scaled_font(widget: tk.Misc, size_multiplier: float) -> None:
    try:
        if 'font' not in widget.keys():
            return
        if not hasattr(widget, '_hyun_base_font'):
            f = tkfont.Font(root=widget, font=widget.cget('font'))
            widget._hyun_base_font = f.actual()
        props = widget._hyun_base_font
        size = abs(int(props['size']))
        if size < 1:
            return
        scaled = tkfont.Font(root=widget, family=props['family'],
                             size=max(9, round(size*size_multiplier)),
                             weight=props['weight'], slant=props['slant'],
                             underline=props['underline'], overstrike=props['overstrike'])
        widget._hyun_scaled_font = scaled  # Retain Tcl font resource
        widget.configure(font=scaled)
    except (tk.TclError, TypeError, ValueError):
        # Some platform-specific widgets report a read-only or invalid font.
        pass


def apply_appearance(root: tk.Tk, style: ttk.Style,
                     prefs: AppearancePreferences) -> dict[str, str]:
    """Restyle existing Tk/ttk widget tree; safe to call repeatedly."""
    prefs = AppearancePreferences.parse({'theme': prefs.theme, 'font_scale': prefs.font_scale})
    p = PALETTES[prefs.theme]
    if 'clam' in style.theme_names() and style.theme_use() != 'clam':
        style.theme_use('clam')
    root.configure(background=p['background'])
    scale = prefs.font_scale
    family = 'Malgun Gothic'
    mono = 'Consolas'

    for name, background in [('TFrame', p['background']), ('Surface.TFrame', p['surface']),
                             ('TLabel', p['background']), ('TCheckbutton', p['background']),
                             ('TRadiobutton', p['background'])]:
        style.configure(name, background=background, foreground=p['foreground'])
    style.configure('TLabel', font=(family, round(12*scale)), padding=2)
    style.configure('Result.TLabel', background=p['surface'], foreground=p['foreground'])
    style.configure('TButton', background=p['surface'], foreground=p['foreground'],
                    bordercolor=p['border'], relief='flat', focuscolor=p['focus'],
                    font=(family, round(12*scale), 'bold'), padding=(11, 8))
    style.map('TButton', background=[('pressed', p['accent']), ('active', p['field']),
                                     ('disabled', p['surface'])],
              foreground=[('pressed', p['accent_foreground']),
                          ('disabled', p['secondary'])])
    style.configure('TEntry', fieldbackground=p['field'], foreground=p['foreground'],
                    bordercolor=p['border'], insertcolor=p['foreground'],
                    font=(mono, round(12*scale)), padding=(7, 6))
    style.configure('TCombobox', fieldbackground=p['field'], foreground=p['foreground'],
                    background=p['surface'], arrowcolor=p['foreground'],
                    bordercolor=p['border'], font=(family, round(11*scale)), padding=(5, 5))
    style.map('TCombobox', fieldbackground=[('readonly', p['field'])],
              foreground=[('readonly', p['foreground'])],
              selectbackground=[('readonly', p['field'])],
              selectforeground=[('readonly', p['foreground'])])
    style.configure('TNotebook', background=p['background'], borderwidth=0)
    style.configure('TNotebook.Tab', background=p['surface'], foreground=p['foreground'],
                    bordercolor=p['border'], focuscolor=p['focus'],
                    font=(family, round(12*scale), 'bold'), padding=(13, 9))
    style.map('TNotebook.Tab', background=[('selected', p['selected']),
                                            ('active', p['field'])],
              foreground=[('selected', p['foreground'])])
    style.configure('TScrollbar', background=p['field'], troughcolor=p['background'],
                    arrowcolor=p['foreground'])
    style.configure('TLabelFrame', background=p['background'], foreground=p['foreground'])
    style.configure('TLabelFrame.Label', background=p['background'], foreground=p['foreground'])
    style.configure('Treeview', background=p['field'], fieldbackground=p['field'],
                    foreground=p['foreground'], rowheight=round(30*scale))
    style.map('Treeview', background=[('selected', p['selected'])],
              foreground=[('selected', p['foreground'])])

    root.option_add('*TCombobox*Listbox.background', p['field'])
    root.option_add('*TCombobox*Listbox.foreground', p['foreground'])
    root.option_add('*TCombobox*Listbox.selectBackground', p['selected'])
    root.option_add('*TCombobox*Listbox.selectForeground', p['foreground'])

    for widget in _walk(root):
        if widget.winfo_class() in ('Text', 'Listbox', 'Entry', 'Spinbox'):
            try:
                widget.configure(background=p['field'], foreground=p['foreground'],
                                 insertbackground=p['foreground'],
                                 selectbackground=p['selected'],
                                 selectforeground=p['foreground'],
                                 highlightcolor=p['focus'],
                                 highlightbackground=p['border'])
            except tk.TclError:
                # A listbox has no insertion cursor on some Tk builds.
                widget.configure(background=p['field'], foreground=p['foreground'],
                                 selectbackground=p['selected'],
                                 selectforeground=p['foreground'])
        elif widget.winfo_class() in ('Frame', 'Canvas'):
            widget.configure(background=p['surface'])
        elif isinstance(widget, (tk.Button, tk.Label, tk.Checkbutton, tk.Radiobutton)):
            widget.configure(background=p['surface'], foreground=p['foreground'],
                             activebackground=p['selected'], activeforeground=p['foreground']) if not isinstance(widget, tk.Label) else widget.configure(background=p['surface'], foreground=p['foreground'])
        _set_scaled_font(widget, scale)
    return p
