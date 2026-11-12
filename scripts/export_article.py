#!/usr/bin/env python3
"""Export a selected My Zettel article and its local images; never commits or pushes."""
import argparse
import datetime
import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, quote

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('--slug', required=True, help='Permanent article identifier, lowercase ASCII')
p.add_argument('--description', required=True)
p.add_argument('--date', required=True, type=datetime.date.fromisoformat)
p.add_argument('--lang', choices=['ru', 'en'], default='ru')
p.add_argument('--write', action='store_true', help='Write files; otherwise only preview')
a = p.parse_args()
if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', a.slug):
    p.error('Invalid slug')
root = Path(__file__).resolve().parents[1]
source = a.source.resolve(strict=True)
text = source.read_text()
if text.startswith('---\n'):
    p.error('Source has frontmatter: reconcile metadata before export to avoid losing properties')
target = root / '_publications' / (a.slug + '.md')
url = '/publications/' + a.slug + '/'
# Refuse to overwrite or create a second file at an existing permanent address.
if target.exists():
    p.error('Target exists: update the existing publication explicitly, preserving its permalink')
for article in (root / '_publications').glob('*.md'):
    if url in article.read_text():
        p.error('Permalink already exists in ' + str(article))
images = {}
def image(path, alt):
    if re.match(r'https?://', path):
        return '![' + alt + '](' + path + ')'
    src = (source.parent / unquote(path)).resolve()
    if not src.is_relative_to(source.parent):
        p.error('Image must be inside article folder: ' + path)
    if not src.is_file() or src.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.avif'}:
        p.error('Missing or unsupported image: ' + path)
    relative = src.relative_to(source.parent)
    images[src] = root / 'assets' / 'articles' / a.slug / relative
    return '![' + alt + '](/assets/articles/' + a.slug + '/' + quote(relative.as_posix()) + ')'
text = re.sub(r'!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', lambda m: image(m[1], m[2] or Path(m[1]).stem), text)
# Already converted site paths must not be processed again.
text = re.sub(r'!\[([^\]]*)\]\(([^\s)]+)\)', lambda m: m[0] if m[2].startswith('/assets/articles/') else image(m[2], m[1]), text)
if '[[' in text:
    p.error('Unresolved Obsidian links: replace them with public Markdown links')
metadata = {'layout': 'publication', 'title': source.stem, 'description': a.description, 'date': str(a.date), 'lang': a.lang, 'permalink': url}
content = '---\n' + ''.join(k + ': ' + json.dumps(v, ensure_ascii=False) + '\n' for k, v in metadata.items()) + '---\n\n' + text
print('Article:', target)
print('URL:', url)
print('Images:', len(images))
if a.write:
    target.parent.mkdir(parents=True, exist_ok=True)
    for src, dst in images.items():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    target.write_text(content)
    print('Exported locally. Review before committing and pushing.')
else:
    print('Preview only. Add --write to export.')
