#!/usr/bin/env python3
"""
PyInstaller build script for Marketing Manager
Builds a standalone executable for Windows/Mac.
"""
import os
import sys
import shutil
import PyInstaller.__main__

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(APP_DIR, 'dist')
BUILD_DIR = os.path.join(APP_DIR, 'build')
ICON_PATH = os.path.join(APP_DIR, 'icon', 'arc_reactor.png')


def clean():
    """Remove previous build artifacts."""
    for d in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d)
    print("Cleaned previous build directories.")


def build_windows():
    """Build for Windows (primary)."""
    print("Building for Windows...")
    PyInstaller.__main__.run([
        os.path.join(APP_DIR, 'Marketing Manager.spec'),
        '--name=Marketing Manager',
        '--distpath=dist',
        '--workpath=build',
        '--icon=' + ICON_PATH,
        '--windowed',
        '--add-data=icon:icon',
        '--add-data=templates:templates',
        '--add-data=static:static',
        '--hidden-import=flask',
        '--hidden-import=werkzeug',
        '--hidden-import=jinja2',
        '--hidden-import=sqlite3',
        '--hidden-import=json',
        '--hidden-import=csv',
        '--hidden-import=threading',
        '--collect-all=markupsafe',
        '--collect-all=jinja2',
        '--noconfirm',
    ])


def build_macos():
    """Build for macOS."""
    print("Building for macOS...")
    PyInstaller.__main__.run([
        os.path.join(APP_DIR, 'Marketing Manager.spec'),
        '--name=Marketing Manager',
        '--distpath=dist',
        '--workpath=build',
        '--icon=' + ICON_PATH,
        '--add-data=icon:icon',
        '--add-data=templates:templates',
        '--add-data=static:static',
        '--hidden-import=flask',
        '--hidden-import=werkzeug',
        '--hidden-import=jinja2',
        '--hidden-import=sqlite3',
        '--hidden-import=json',
        '--hidden-import=csv',
        '--hidden-import=threading',
        '--collect-all=markupsafe',
        '--collect-all=jinja2',
        '--noconfirm',
    ])


def main():
    if len(sys.argv) < 2:
        print("Usage: python build.py [clean|windows|macos|all]")
        return

    cmd = sys.argv[1].lower()
    if cmd == 'clean':
        clean()
    elif cmd == 'windows':
        clean()
        build_windows()
    elif cmd == 'macos':
        clean()
        build_macos()
    elif cmd == 'all':
        clean()
        build_windows()
        build_macos()
    else:
        print(f"Unknown command: {cmd}")


if __name__ == '__main__':
    main()
