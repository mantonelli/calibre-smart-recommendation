#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build script: empacota o plugin para instalação no Calibre.
Uso: python build.py [--output DIR]
"""

import argparse
import ast
import os
import sys
import zipfile

PLUGIN_FILES = [
    '__init__.py',
    'engine.py',
    'ui.py',
    'config.py',
    'plugin-import-name-recommender.txt',
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


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

    # Coleta arquivos de imagem opcionais (images/*.png, images/*.svg, etc.)
    images_dir = os.path.join(SCRIPT_DIR, 'images')
    image_files = []
    if os.path.isdir(images_dir):
        for fname in os.listdir(images_dir):
            if fname.lower().endswith(('.png', '.svg', '.ico', '.jpg')):
                image_files.append(os.path.join('images', fname))

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in PLUGIN_FILES:
            zf.write(os.path.join(SCRIPT_DIR, filename), arcname=filename)
        for filename in image_files:
            zf.write(os.path.join(SCRIPT_DIR, filename), arcname=filename)

    extras = f' + {len(image_files)} imagem(ns)' if image_files else ''
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
