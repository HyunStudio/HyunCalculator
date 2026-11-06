from __future__ import annotations
import argparse


def main():
    parser = argparse.ArgumentParser(description='HyunCalculator desktop application')
    parser.add_argument('--classic', action='store_true', help='Open the original Tk desktop interface')
    parser.add_argument('--browser', action='store_true', help='Open the responsive interface in a browser')
    parser.add_argument('--lang', choices=('ko','en'), default='ko')
    parser.add_argument('--test', action='store_true', help='Run project unit tests (headless)')
    parser.add_argument('--list-formulas', action='store_true', help='List all 33 formula IDs and availability')
    parser.add_argument('--generate', metavar='FORMULA_ID', help='Generate code for a registered formula')
    parser.add_argument('--language', default='Python', help='Code output language')
    parser.add_argument('--structure', choices=('function','class'), default='function')
    parser.add_argument('--loop', choices=('auto','for','while'), default='auto')
    parser.add_argument('--variant', choices=('periodic','continuous'), default='periodic')
    parser.add_argument('--imports', choices=('auto','standard'), default='auto')
    parser.add_argument('--function-name', help='Generated function name')
    parser.add_argument('--class-name', default='GeneratedCalculator', help='Name for class structure')
    parser.add_argument('--rename', metavar='OLD=NEW', action='append', default=[], help='Rename a canonical input parameter')
    parser.add_argument('--output', metavar='PATH', help='Write generated UTF-8 source file; otherwise print to stdout')
    parser.add_argument('--bundle', metavar='ZIP_PATH', help='Export source, manifest and offline integrity tests as a ZIP project')
    args = parser.parse_args()
    if args.bundle and args.output:
        parser.error('--bundle and --output cannot be used together')
    if args.bundle and not args.generate:
        parser.error('--bundle requires --generate FORMULA_ID')
    if args.test:
        import unittest
        import pathlib
        tests = pathlib.Path(__file__).resolve().parent.parent / 'tests'
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(tests)))
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if args.list_formulas or args.generate:
        from .codegen import catalog, generate, GenerationOptions, GenerationError
        if args.list_formulas:
            for item in catalog():
                print(f'{item.id}  {", ".join(item.supported_languages)}  {item.title_en}')
            return
        try:
            renames=[]
            for pair in args.rename:
                if '=' not in pair: raise GenerationError('--rename requires OLD=NEW')
                original,new=(s.strip() for s in pair.split('=',1))
                renames.append((original,new))
            options = GenerationOptions(language=args.language,
                structure=args.structure, iteration=args.loop, imports=args.imports,
                variant=args.variant, function_name=args.function_name,
                class_name=args.class_name,variable_names=tuple(renames))
            code = generate(args.generate, options)
        except GenerationError as exc:
            parser.error(str(exc))
        if args.bundle:
            from pathlib import Path
            from .codegen.bundle import bundle_bytes
            try:
                Path(args.bundle).write_bytes(bundle_bytes(args.generate, options))
            except (OSError, GenerationError) as exc:
                parser.error(str(exc))
            print(f'Project ZIP: {args.bundle}')
        elif args.output:
            from pathlib import Path
            Path(args.output).write_text(code, encoding='utf-8')
            print(f'Generated: {args.output}')
        else:
            print(code, end='')
        return
    if args.classic:
        from .gui import run_gui
        run_gui(args.lang)
    else:
        from .modern import run_modern
        run_modern(args.lang, browser=args.browser)


if __name__ == '__main__':
    main()
