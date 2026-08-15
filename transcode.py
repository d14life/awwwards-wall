"""Make small, web-playable proxies of every source video.

Originals are 3K QuickTime-branded H.264 (~5-15 MB each). Chrome aborts them and
no machine plays 290 at once. Proxies: 960px wide, faststart, no audio.
"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

SRC, DST = 'videos', 'web'
WIDTH = 960


def jobs():
    for cat in sorted(os.listdir(SRC)):
        d = os.path.join(SRC, cat)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name.lower().endswith(('.mp4', '.webm', '.mov')):
                out = os.path.join(DST, cat, os.path.splitext(name)[0] + '.mp4')
                yield os.path.join(d, name), out


def convert(job):
    src, out = job
    if os.path.exists(out) and os.path.getsize(out) > 10_000:
        return None
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + '.tmp.mp4'
    r = subprocess.run([
        'ffmpeg', '-y', '-loglevel', 'error', '-i', src,
        '-vf', f'scale={WIDTH}:-2:flags=bicubic',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '26',
        '-profile:v', 'main', '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart', '-an', tmp,
    ], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(tmp) or os.path.getsize(tmp) < 10_000:
        if os.path.exists(tmp):
            os.remove(tmp)
        return f'{src}: {r.stderr.strip()[:160]}'
    os.rename(tmp, out)
    return None


if __name__ == '__main__':
    todo = list(jobs())
    print(f'{len(todo)} sources', file=sys.stderr)
    done = fails = 0
    with ThreadPoolExecutor(6) as ex:
        for err in ex.map(convert, todo):
            done += 1
            if err:
                fails += 1
                print('FAIL', err, file=sys.stderr)
            if done % 25 == 0:
                print(f'{done}/{len(todo)}', file=sys.stderr)
    print(f'done: {done - fails} ok, {fails} failed')
