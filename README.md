# S.E.H Kelly archive

A filesystem-based archive of S.E.H Kelly garments over the years, plus a local static site to browse it.

## Sources
- Live catalog: `sehkelly.com/products.json` (Shopify) - 56 current garments with canonical metadata and photos.
- Historical record: the Styleforum S.E.H Kelly thread (https://www.styleforum.net/threads/s-e-h-kelly.277070/, 496 pages, 7,429 posts, 2011-2026) - garment page links and the maker's own posts supply release timing, mentions, and period photos.

## Layout
- `data/garments/<id>/metadata.json` - one garment: name, category, fabric, colour, materials, release date (or first-sighted estimate), season, price (when known), sources, thread stats, local photo list.
- `data/garments/<id>/photos/` - the garment's photos (downloaded from sehkelly.com CDN and styleforum.net attachments).
- `data/index.json` - master index over all garments.
- `site/` - static gallery. Open `site/index.html` in a browser (works from file://). Filter by category, material, year, status; search; click a card for all photos and metadata.
- `scrapers/` - how the raw data was pulled. `build/` - how the database and site data were generated.

## Coverage notes
- Garments come from (a) the live catalog and (b) garment-page links in the thread, matched to posts by link and by name-in-text. Very old garments only ever mentioned in passing prose (no link, no exact name match) are not captured.
- 547 thread image URLs from ~2011-2016 are dead at the source (old external hosts); those photos are unrecoverable. 39 garments have no surviving photo.
- Release dates for archived garments are "first sighted in thread" estimates, not official release dates.

## Rebuild
1. `sh scrapers/scrape_products.sh`
2. `sh scrapers/scrape_thread.sh` (slow; ~500 pages)
3. `python3 scrapers/parse_thread.py` (needs beautifulsoup4)
4. `python3 build/build_db.py`
5. `python3 build/fetch_photos.py 0 99999`
