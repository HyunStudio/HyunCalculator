# HyunCalculator shared UI and platform status

The default interface is the IntelliJ / financial-workbench design: charcoal
surfaces, a calculator explorer, editor-style workspace, purple selection and
mint numerical results. Korean and English, search, local history, light/dark
themes and a mobile navigation drawer share the same HTML/CSS/JavaScript.
No CDN, remote font, analytics or hosted calculation API is required.

## Desktop

Install `requirements-desktop.txt` and run `python -m hyuncalculator`.
The native window hosts the shared UI and uses the original Python calculator
engine. If a native webview is unavailable, the same UI opens in a browser.
`--browser` explicitly opens the browser. `--classic` retains the Tk interface.

Windows, Linux and macOS use the same code. Automated packaging jobs produce
platform artifacts; this does not replace interactive acceptance testing on
each operating system. Windows EXE startup, scientific calculation and code
generation were checked locally. The local build uses Windows x64/Python 3.14;
the Windows CI build uses Python 3.12. Native webview startup may depend on
system webview packages; the browser fallback remains available.

Build Windows with `./packaging/build_windows.ps1` after installing PyInstaller
and desktop requirements. Linux/macOS: `python packaging/build_desktop.py`.
CI artifacts are unsigned development builds, not store installers.

## Android / mobile

`hyuncalculator/webui/` is a static, installable PWA foundation. Deploy its
contents on HTTPS to install from an Android browser. It includes a manifest,
192/512px icons, a service worker and offline assets. The localhost development
server is only accessible on the current computer, not from an Android phone.
No public hosting or app-store submission has been performed.

The mobile layout was checked at 390 x 844 pixels without horizontal overflow.
The standalone offline mode supports all 33 financial/quantitative formulas,
real-valued scientific expressions, graphs and default JavaScript source
export. The Python-backed desktop adds all 57 registered form calculators,
including the 19 ML/DL/RL and five programmer calculations, full scientific
features and advanced code-generation options. Those extra Python features
have NOT been ported to Android offline mode. Complex scientific expressions
on mobile, a signed Android APK/AAB, physical-device testing and store releases
remain open. A PWA layout is not an Android native binary.

## Verification

`python -m unittest discover -s tests -v` includes all 57 form-calculator routes,
Unicode/nonfinite/large-integer JSON handling, local HTTP origin checks,
checked-in offline-source parity and the offline scientific parser.
The browser checks covered scientific evaluation (4.5), Black–Scholes price
(10.4505835722), navigation, desktop/mobile layout and default code generation.
History is stored on the current device. It is not synchronized or uploaded.

Before editing emitted formula code, run `python tools/export_web_catalog.py`
to regenerate the offline copies and catalog metadata.
