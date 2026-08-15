"""Download every preview video from files.json into videos/<Category>/."""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

VIDEO_EXT = ('.mp4', '.webm', '.mov')
OUT = 'videos'


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def dest(f):
    return os.path.join(OUT, slug(f['path'][0]), f'{f["path"][1]}-{f["name"]}')


def fetch(f):
    path = dest(f)
    if os.path.exists(path) and os.path.getsize(path) > 10_000:
        return ('skip', path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.part'
    r = subprocess.run(
        ['curl', '-sL', '--retry', '3', '--retry-delay', '2', '--max-time', '600',
         '-o', tmp, '-w', '%{http_code} %{content_type}',
         f'https://drive.usercontent.google.com/download?id={f["id"]}&export=download&confirm=t'],
        capture_output=True, text=True)
    code, _, ctype = r.stdout.partition(' ')
    # a Drive error page is HTML, not video — never let one land as a .mp4.
    # Drive serves .webm as application/octet-stream, so allow that too.
    ok_type = ctype.startswith('video') or ctype.startswith('application/octet-stream')
    # curl leaves no file at all when it never connects, so check before stat
    size = os.path.getsize(tmp) if os.path.exists(tmp) else 0
    if code != '200' or not ok_type or size < 10_000:
        if os.path.exists(tmp):
            os.remove(tmp)
        return ('FAIL', f'{path} http={code} type={ctype}')
    os.rename(tmp, path)
    return ('ok', path)


if __name__ == '__main__':
    files = [f for f in json.load(open('files.json'))
             if f['name'].lower().endswith(VIDEO_EXT)]
    print(f'{len(files)} videos to fetch', file=sys.stderr)
    done = fails = 0
    with ThreadPoolExecutor(8) as ex:
        for status, msg in ex.map(fetch, files):
            done += 1
            if status == 'FAIL':
                fails += 1
                print('FAIL', msg, file=sys.stderr)
            if done % 25 == 0:
                print(f'{done}/{len(files)}', file=sys.stderr)
    print(f'done: {done - fails} ok, {fails} failed')
