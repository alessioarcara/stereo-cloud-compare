#!/usr/bin/env python3
"""One-shot setup: ONNX Runtime Web into vendor/ and FoundationStereo into models/ (use --no-models to skip it).

FoundationStereo is NVIDIA's official ONNX (480x640 input, 718 MB, NVIDIA Source Code License, non-commercial), fetched
from the Google Drive folder of https://github.com/NVlabs/FoundationStereo; it is never redistributed by this repository.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

ORT = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.20.1/dist/'
ORT_FILES = ['ort.all.min.js', 'ort-wasm-simd-threaded.jsep.wasm', 'ort-wasm-simd-threaded.jsep.mjs', 'ort-wasm-simd-threaded.wasm', 'ort-wasm-simd-threaded.mjs']
FILE_ID = '1NbgG4zahqwMzEa2zx7nWyNtLHiy-Pjus'
ENTRY = {'file': 'foundation_stereo_23-51-11.onnx', 'name': 'FoundationStereo 23-51-11 (ViT-L)', 'width': 640, 'height': 480,
         'note': 'ONNX ufficiale NVIDIA, 718 MB, licenza non commerciale; pseudo ground truth'}

parser = argparse.ArgumentParser()
parser.add_argument('--no-models', action='store_true', help='only ONNX Runtime Web')
args = parser.parse_args()
here = Path(__file__).resolve().parent.parent


def fetch(url, path):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})) as r, path.open('wb') as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)


vendor = here / 'vendor'
vendor.mkdir(exist_ok=True)
for name in ORT_FILES:
    if (vendor / name).exists():
        continue
    print('vendor/' + name, flush=True)
    fetch(ORT + name, vendor / name)

def drive_download(file_id, path):
    """Google Drive download without extra packages: large files answer with a confirmation form, which is resubmitted."""
    import html
    import re
    import urllib.parse
    import urllib.request
    url = f'https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t'
    for _ in range(3):
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})) as r:
            if 'text/html' not in r.headers.get('Content-Type', ''):
                total = int(r.headers.get('Content-Length') or 0)
                done = 0
                with path.open('wb') as f:
                    while chunk := r.read(1 << 20):
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            print(f'\r  {100 * done // total:3d} %  {done / 2 ** 20:6.0f} / {total / 2 ** 20:.0f} MB', end='', flush=True)
                print()
                return
            page = r.read().decode('utf-8', 'replace')
        form = re.search(r'<form[^>]+action="([^"]+)"[^>]*>(.*?)</form>', page, re.S)
        if not form:
            raise RuntimeError('Drive non ha restituito il file (quota superata o link cambiato)')
        fields = {k: html.unescape(v) for k, v in re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', form.group(2))}
        url = html.unescape(form.group(1)) + '?' + urllib.parse.urlencode(fields)
    raise RuntimeError('troppi reindirizzamenti dal modulo di conferma di Drive')


models = here / 'models'
models.mkdir(exist_ok=True)
dest = models / ENTRY['file']
if not args.no_models and not dest.exists():
    print('models/' + ENTRY['file'], flush=True)
    try:
        drive_download(FILE_ID, dest)
    except Exception as err:
        dest.unlink(missing_ok=True)
        print(f'FoundationStereo non scaricato ({err}): prendi onnx/{ENTRY["file"]} dalla cartella Drive di NVlabs/FoundationStereo e copialo in models/.', file=sys.stderr)
    if dest.exists() and dest.stat().st_size < 100 * 2 ** 20:
        dest.unlink()
        print('FoundationStereo non scaricato: file incompleto.', file=sys.stderr)
entries = [{**ENTRY, 'size_mb': round(dest.stat().st_size / 2 ** 20)}] if dest.exists() else []
(models / 'index.json').write_text(json.dumps({'models': entries}, indent=2, ensure_ascii=False))
print('ok: vendor/', 'e', ', '.join(e['name'] for e in entries) if entries else 'nessun modello nel catalogo')
