"""Join the Drive listing with the transcoded proxies -> videos.json."""
import json, os, re

WEB = 'web'
DRIVE = 'https://drive.google.com/drive/folders/'


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


items, missing = [], 0
for f in json.load(open('files.json')):
    if not f['name'].lower().endswith(('.mp4', '.webm', '.mov')):
        continue
    cat, num = f['path'][0], f['path'][1]
    src = os.path.join(WEB, slug(cat), f'{num}-{os.path.splitext(f["name"])[0]}.mp4')
    if not os.path.exists(src):
        missing += 1
        continue
    items.append({'cat': slug(cat), 'catName': cat, 'num': num, 'src': src,
                  'name': os.path.splitext(f['name'])[0],
                  'code': DRIVE + f['parent']})

items.sort(key=lambda i: (i['catName'], len(i['num']), i['num']))
json.dump(items, open('videos.json', 'w'), indent=0)
print(f'{len(items)} videos in {len({i["cat"] for i in items})} categories'
      f' ({missing} not transcoded yet)')
