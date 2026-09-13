"""Build the garment database from raw_products.json + raw_thread_posts.jsonl.

Outputs:
  data/garments/<id>/metadata.json
  data/garments/<id>/photos_manifest.json   (photos downloaded by fetch_photos.sh)
  data/index.json
"""
import json, re, os, collections, datetime, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, *p)

# ---------- vocab ----------
MATERIALS = ['linen','cotton','wool','lambswool','merino','cashmere','silk','tweed','flannel',
 'corduroy','cord','moleskin','melton','hopsack','ripstop','ventile','denim','canvas','wax','waxed',
 'leather','shetland','geelong','donegal','herringbone','oxford','poplin','jersey','bedford',
 'natte','barathea','gabardine','chamois','fleece','towelling','seersucker','madras','tuck',
 'sail cloth','sailcloth','drill','twill','velvet','suede','alpaca','mohair','angora','horn','brass',
 'worsted','woollen','ripstop','fustian','chenille','boucle','doeskin','cavalry','duffle','serge']

TYPE_WORDS = {
 'balmacaan':'Coat','trench':'Coat','peacoat':'Coat','topcoat':'Coat','overcoat':'Coat','duffle':'Coat',
 'ulster':'Coat','british-warm':'Coat','car-coat':'Coat','field-coat':'Coat','raincoat':'Raincoat','mac':'Raincoat',
 'parka':'Coat','anorak':'Jacket','jacket':'Jacket','trucker':'Jacket','blazer':'Jacket','overshirt':'Overshirt',
 'work-jacket':'Jacket','shirt-jacket':'Overshirt','shirt':'Shirt','popover':'Shirt','polo':'Shirt',
 't-shirt':'T-Shirt','tee':'T-Shirt','trouser':'Trousers','trousers':'Trousers','pants':'Trousers','shorts':'Trousers',
 'jean':'Trousers','gansey':'Knitwear','jumper':'Knitwear','cardigan':'Knitwear','sweater':'Knitwear',
 'crewneck':'Knitwear','v-neck':'Knitwear','shawl':'Knitwear','knit':'Knitwear','waistcoat':'Waistcoat','vest':'Waistcoat',
 'scarf':'Accessories','hat':'Accessories','cap':'Accessories','glove':'Accessories','socks':'Accessories',
 'belt':'Accessories','bag':'Accessories','spectacle':'Accessories','glasses':'Accessories','snood':'Accessories',
 'hood':'Accessories','pyjama':'Pyjama','suit':'Suit','watch-cap':'Accessories','mittens':'Accessories',
}
NON_GARMENT = {'shop','images','cdn','words','worn','pages','blogs','collections','products','cart','search',
 'account','policies','makers','news','wp-content','en-us','en-ca','en-ie','en-gb','sitemap.xml','feeds',
 'articles','xl','large','medium','small','xs','xxl','stockists','stockist','about','contact','synthetic-serendipity'}

def slug_type(slug):
    s = slug.split('-in-')[0]
    toks = s.split('-')
    best = None
    for i in range(len(toks)):
        for j in range(i+1, len(toks)+1):
            w = '-'.join(toks[i:j])
            if w in TYPE_WORDS and (best is None or len(w) > len(best[0])):
                best = (w, TYPE_WORDS[w])
    return best  # (type_word, category) or None

def parse_slug(slug):
    """Return dict(type, fabric, colour) from '<type>-in-<fabric>-in-<colour>' style slug."""
    parts = slug.split('-in-')
    out = {'garment_type': None, 'fabric': None, 'colour': None}
    if len(parts) >= 3:
        out['garment_type'] = parts[0].replace('-', ' ')
        out['fabric'] = '-in-'.join(parts[1:-1]).replace('-', ' ')
        out['colour'] = parts[-1].replace('-', ' ')
    elif len(parts) == 2:
        out['garment_type'] = parts[0].replace('-', ' ')
        out['fabric'] = parts[1].replace('-', ' ')
    else:
        out['garment_type'] = slug.replace('-', ' ')
    return out

def materials_of(*texts):
    blob = ' '.join(t for t in texts if t).lower()
    found = []
    for m in MATERIALS:
        if re.search(r'\b' + re.escape(m) + r's?\b', blob) and m not in found:
            found.append(m)
    return found

