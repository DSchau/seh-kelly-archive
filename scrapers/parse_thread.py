"""Parse downloaded Styleforum thread HTML into raw_thread_posts.jsonl.

Each line: {page, post_id, author, datetime, ts, text, images, links}
"""
import glob, json, re
from bs4 import BeautifulSoup

out = open('data/raw_thread_posts.jsonl', 'w')
for f in sorted(glob.glob('thread_html/page-*.html'), key=lambda x: int(re.search(r'page-(\d+)', x).group(1))):
    page = int(re.search(r'page-(\d+)', f).group(1))
    soup = BeautifulSoup(open(f, encoding='utf-8', errors='replace').read(), 'html.parser')
    for art in soup.select('article.message--post'):
        body = art.select_one('div.bbWrapper')
        if not body:
            continue
        t = art.select_one('time.u-dt')
        imgs, links = [], []
        for img in body.select('img'):
            src = img.get('src') or img.get('data-src')
            if src and 'data:image' not in src and 'reaction-sprite' not in src:
                imgs.append(src if not src.startswith('/') else 'https://www.styleforum.net' + src)
        for a in body.select('a[href]'):
            href = a.get('href') or ''
            if href.startswith('/'):
                href = 'https://www.styleforum.net' + href
            links.append(href)
            if '/attachments/' in href and not any(href in i for i in imgs):
                imgs.append(href)
        out.write(json.dumps({
            'page': page,
            'post_id': art.get('data-content', ''),
            'author': art.get('data-author', ''),
            'datetime': t.get('datetime') if t else None,
            'ts': int(t.get('data-time')) if t else None,
            'text': body.get_text('\n', strip=True),
            'images': imgs,
            'links': links,
        }) + '\n')
out.close()
