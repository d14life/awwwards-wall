"""Recursively list the Awwwards Pack Drive tree via embeddedfolderview."""
import re, json, subprocess, html, sys
from concurrent.futures import ThreadPoolExecutor

ROOT = '1BPrOBFEt3pseDZYCK1vwZG3lC_db_DdQ'

ENTRY = re.compile(
    r'<div class="flip-entry" id="entry-([^"]+)".*?'
    r'<a href="https://drive\.google\.com/(drive/folders|file/d)/.*?'
    r'<div class="flip-entry-title">([^<]*)</div>', re.S)


def listing(fid):
    # ponytail: curl, not urllib — this python has no CA bundle
    out = subprocess.run(
        ['curl', '-sL', '--retry', '3',
         f'https://drive.google.com/embeddedfolderview?id={fid}#list'],
        capture_output=True, text=True, timeout=180).stdout
    return [(i, kind == 'drive/folders', html.unescape(n))
            for i, kind, n in ENTRY.findall(out)]


def crawl(root, max_depth=3):
    """Breadth-first, parallel per level. Returns flat list of file dicts."""
    files, level = [], [(root, [], root)]
    for depth in range(max_depth):
        if not level:
            break
        with ThreadPoolExecutor(12) as ex:
            results = list(ex.map(lambda n: (n[1], n[0], listing(n[0])), level))
        nxt = []
        for path, parent, entries in results:
            for fid, is_folder, name in entries:
                if name == '.DS_Store':
                    continue
                if is_folder:
                    nxt.append((fid, path + [name], fid))
                else:
                    # parent = the numbered folder holding video + code.zip
                    files.append({'id': fid, 'name': name, 'path': path,
                                  'parent': parent})
        print(f'depth {depth}: {len(nxt)} folders, {len(files)} files so far',
              file=sys.stderr)
        level = nxt
    return files


if __name__ == '__main__':
    files = crawl(ROOT)
    json.dump(files, open('files.json', 'w'), indent=1, ensure_ascii=False)
    print('TOTAL FILES:', len(files))