def season_of(dtstr):
    if not dtstr: return None
    y, m = int(dtstr[:4]), int(dtstr[5:7])
    return f'{"SS" if 3 <= m <= 7 else "AW"}{y}'

def title_of(parsed, slug):
    t, f, c = parsed['garment_type'], parsed['fabric'], parsed['colour']
    if t and f and c: return f'{t} in {f} in {c}'
    if t and f: return f'{t} in {f}'
    return t or slug.replace('-', ' ')

# ---------- load ----------
products = json.load(open(D('data/raw_products.json')))['products']
posts = [json.loads(l) for l in open(D('data/raw_thread_posts.jsonl'))]
posts_by_id = {p['post_id']: p for p in posts}

garments = {}  # id -> record

# ---------- live catalog ----------
for pr in products:
    h = pr['handle']
    parsed = parse_slug(h)
    prices = [float(v['price']) for v in pr['variants'] if v.get('price')]
    sizes = sorted({v['option2'] for v in pr['variants'] if v.get('option2')})
    colours = sorted({v['option1'] for v in pr['variants'] if v.get('option1')})
    body = re.sub(r'<[^>]+>', ' ', pr.get('body_html') or '')
    body = html.unescape(re.sub(r'\s+', ' ', body)).strip()
    tw = slug_type(h)
    g = {
        'id': h, 'name': pr['title'],
        'category': pr.get('product_type') or (tw[1] if tw else 'Other'),
        'garment_type': parsed['garment_type'], 'fabric': parsed['fabric'], 'colour': parsed['colour'],
        'colours_offered': colours, 'materials': materials_of(parsed['fabric'], body, pr['title']),
        'release_date': pr.get('published_at', '')[:10], 'release_estimate': False,
        'season': season_of(pr.get('published_at')),
        'price_gbp': min(prices) if prices else None, 'sizes': sizes,
        'status': 'in production', 'description': body,
        'product_url': f'https://sehkelly.com/products/{h}',
        'sources': ['sehkelly.com live catalog'],
        'thread_links': [], 'thread_post_ids': [], 'first_seen': None, 'last_seen': None, 'mention_count': 0,
        'photos': [],
    }
    for img in pr.get('images', []):
        g['photos'].append({'url': img['src'], 'origin': 'sehkelly.com', 'post_id': None, 'date': None, 'author': None})
    garments[h] = g

# ---------- thread-linked garments ----------
slug_pat = re.compile(r'sehkelly\.(?:com|co\.uk)/(?:shop/)?(?:[a-z-]+/)?([a-z0-9]+(?:-[a-z0-9]+)+)/?(?:[?#].*)?$')
link_posts = collections.defaultdict(list)
for p in posts:
    seen = set()
    for href in p['links']:
        m = slug_pat.search(href)
        if not m: continue
        slug = m.group(1)
        first = slug.split('-')[0]
        if first in NON_GARMENT or slug in NON_GARMENT: continue
        if any(x in href for x in ('/images/', '/cdn/', 'wp-content', '/words/', '/news/', '/makers/', '/pages/', '/blogs/')): continue
        tw = slug_type(slug)
        if not tw: continue
        if slug in seen: continue
        seen.add(slug)
        link_posts[slug].append(p)

def find_live(slug):
    if slug in garments: return slug
    for h in garments:
        if h.endswith(slug) or slug.endswith(h): return h
    return None

for slug, ps in link_posts.items():
    live = find_live(slug)
    dates = sorted(p['datetime'] for p in ps if p['datetime'])
    first_seen, last_seen = (dates[0][:10], dates[-1][:10]) if dates else (None, None)
    if live:
        g = garments[live]
        g['sources'].append('styleforum thread')
        g['first_seen'], g['last_seen'] = first_seen, last_seen
        g['mention_count'] = len(ps)
        g['thread_post_ids'] = [p['post_id'] for p in ps]
        g['thread_links'] = sorted({f'https://sehkelly.com/{slug}/'})
        continue
    parsed = parse_slug(slug)
    tw = slug_type(slug)
    g = {
        'id': slug, 'name': title_of(parsed, slug),
        'category': tw[1] if tw else 'Other',
        'garment_type': parsed['garment_type'], 'fabric': parsed['fabric'], 'colour': parsed['colour'],
        'colours_offered': [], 'materials': materials_of(parsed['fabric'], parsed['garment_type'], slug),
        'release_date': first_seen, 'release_estimate': True,
        'season': season_of(first_seen),
        'price_gbp': None, 'sizes': [],
        'status': 'archived', 'description': None,
        'product_url': f'https://sehkelly.com/{slug}/',
        'sources': ['styleforum thread'],
        'thread_links': sorted({l for p in ps for l in p['links'] if slug in l})[:5],
        'thread_post_ids': [p['post_id'] for p in ps],
        'first_seen': first_seen, 'last_seen': last_seen, 'mention_count': len(ps),
        'photos': [],
    }
    garments[slug] = g

