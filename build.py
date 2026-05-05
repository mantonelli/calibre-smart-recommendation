#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build script: empacota o plugin para instalação no Calibre.
Uso: python build.py [--output DIR]
"""

import argparse
import ast
import os
import struct
import sys
import zipfile
import zlib

PLUGIN_FILES = [
    '__init__.py',
    'engine.py',
    'ui.py',
    'config.py',
    'plugin-import-name-recommender.txt',
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def create_icon():
    """Gera ícone de livro 32×32 PNG usando apenas stdlib."""
    W, H = 32, 32

    BG     = (235, 235, 235)
    SPINE  = (45,  35, 110)
    COVER  = (70,  55, 155)
    PAGE   = (248, 244, 230)
    LINE   = (185, 175, 150)
    BORDER = (25,  18,  75)

    px = [[BG] * W for _ in range(H)]

    def fill(r1, c1, r2, c2, color):
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if 0 <= r < H and 0 <= c < W:
                    px[r][c] = color

    fill(2, 5, 29, 26, COVER)
    fill(2, 5, 29,  9, SPINE)
    fill(3, 22, 28, 26, PAGE)

    for r in range(2, 30):
        px[r][5]  = BORDER
        px[r][26] = BORDER
    for c in range(5, 27):
        px[2][c]  = BORDER
        px[29][c] = BORDER

    for r in range(3, 29):
        px[r][7] = (min(255, SPINE[0] + 30), min(255, SPINE[1] + 25), min(255, SPINE[2] + 45))

    for r in (9, 14, 19, 24):
        for c in range(23, 26):
            px[r][c] = LINE

    def make_chunk(tag, data):
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', crc)

    raw = bytearray()
    for row in px:
        raw.append(0)
        for r, g, b in row:
            raw += bytes([r, g, b])

    ihdr = struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)
    return (
        b'\x89PNG\r\n\x1a\n'
        + make_chunk(b'IHDR', ihdr)
        + make_chunk(b'IDAT', zlib.compress(bytes(raw), 9))
        + make_chunk(b'IEND', b'')
    )


def read_version():
    init_path = os.path.join(SCRIPT_DIR, '__init__.py')
    with open(init_path, encoding='utf-8') as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if (
                    isinstance(item, ast.Assign)
                    and any(
                        isinstance(t, ast.Name) and t.id == 'version'
                        for t in item.targets
                    )
                    and isinstance(item.value, ast.Tuple)
                ):
                    return tuple(
                        elt.n if hasattr(elt, 'n') else elt.value
                        for elt in item.value.elts
                    )

    raise ValueError("version tuple not found in __init__.py")


def build(output_dir):
    version = read_version()
    version_str = '.'.join(str(v) for v in version)
    zip_name = f'recommender-{version_str}.zip'
    zip_path = os.path.join(output_dir, zip_name)

    os.makedirs(output_dir, exist_ok=True)

    missing = [f for f in PLUGIN_FILES if not os.path.exists(os.path.join(SCRIPT_DIR, f))]
    if missing:
        print(f"ERRO: arquivos ausentes: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    # Garante ícone atualizado em images/icon.png
    images_dir = os.path.join(SCRIPT_DIR, 'images')
    os.makedirs(images_dir, exist_ok=True)
    with open(os.path.join(images_dir, 'icon.png'), 'wb') as _f:
        _f.write(create_icon())

    # Coleta arquivos de imagem (images/*.png, images/*.svg, etc.)
    image_files = []
    if os.path.isdir(images_dir):
        for fname in os.listdir(images_dir):
            if fname.lower().endswith(('.png', '.svg', '.ico', '.jpg')):
                image_files.append(os.path.join('images', fname))

    # Coleta traduções compiladas (translations/*.mo)
    translations_dir = os.path.join(SCRIPT_DIR, 'translations')
    translation_files = []
    if os.path.isdir(translations_dir):
        for fname in os.listdir(translations_dir):
            if fname.lower().endswith('.mo'):
                translation_files.append(os.path.join('translations', fname))

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in PLUGIN_FILES:
            zf.write(os.path.join(SCRIPT_DIR, filename), arcname=filename)
        for filename in image_files:
            zf.write(os.path.join(SCRIPT_DIR, filename), arcname=filename)
        for filename in translation_files:
            zf.write(os.path.join(SCRIPT_DIR, filename), arcname=filename)

    parts = []
    if image_files:
        parts.append(f'{len(image_files)} imagem(ns)')
    if translation_files:
        parts.append(f'{len(translation_files)} tradução(ões)')
    extras = (' + ' + ', '.join(parts)) if parts else ''
    print(f"Plugin v{version_str}{extras} → {zip_path}")
    return zip_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Empacota o plugin para o Calibre')
    parser.add_argument(
        '--output', '-o',
        default=os.path.join(SCRIPT_DIR, 'dist'),
        help='Diretório de saída (padrão: ./dist)',
    )
    args = parser.parse_args()
    build(args.output)
