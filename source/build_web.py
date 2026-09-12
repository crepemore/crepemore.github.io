#!/usr/bin/env python3
"""Build the single-page web menu for Crepe & More - Al Rashid Mall.

One scrolling page, one section per full-width row. Item names, prices and
photos come from the same data as the PDF build (see build.py); prices in
build.PRICE override the API where the restaurant's own list disagrees.

Output goes to site/ : index.html, img/, fonts/, logo.png
"""
import json, os, re, shutil, html
from fontTools import subset
from fontTools.ttLib import TTFont

import build   # AR / EN / PRICE overrides and the item data

BLUE, INK, MUTED, RULE = '#2E5D95', '#1F3D63', '#8D9CB0', '#CBD6E5'
OUT = 'site'
HOURS_EN, HOURS_AR = '10 AM – 12 AM', '١٠ ص – ١٢ م'

# section order, grouped; ids are the same ones the PDF uses
GROUPS = [
    ('الطعام', 'FOOD', [
        ('كريب',        'CREPE',        [117, 1, 93, 2, 3, 89, 4]),
        ('بان كيك',     'PANCAKE',      [139, 7, 140, 138]),
        ('وافل',        'WAFFLE',       [143, 142, 123]),
        ('فرنش توست',   'FRENCH TOAST', [144]),
        ('كريب مالح',   'SAVORY CREPE', [17, 18, 19]),
        ('مخبوزات',     'BAKERY',       [83, 84, 85, 86, 145, 146]),
        ('ساندوتش',     'SANDWICHES',   [129, 12, 14, 184, 164]),
        ('آيس كريم',    'ICE CREAM',    [149]),
    ]),
    ('المشروبات', 'DRINKS', [
        ('مشروبات ساخنة', 'HOT DRINKS', [21, 22, 20, 161, 23, 24, 25, 26, 27,
                                          29, 28, 30, 32, 31, 33, 34, 36, 37]),
        ('مشروبات مثلجة', 'ICED DRINKS', [50, 40, 167, 41, 42, 43, 44, 49, 51]),
        ('فرابيه',        'FRAPPE',      [45, 46, 47, 48]),
        ('ميلك شيك',      'MILKSHAKE',   [53, 54, 55, 56, 57, 58]),
        ('عصائر و سموثي', 'JUICE & SMOOTHIE', [59, 60, 61, 63, 64, 62, 176]),
        ('موهيتو',        'MOJITO',      [173, 172, 67, 171]),
        ('مشروبات باردة', 'COLD DRINKS', [52, 91]),
    ]),
]
EXTRAS = [100, 99, 101, 102, 159, 178]


def slug(en):
    return re.sub(r'[^a-z0-9]+', '-', en.lower()).strip('-')


def name_ar(i, items):
    return build.AR.get(i, (items[i]['name_ar'] or '').strip())


def name_en(i, items):
    return build.EN.get(i, (items[i]['name_en'] or '').strip())


def price(i, items):
    v = build.PRICE.get(i, items[i]['price'])
    n = int(v) if float(v).is_integer() else round(float(v), 2)
    return n


def cell(i, items):
    src = f'img/{i}.jpg'
    img = (f'<img src="{src}" alt="{html.escape(name_en(i, items))}"'
           f' loading="lazy" decoding="async">'
           if os.path.exists(f'{OUT}/{src}') else '')
    return (f'<li class=item>'
            f'<div class=shot>{img}</div>'
            f'<h3>{html.escape(name_ar(i, items))}</h3>'
            f'<p class=en>{html.escape(name_en(i, items))}</p>'
            f'<p class=price>{price(i, items)}<span>SR</span></p>'
            f'</li>')


def build_html(items):
    nav, body = [], []
    for g_ar, g_en, secs in GROUPS:
        if g_en != 'FOOD':          # food needs no label - the page opens on it
            body.append(f'<h2 class=group id="{slug(g_en)}">'
                        f'<span class=ar>{g_ar}</span>'
                        f'<span class=en>{g_en}</span></h2>')
        for s_ar, s_en, ids in secs:
            sid = slug(s_en)
            nav.append(f'<a href="#{sid}">{s_ar}</a>')
            cells = ''.join(cell(i, items) for i in ids if i in items)
            body.append(
                f'<section id="{sid}">'
                f'<div class=sh><h2>{html.escape(s_ar)}</h2>'
                f'<span class=e>{html.escape(s_en)}</span><i></i></div>'
                f'<ul class=grid>{cells}</ul></section>')

    ex = ''.join(
        f'<li><b>{html.escape(name_ar(i, items))}</b>'
        f'<em>{html.escape(name_en(i, items))}</em>'
        f'<span class=price>{price(i, items)}<span>SR</span></span></li>'
        for i in EXTRAS if i in items)
    body.append(
        '<section id="extras"><div class=sh><h2>إضافات</h2>'
        '<span class=e>EXTRAS</span><i></i></div>'
        f'<ul class=extras>{ex}</ul></section>')

    return f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>كريب أند مور · الراشد مول — القائمة</title>