# ---------- text-mention matching ----------
STOP = {'in','the','a','an','of','and','with','for','to','on','at','by','is','it'}
def toks(s):
    return set(re.findall(r"[a-z][a-z'-]+", (s or '').lower())) - STOP

def head_token(s):
    t = [w for w in re.findall(r"[a-z][a-z'-]+", (s or '').lower()) if w not in STOP]
    return t[0] if t else None

gmatch = {}
for gid, g in garments.items():
    type_head = head_token(g['garment_type'])
    fabric_head = head_token(g['fabric'])
    colour_head = head_token(g['colour'])
    if not type_head: continue
    gmatch[gid] = (type_head, fabric_head, colour_head)

text_posts = collections.defaultdict(list)
for p in posts:
    tl = p['text'].lower()
    if len(tl) < 8: continue
    for gid, (th, fh, ch) in gmatch.items():
        if th not in tl: continue
        if (fh and fh in tl) or (ch and ch in tl):
            text_posts[gid].append(p)

for gid, ps in text_posts.items():
    g = garments[gid]
    known = set(g['thread_post_ids'])
    new = [p for p in ps if p['post_id'] not in known]
    g['thread_post_ids'] += [p['post_id'] for p in new]
    g['mention_count'] += len(new)
    dates = [p['datetime'] for p in ps if p['datetime']]
    if dates:
        fs, ls = min(dates)[:10], max(dates)[:10]
        g['first_seen'] = min(filter(None, [g['first_seen'], fs])) if g['first_seen'] else fs
        g['last_seen'] = max(filter(None, [g['last_seen'], ls])) if g['last_seen'] else ls
        if g['status'] == 'archived' and g['release_estimate']:
            g['release_date'] = g['first_seen']
            g['season'] = season_of(g['first_seen'])

# ---------- thread photos onto garments ----------
for gid, g in garments.items():
    seen_urls = {ph['url'] for ph in g['photos']}
    for pid in g['thread_post_ids']:
        p = posts_by_id.get(pid)
        if not p: continue
        for url in p['images']:
            if url in seen_urls: continue
            seen_urls.add(url)
            g['photos'].append({'url': url, 'origin': 'styleforum', 'post_id': pid,
                                'date': (p['datetime'] or '')[:10], 'author': p['author']})
    # maker's photos first, then newest
    g['photos'].sort(key=lambda ph: (ph['origin'] != 'sehkelly.com', (ph['author'] or '').lower() != 'sehkelly', ph['date'] or '9999'))
    g['photos'] = g['photos'][:40]

# ---------- write ----------
os.makedirs(D('data/garments'), exist_ok=True)
index = []
for gid, g in sorted(garments.items()):
    gd = D('data/garments', gid)
    os.makedirs(gd, exist_ok=True)
    manifest = g.pop('photos')
    json.dump(g, open(os.path.join(gd, 'metadata.json'), 'w'), indent=2)
    json.dump(manifest, open(os.path.join(gd, 'photos_manifest.json'), 'w'), indent=2)
    year = (g['release_date'] or g['first_seen'] or '')[:4] or None
    index.append({'id': gid, 'name': g['name'], 'category': g['category'], 'year': year,
                  'season': g['season'], 'fabric': g['fabric'], 'colour': g['colour'],
                  'materials': g['materials'], 'status': g['status'], 'photo_count': len(manifest),
                  'price_gbp': g['price_gbp']})
json.dump(sorted(index, key=lambda x: (x['year'] or '9999', x['name'])), open(D('data/index.json'), 'w'), indent=2)
print('garments:', len(garments))
print('photos planned:', sum(i['photo_count'] for i in index))
print('archived (thread-only):', sum(1 for i in index if i['status'] == 'archived'))
