# Crepe & More — Al Rashid Mall menu

Single-page digital menu, built for viewing in a browser on an in-store tablet.

**Live:** https://botlychat.github.io/crepe-more-menu/

- One scrolling page, one section per row, Arabic + English, prices in SAR.
- Pinned to a white background so a device in dark mode still shows the
  brand's white menu.
- Responsive: ~6 items per row on an iPad in landscape, ~4 in portrait,
  3 on a phone.
- Product photos are the restaurant's own studio shots with the white
  background removed, so each item floats on the page.
- Fonts (El Messiri, Poppins) are self-hosted and subset to only the glyphs
  this page uses, so the page loads without any third-party requests.

## Adding it to the tablet

Open the link in Safari, then **Share → Add to Home Screen**. It opens
full-screen without browser chrome, like an app.

## Updating

`index.html` is generated. Edit the source and regenerate rather than editing
the HTML by hand:

- `source/build_web.py` — section order, which items appear, page markup + CSS
- `source/build.py` — Arabic/English name overrides and the `PRICE` dict that
  overrides the API where the restaurant's own price list disagrees
- `source/cutout.sh` — removes the white studio background from product photos

```sh
cd source && python3 build_web.py   # writes ../site, then copy over the root
```

Item data originally came from the branch's own API
(`menu.crepemoresa.com/api/items-light/`).
