"""Headless tests for accessible theme palettes and safe local settings."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hyuncalculator.appearance import (
    AppearancePreferences, PALETTES, THEMES, SCALES,
    contrast_ratio, load_preferences, save_preferences,
)


class AppearanceTests(unittest.TestCase):
    def test_every_theme_has_readable_text_contrast(self):
        for name, palette in PALETTES.items():
            with self.subTest(theme=name):
                for background in ('background', 'surface', 'field'):
                    self.assertGreaterEqual(contrast_ratio(palette['foreground'], palette[background]), 7)
                self.assertGreaterEqual(contrast_ratio(palette['secondary'], palette['background']), 7)
                self.assertGreaterEqual(contrast_ratio(palette['accent_foreground'], palette['accent']), 6.5)
        self.assertEqual(set(THEMES), set(PALETTES))

    def test_settings_validation_rejects_unsafe_or_nonfinite_values(self):
        for bad in ('bad', None, [], 99, {'theme': '__import__("os")', 'font_scale': float('inf')},
                    {'theme': 'dark', 'font_scale': True},
                    {'theme': 42, 'font_scale': -2.0},
                    {'theme': 'nonsense', 'font_scale': '200%'}):
            with self.subTest(value=bad):
                self.assertEqual(AppearancePreferences.parse(bad), AppearancePreferences())
        self.assertEqual(AppearancePreferences.parse({'theme': 'light', 'font_scale': '200%'}),
                         AppearancePreferences('light', 1.25))
        for theme in THEMES:
            for size in SCALES:
                self.assertEqual(AppearancePreferences.parse({'theme': theme, 'font_scale': size}),
                                 AppearancePreferences(theme, size))

    def test_save_load_atomic_and_corrupt_fallback(self):
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / 'settings' / 'appearance.json'
            for prefs in (AppearancePreferences('high-contrast', 1.75),
                          AppearancePreferences('light', 1.0),
                          AppearancePreferences('dark', 1.5)):
                save_preferences(prefs, target)
                self.assertEqual(load_preferences(target), prefs)
                contents = json.loads(target.read_text(encoding='utf-8'))
                self.assertEqual(set(contents), {'theme', 'font_scale'})
            target.write_text('{bad json', encoding='utf-8')
            self.assertEqual(load_preferences(target), AppearancePreferences())
            target.write_bytes(b' ' * 5000)
            self.assertEqual(load_preferences(target), AppearancePreferences())
            self.assertEqual(list(target.parent.glob('.appearance-*.tmp')), [])

    def test_hex_color_guards(self):
        for value in ('red', '#ABC', '#00112233', '#foo012'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                contrast_ratio(value, '#FFFFFF')


if __name__ == '__main__':
    unittest.main()
