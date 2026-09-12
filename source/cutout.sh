#!/bin/bash
# Remove the white studio background, trim to the product, cap longest side at 420px.
mkdir -p cut
for f in img/*.webp; do
  n=$(basename "$f" .webp)
  [ -s "cut/$n.png" ] && continue
  magick "$f" -alpha set -bordercolor white -border 2 -fuzz 3% \
    -fill none -draw "alpha 0,0 floodfill" -shave 2x2 +repage \
    -trim +repage -resize '420x420>' \
    -strip "PNG32:cut/$n.png" 2>/dev/null
done
