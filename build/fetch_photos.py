"""Download manifest photos into data/garments/<id>/photos/. Usage: fetch_photos.py <start> <end>"""
import json, os, sys, subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
start, end = int(sys.argv[1]), int(sys.argv[2])

jobs = []
for gid in sorted(os.listdir(os.path.join(ROOT, 'data/garments'))):
    mp = os.path.join(ROOT, 'data/garments', gid, 'photos_manifest.json')
    if not os.path.exists(mp): continue
    man = json.load(open(mp))
    pdir = os.path.join(ROOT, 'data/garments', gid, 'photos')
    os.makedirs(pdir, exist_ok=True)
    for i, ph in enumerate(man):
        dest = os.path.join(pdir, f'p{i+1:03d}')
        if any(os.path.exists(dest + ext) for ext in ('.jpg','.png','.gif','.webp','.jpeg')): continue
        jobs.append((ph['url'], dest))

def fetch(job):
    url, dest = job
    try:
        r = subprocess.run(['curl','-sL','--max-time','25','-A','Mozilla/5.0','-o',dest,'-w','%{http_code} %{content_type}', url],
                           capture_output=True, text=True, timeout=35)
    except Exception:
        return False
    code, _, ctype = (r.stdout + ' ').partition(' ')
    ext = {'image/jpeg':'.jpg','image/png':'.png','image/gif':'.gif','image/webp':'.webp'}.get((ctype or '').strip().split(';')[0])
    size = os.path.getsize(dest) if os.path.exists(dest) else 0
    if code.startswith('2') and ext and size > 3000:
        os.rename(dest, dest + ext)
        return True
    if os.path.exists(dest): os.remove(dest)
    return False

chunk = jobs[start:end]
print('pending total:', len(jobs), '| this chunk:', len(chunk))
with ThreadPoolExecutor(max_workers=16) as ex:
    oks = list(ex.map(fetch, chunk))
print('ok:', sum(oks), 'failed:', len(oks)-sum(oks))
