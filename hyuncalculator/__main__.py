from __future__ import annotations
import argparse


def main():
    parser = argparse.ArgumentParser(description='HyunCalculator desktop application')
    parser.add_argument('--lang', choices=('ko','en'), default='ko')
    parser.add_argument('--test', action='store_true', help='Run project unit tests (headless)')
    args = parser.parse_args()
    if args.test:
        import unittest
        import pathlib
        tests = pathlib.Path(__file__).resolve().parent.parent / 'tests'
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(tests)))
        raise SystemExit(0 if result.wasSuccessful() else 1)
    from .gui import run_gui
    run_gui(args.lang)


if __name__ == '__main__':
    main()
