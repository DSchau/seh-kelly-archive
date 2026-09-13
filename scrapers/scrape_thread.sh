#!/bin/sh
# Download all pages of the Styleforum S.E.H Kelly thread (496 pages as of 2026-09-12).
mkdir -p thread_html
for p in $(seq 1 496); do
  curl -sL -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36' \
    "https://www.styleforum.net/threads/s-e-h-kelly.277070/page-$p" -o "thread_html/page-$p.html"
done
