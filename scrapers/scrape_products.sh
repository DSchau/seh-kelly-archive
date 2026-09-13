#!/bin/sh
# Pull the live S.E.H Kelly Shopify catalog.
curl -s 'https://sehkelly.com/products.json?limit=250' -o data/raw_products.json