<meta name="description" content="قائمة كريب أند مور - فرع الراشد مول. Crepe &amp; More menu, Al Rashid Mall.">
<meta name="theme-color" content="{BLUE}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Crepe &amp; More">
<link rel="icon" href="logo.png">
<link rel="apple-touch-icon" href="logo.png">
<style>{CSS}</style>
</head>
<body>
<header class=top>
 <div class=bar>
  <img class=logo src="logo.png" alt="Crepe &amp; More">
  <div class=where><b>الراشد مول</b><span>AL RASHID MALL</span></div>
  <div class=hours><b>{HOURS_AR}</b><span>{HOURS_EN}</span></div>
 </div>
 <nav class=jump>{''.join(nav)}</nav>
</header>
<main>{''.join(body)}</main>
<footer>
 <p>الأسعار بالريال السعودي · Prices in Saudi Riyal</p>
 <p class=sub>كريب أند مور — فرع الراشد مول · Crepe &amp; More, Al Rashid Mall</p>
</footer>
</body>
</html>'''


CSS = f'''
@font-face{{font-family:EM;src:url('fonts/em-600.ttf') format('truetype');font-weight:600;font-display:swap}}
@font-face{{font-family:EM;src:url('fonts/em-700.ttf') format('truetype');font-weight:700;font-display:swap}}
@font-face{{font-family:PP;src:url('fonts/pp-500.ttf') format('truetype');font-weight:500;font-display:swap}}
@font-face{{font-family:PP;src:url('fonts/pp-700.ttf') format('truetype');font-weight:700;font-display:swap}}

*{{box-sizing:border-box;margin:0;padding:0}}
:root{{color-scheme:light;--blue:{BLUE};--ink:{INK};--muted:{MUTED};--rule:{RULE};--pad:clamp(12px,3vw,28px)}}
html{{scroll-behavior:smooth;-webkit-text-size-adjust:100%}}
body{{background:#fff;color:var(--ink);color-scheme:light;font-family:EM,PP,system-ui,sans-serif;
 -webkit-tap-highlight-color:transparent}}

/* sticky header */
.top{{position:sticky;top:0;z-index:10;background:#fff;
 border-bottom:1px solid var(--rule);padding-top:env(safe-area-inset-top)}}
.bar{{display:flex;align-items:center;gap:clamp(10px,2.5vw,22px);
 padding:10px var(--pad) 8px;max-width:1500px;margin:0 auto}}
.logo{{height:clamp(28px,5.2vw,44px);width:auto;display:block}}
.where{{margin-inline-end:auto;line-height:1.15}}
.where b{{display:block;font:700 clamp(14px,2.5vw,19px)/1.15 EM;color:var(--blue)}}
.where span{{direction:ltr;display:block;font:500 clamp(8px,1.3vw,10px)/1.3 PP;
 letter-spacing:.14em;color:var(--muted)}}
.hours{{text-align:left;line-height:1.15}}
.hours b{{display:block;font:700 clamp(12px,2vw,16px)/1.15 EM;color:var(--ink)}}
.hours span{{direction:ltr;display:block;font:500 clamp(8px,1.3vw,10px)/1.3 PP;
 letter-spacing:.1em;color:var(--muted)}}

/* quick jump strip */
.jump{{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;
 padding:0 var(--pad) 9px;max-width:1500px;margin:0 auto}}
.jump::-webkit-scrollbar{{display:none}}
.jump a{{flex:none;text-decoration:none;font:600 clamp(11px,1.8vw,14px) EM;
 color:var(--blue);background:#EEF3F9;border-radius:999px;
 padding:5px clamp(9px,1.6vw,14px);white-space:nowrap}}
.jump a:active{{background:var(--blue);color:#fff}}

main{{max-width:1500px;margin:0 auto;padding:0 var(--pad) 8px}}

/* group divider: FOOD / DRINKS */
.group{{display:flex;align-items:baseline;gap:10px;
 margin:clamp(22px,4vw,40px) 0 clamp(10px,1.6vw,16px)}}
.group .ar{{font:700 clamp(22px,4.6vw,38px)/1 EM;color:var(--blue)}}
.group .en{{direction:ltr;font:500 clamp(9px,1.4vw,12px) PP;letter-spacing:.3em;
 color:var(--muted)}}
.group::after{{content:"";flex:1;height:2px;background:var(--blue);opacity:.22}}

/* section heading: arabic right, rule running left */
section{{scroll-margin-top:clamp(92px,17vw,132px)}}
.sh{{display:flex;align-items:center;gap:10px;margin:clamp(16px,2.6vw,26px) 0 clamp(8px,1.4vw,14px)}}
.sh h2{{font:700 clamp(15px,2.9vw,25px)/1 EM;color:var(--blue);white-space:nowrap}}
.sh .e{{direction:ltr;font:500 clamp(8px,1.2vw,11px) PP;letter-spacing:.2em;
 color:var(--muted);white-space:nowrap}}
.sh i{{flex:1;height:1px;background:linear-gradient(to left,var(--blue),var(--rule))}}

/* items */
.grid{{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;
 gap:clamp(10px,1.8vw,22px) clamp(6px,1.2vw,16px)}}
.item{{flex:0 0 auto;width:clamp(118px,22vw,200px)}}
.item{{display:flex;flex-direction:column;align-items:center;text-align:center}}
.shot{{width:100%;height:clamp(100px,20vw,190px);display:flex;
 align-items:flex-end;justify-content:center}}
.shot img{{max-width:100%;max-height:100%;object-fit:contain;display:block}}
.item h3{{font:600 clamp(12px,1.9vw,17px)/1.25 EM;color:var(--ink);margin-top:7px}}
.item .en{{direction:ltr;font:500 clamp(8px,1.15vw,11px)/1.3 PP;color:var(--muted);
 letter-spacing:.02em;margin-top:2px}}
.item .price{{direction:ltr;font:700 clamp(12px,1.9vw,17px) PP;color:var(--blue);margin-top:5px}}
.item .price span{{font:700 .62em PP;margin-inline-start:2px;letter-spacing:.04em}}

/* extras strip */
.extras{{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;
 gap:clamp(8px,1.4vw,14px) clamp(14px,3vw,34px)}}
.extras li{{display:flex;align-items:baseline;gap:7px}}
.extras b{{font:600 clamp(12px,1.8vw,16px) EM;color:var(--ink)}}
.extras em{{direction:ltr;font:500 clamp(8px,1.1vw,10px) PP;color:var(--muted);font-style:normal}}
.extras .price{{direction:ltr;font:700 clamp(12px,1.8vw,16px) PP;color:var(--blue)}}
.extras .price span{{font:700 .62em PP;margin-inline-start:2px}}

footer{{margin-top:clamp(26px,4vw,44px);border-top:1px solid var(--rule);
 padding:14px var(--pad) calc(20px + env(safe-area-inset-bottom));text-align:center}}
footer p{{font:600 clamp(10px,1.4vw,13px) EM;color:var(--muted)}}
footer .sub{{font:500 clamp(9px,1.2vw,11px) PP;color:#B6C0CE;margin-top:4px;direction:ltr}}

'''


def used_ids():
    ids = [i for _, _, secs in GROUPS for _, _, s in secs for i in s]
    return ids + EXTRAS


def subset_fonts(text_ar, text_latin):
    os.makedirs(f'{OUT}/fonts', exist_ok=True)
    jobs = [('fonts/ElMessiri-SemiBold.ttf', 'em-600.ttf', text_ar + text_latin),
            ('fonts/ElMessiri-Bold.ttf',     'em-700.ttf', text_ar + text_latin),
            ('fonts/Poppins-Medium.ttf',     'pp-500.ttf', text_latin),
            ('fonts/Poppins-Bold.ttf',       'pp-700.ttf', text_latin)]
    for src, dst, chars in jobs:
        font = TTFont(src)
        opts = subset.Options(layout_features='*', notdef_outline=True,
                              drop_tables=['FFTM'])
        s = subset.Subsetter(options=opts)
        s.populate(unicodes={ord(c) for c in set(chars)})
        s.subset(font)
        font.save(f'{OUT}/fonts/{dst}')
        a, b = os.path.getsize(src), os.path.getsize(f'{OUT}/fonts/{dst}')
        print(f'  {dst:<12} {a//1024:>4}KB -> {b//1024:>3}KB')


def main():
    items = {x['id']: x for x in json.load(open('items-light.json'))['data']}
    ids = used_ids()

    # fresh output tree
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(f'{OUT}/img', exist_ok=True)
    shutil.copy('logo_blue.png', f'{OUT}/logo.png')

    missing = []
    for i in ids:
        src = f'jpg/{i}.jpg'
        if os.path.exists(src):
            shutil.copy(src, f'{OUT}/img/{i}.jpg')
        elif i not in EXTRAS:
            missing.append(i)

    page = build_html(items)
    open(f'{OUT}/index.html', 'w', encoding='utf-8').write(page)

    # subset the fonts down to the glyphs this page actually uses
    txt = re.sub(r'<[^>]+>', ' ', re.sub(r'<style>.*?</style>', ' ', page, flags=re.S))
    txt += HOURS_AR + HOURS_EN + '0123456789٠١٢٣٤٥٦٧٨٩'
    ar = ''.join(c for c in txt if '؀' <= c <= 'ۿ')
    latin = ''.join(c for c in txt if c.isascii() and c.isprintable())
    print('fonts:')
    subset_fonts(ar, latin)

    kb = lambda p: os.path.getsize(p) // 1024
    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _, fs in os.walk(OUT) for f in fs)
    print(f'\nitems on page: {len([i for i in ids if i not in EXTRAS])}'
          f' + {len(EXTRAS)} extras')
    print('images missing:', missing or 'none')
    print(f'index.html {kb(f"{OUT}/index.html")}KB   site total {total//1024}KB')


if __name__ == '__main__':
    main()
