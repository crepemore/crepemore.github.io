#!/usr/bin/env python3
"""Build a 2-page tablet menu PDF for Crepe & More - Al Rashid Mall (branch 7).

Data comes from menu.crepemoresa.com's public API (items-light / categories);
photos are the site's own product shots with the studio background removed.

Page 1 = food, page 2 = drinks. Each page is two "page columns"; sections are
assigned so both columns land on the same row count, which makes the section
gaps come out even. Page 1 runs 3 items per row, page 2 runs 4.
"""
import json, os, html

BLUE, INK, MUTED, RULE = '#2E5D95', '#1F3D63', '#8D9CB0', '#CBD6E5'
TILE_IDS = {76, 77, 78, 79, 80, 81, 82, 124}   # photo tiles, not cutouts

# ---- name overrides -------------------------------------------------------
# Source names run long, are inconsistently cased, or lack Arabic. Cells are
# ~22mm wide, so Arabic is tightened to one line and English to one line.
AR = {
    17:'ديك رومي وموزاريلا', 83:'كرواسون', 84:'كرواسون ديك رومي',
    85:'كرواسون حلومي', 86:'كرواسون تونة',
    129:'كلوب ديك رومي', 186:'كلوب ديك رومي بني', 12:'كلوب تونة',
    14:'كلوب تونة بني', 187:'كلوب دجاج تكا', 152:'كلوب فاهيتا',
    13:'كلوب مكسيكي', 165:'بانيني حلومي مشوي', 168:'شاباتا دجاج مكسيكي',
    184:'جامبو دجاج إيطالي', 153:'جامبو جبنة عكاوي', 164:'بانيني دجاج فاهيتا',
    181:'أفوكادو بالقشطة', 182:'أفوكادو ومانجا',
    193:'وافل بابل', 195:'سوفت آيس كريم', 149:'آيس كريم جيلاتو',
    7:'ميني بان كيك وفواكه', 138:'بان كيك بالفواكه', 140:'بان كيك أصلي',
    21:'قهوة اليوم', 34:'قهوة سعودية', 28:'كراميل ماكياتو',
    43:'آيس كراميل ماكياتو', 167:'آيس V60', 60:'ليموناضة',
    147:'سموثي خوخ', 67:'موهيتو باشن فروت', 63:'ليمون ونعناع', 35:'أعشاب',
    76:'بروتين فراولة', 77:'بروتين مانجو', 78:'بروتين تمر وشوفان',
    79:'بروتين سناكس', 80:'بروتين فانيليا', 81:'بروتين زبدة الفول',
    82:'بروتين سنيكرز', 178:'كوب ثلج', 99:'كود ريد',
}
EN = {
    83:'Butter / Cheese / Chocolate', 84:'Turkey & Mozzarella',
    85:'Halloumi Croissant', 86:'Tuna Croissant',
    129:'Turkey & Cheese Club', 186:'Turkey & Cheese (Brown)',
    12:'Tuna Club', 14:'Tuna Club (Brown)', 187:'Chicken Tikka Club',
    152:'Fajita Club', 13:'Mexican Club', 165:'Halloumi Pesto Panini',
    168:'Mexican Chicken Ciabatta', 184:'Italian Chicken Jumbo',
    153:'Jumbo Akkawi Cheese', 164:'Chicken Fajita Panini',
    181:'Avocado, Honey & Ashta', 182:'Avocado, Mango & Ashta',
    7:'Mini Pancake & Fruits', 138:'Pancake & Fruits',
    21:'Coffee of the Day', 34:'Saudi Coffee', 51:'Iced Matcha Latte',
    60:'Lemonade', 147:'Peach Smoothie', 67:'Passion Fruit Mojito',
    149:'Gelato', 76:'Strawberry Protein', 77:'Mango Protein',
    78:'Dates & Oats Protein', 79:'Snacks Protein', 80:'Vanilla Protein',
    81:'Peanut Butter Protein', 82:'Snickers Protein',
    178:'Ice Cup', 99:'Code Red', 102:'7 Up', 193:'Waffle Bubbles',
    195:'Soft Ice Cream', 167:'Iced V60', 161:'V60',
}

# ---- page structure -------------------------------------------------------
# Removed on request: Crepe Sandwich, Waffle Bubbles, the whole Signature
# section (avocados / fruit salad / pomegranate / crunchy cup), Soft Ice Cream,
# all four Popcorn flavours, Herbs, Sahlab, Peach Smoothie, and the whole
# Protein Drinks section. Waffle, Pancake, Savory Crepe and French Toast each
# stand as their own section; Gelato gets an Ice Cream section, and those last
# two one-item sections share a row rather than each taking a full one.
PAGES = [
    # Page 1 is laid out in bands rather than two independent columns: each
    # band puts one section on the right and the next one on the left, so the
    # order reads right-left, right-left down the page and the paired section
    # headings line up with each other.
    dict(ar='الطعام', en='FOOD', cols_n=4, img=20.8, cell=29.0, bands=[
        [('كريب', 'CREPE', [117, 1, 93, 2, 3, 89, 4]),
         ('بان كيك', 'PANCAKE', [139, 7, 140, 138])],
        [('وافل', 'WAFFLE', [143, 142, 123]),
         ('فرنش توست', 'FRENCH TOAST', [144])],
        [('كريب مالح', 'SAVORY CREPE', [17, 18, 19]),
         ('مخبوزات', 'BAKERY', [83, 84, 85, 86, 145, 146])],
        [('ساندوتش', 'SANDWICHES', [129, 12, 14, 184, 164]),
         ('آيس كريم', 'ICE CREAM', [149])],
    ]),
    dict(ar='المشروبات', en='DRINKS', cols_n=4, img=17.8, cell=26.0, cols=[
        [
            ('مشروبات ساخنة', 'HOT DRINKS',
             [21, 22, 20, 161, 23, 24, 25, 26, 27, 29, 28, 30, 32, 31, 33, 34,
              36, 37]),
            ('مشروبات مثلجة', 'ICED DRINKS', [50, 40, 167, 41, 42, 43, 44, 49, 51]),
        ],
        [
            ('فرابيه', 'FRAPPE', [45, 46, 47, 48]),
            ('ميلك شيك', 'MILKSHAKE', [53, 54, 55, 56, 57, 58]),
            ('عصائر و سموثي', 'JUICE & SMOOTHIE', [59, 60, 61, 63, 64, 62, 176]),
            ('موهيتو', 'MOJITO', [173, 172, 67, 171]),
            ('مشروبات باردة', 'COLD DRINKS', [52, 91]),
        ],
    ], extras=[100, 99, 101, 102, 159, 178]),
]


def img_for(i):
    """Cutouts are flattened onto white and stored as JPEG: the page is pure
    white, so the result is identical on screen at a fraction of the size."""
    p = f'jpg/{i}.jpg'
    return (p, i in TILE_IDS) if os.path.exists(p) else (None, False)


# Prices come from the restaurant's own published list, which is ahead of the
# API in several places (the API still shows the old figures). These win.
PRICE = {
    21: 10,    # Coffee of the Day      8 -> 10
    32: 19,    # Pistachio Latte       17 -> 19
    34: 20,    # Saudi Coffee          10 -> 20
    36: 10,    # Tea                    8 -> 10
    59: 16,    # Orange Juice          12 -> 16
    61: 16,    # Fresh Apple Juice     14 -> 16
    93: 32,    # Dubai Crepe           28 -> 32
    123: 25,   # Waffle Balls          20 -> 25
    129: 15,   # Turkey & Cheese Club  14 -> 15
    133: 28,   # Classic Waffle        22 -> 28
    139: 28,   # Mini Pancake          24 -> 28
    140: 28,   # Original Pancake      24 -> 28
}


def price(v):
    n = int(v) if float(v).is_integer() else round(float(v), 2)
    return f'<span class=pr>{n}<i>SR</i></span>'


def cell_w(cols_n, half=False):
    """Usable cell width in mm: page 194mm wide, two 94mm columns, 1.4mm gaps.
    A paired (half-width) section splits its column, less a 4mm pair gap."""
    track = (94 - 4) / 2 if half else 94
    return (track - 1.4 * (cols_n - 1)) / cols_n


def fit(text, kind, w):
    """Step the type down so long names still hold one line at width w."""
    n = len(text) * 22.45 / w          # length normalised to a 4-up cell
    if kind == 'ar':
        return ' s2' if n > 23 else (' s1' if n > 19 else '')
    return ' s2' if n > 30 else (' s1' if n > 26 else '')


def cell(i, items, w):
    x = items[i]
    ar = AR.get(i, (x['name_ar'] or '').strip())
    en = EN.get(i, (x['name_en'] or '').strip())
    src, tile = img_for(i)
    im = f'<img class="{"tile" if tile else ""}" src="{src}">' if src else ''
    return (f'<div class=cell><div class=ph>{im}</div>'
            f'<div class="nar{fit(ar,"ar",w)}">{html.escape(ar)}</div>'
            f'<div class="nen{fit(en,"en",w)}">{html.escape(en)}</div>'
            f'{price(PRICE.get(i, x["price"]))}</div>')


def shead(ar, en):
    return (f'<div class=sh><span class=t>{html.escape(ar)}</span>'
            f'<span class=e>{html.escape(en)}</span><span class=r></span></div>')


def section(ar, en, ids, items, w, half=False):
    cells = ''.join(cell(i, items, w) for i in ids if i in items)
    cls = 'sec half' if half else 'sec'
    # 0.1mm shaved off so rounding never wraps a row early
    return (f'<div class="{cls}">{shead(ar, en)}'
            f'<div class=grid style="--cw:{w - 0.1:.2f}mm">{cells}</div></div>')


def column(entries, items, cols_n):
    """A column entry is one section, or a list of two sections to sit side by
    side - which keeps one- and two-item sections from each eating a whole row."""
    out = []
    for e in entries:
        if isinstance(e, list):
            n = max(1, cols_n // 2)
            out.append('<div class=pair>' + ''.join(
                section(a, en, ids, items, cell_w(n, half=True), half=True)
                for a, en, ids in e) + '</div>')
        else:
            a, en, ids = e
            out.append(section(a, en, ids, items, cell_w(cols_n)))
    return '<div class=col>' + ''.join(out) + '</div>'


def extras(ids, items):
    bits = []
    for i in ids:
        if i not in items:
            continue
        x = items[i]
        ar = AR.get(i, (x['name_ar'] or '').strip())
        en = EN.get(i, (x['name_en'] or '').strip())
        bits.append(f'<span class=x><b>{html.escape(ar)}</b>'
                    f'<em>{html.escape(en)}</em>'
                    f'{price(PRICE.get(i, x["price"]))}</span>')
    return (f'<div class=extras>{shead("إضافات", "EXTRAS")}'
            f'<div class=xrow>{"".join(bits)}</div></div>')


def bands(rows, items, cols_n):
    w = cell_w(cols_n)
    return '<div class=bands>' + ''.join(
        '<div class=band>' + ''.join(section(a, e, ids, items, w)
                                     for a, e, ids in b) + '</div>'
        for b in rows) + '</div>'


def page(p, items, n, total):
    cols = (bands(p['bands'], items, p['cols_n']) if p.get('bands')
            else '<div class=cols>' + ''.join(
                column(c, items, p['cols_n']) for c in p['cols']) + '</div>')
    ex = extras(p['extras'], items) if p.get('extras') else ''
    return f'''<div class=page style="--img:{p['img']}mm;--cell:{p['cell']}mm;--cols:{p['cols_n']};--hcols:{max(1, p['cols_n'] // 2)}">
 <div class=head>
  <div class=brand><img src="logo_blue.png"><span class=branch>الراشد مول<i>Al Rashid Mall</i></span></div>
  <div class=ptitle><div class=ar>{p['ar']}</div><div class=en>{p['en']}</div></div>
 </div>
 {cols}
 {ex}
 <div class=foot><span><b>الأسعار بالريال السعودي</b> · Prices in Saudi Riyal</span><span dir=ltr>{n} / {total}</span></div>
</div>'''


CSS = f'''
@font-face{{font-family:EM;src:url('fonts/ElMessiri-SemiBold.ttf');font-weight:600}}
@font-face{{font-family:EM;src:url('fonts/ElMessiri-Bold.ttf');font-weight:700}}
@font-face{{font-family:PP;src:url('fonts/Poppins-Regular.ttf');font-weight:400}}
@font-face{{font-family:PP;src:url('fonts/Poppins-Medium.ttf');font-weight:500}}
@font-face{{font-family:PP;src:url('fonts/Poppins-SemiBold.ttf');font-weight:600}}
@font-face{{font-family:PP;src:url('fonts/Poppins-Bold.ttf');font-weight:700}}
@page{{size:210mm 280mm;margin:0}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.page{{width:210mm;height:280mm;padding:7mm 8mm 5.5mm;display:flex;flex-direction:column;
 background:#fff;overflow:hidden;direction:rtl;font-family:EM,PP,sans-serif;break-after:page}}
.page:last-child{{break-after:auto}}

.head{{display:flex;align-items:flex-end;justify-content:space-between;flex:none;
 border-bottom:.5mm solid {BLUE};padding-bottom:2.2mm;margin-bottom:3.4mm}}
.brand{{display:flex;align-items:center;gap:2.6mm}}
.brand img{{height:8.4mm;display:block}}
.branch{{font:600 7pt EM;color:{INK};line-height:1.1}}
.branch i{{display:block;direction:ltr;font:500 4.8pt PP;color:{MUTED};
 font-style:normal;letter-spacing:.08em}}
.ptitle{{text-align:left}}
.ptitle .ar{{font:700 15pt EM;color:{BLUE};line-height:1}}
.ptitle .en{{direction:ltr;font:600 5.6pt PP;letter-spacing:.26em;color:{MUTED};margin-top:.4mm}}

.cols{{flex:1;display:flex;gap:6mm;align-items:stretch;min-height:0}}
/* banded layout: paired sections sit side by side with their headings level */
.bands{{flex:1;display:flex;flex-direction:column;justify-content:space-between;min-height:0}}
.band{{display:flex;gap:6mm;align-items:flex-start}}
.band>.sec{{flex:1;min-width:0}}
.col{{flex:1;display:flex;flex-direction:column;justify-content:space-between;min-width:0}}

/* section heading: Arabic title at the right, rule running left */
.sh{{display:flex;align-items:center;gap:1.8mm;margin-bottom:1.6mm}}
.sh .t{{font:700 9.5pt EM;color:{BLUE};line-height:1;white-space:nowrap}}
.sh .e{{direction:ltr;font:600 4.9pt PP;letter-spacing:.16em;color:{MUTED};white-space:nowrap}}
.sh .r{{flex:1;height:.3mm;background:linear-gradient(to left,{BLUE},{RULE})}}

/* two small sections sharing one row */
.pair{{display:flex;gap:4mm;align-items:flex-start}}
.pair>.sec{{flex:1;min-width:0}}

.grid{{display:flex;flex-wrap:wrap;justify-content:center;column-gap:1.4mm;row-gap:1mm}}
.cell{{width:var(--cw);flex:0 0 auto;height:var(--cell);text-align:center;min-width:0;display:flex;flex-direction:column;overflow:hidden}}
.ph{{height:var(--img);flex:none;display:flex;align-items:flex-end;justify-content:center}}
.ph img{{max-height:var(--img);max-width:100%;object-fit:contain;display:block}}
.ph img.tile{{height:calc(var(--img) - 1.4mm);width:calc(var(--img) - 1.4mm);
 object-fit:cover;border-radius:1.4mm}}
.nar{{font:600 6.5pt EM;color:{INK};line-height:1.1;margin-top:.9mm;
 white-space:nowrap;overflow:hidden}}
.nar.s1{{font-size:5.9pt}} .nar.s2{{font-size:5.3pt}}
.nen{{direction:ltr;font:500 4.4pt PP;color:{MUTED};line-height:1.15;
 letter-spacing:.02em;white-space:nowrap;overflow:hidden;margin-top:.35mm}}
.nen.s1{{font-size:4.0pt}} .nen.s2{{font-size:3.6pt}}
.pr{{direction:ltr;font:700 6.4pt PP;color:{BLUE};margin-top:auto;line-height:1}}
.pr i{{font:600 4.2pt PP;font-style:normal;margin-left:.3mm;letter-spacing:.04em}}

.extras{{flex:none;margin-top:3.4mm}}
.xrow{{display:flex;flex-wrap:wrap;gap:1.4mm 5mm}}
.x{{display:flex;align-items:baseline;gap:1.3mm}}
.x b{{font:600 7pt EM;color:{INK}}}
.x em{{direction:ltr;font:500 4.6pt PP;color:{MUTED};font-style:normal}}

.foot{{flex:none;display:flex;justify-content:space-between;align-items:center;
 margin-top:2.6mm;padding-top:1.6mm;border-top:.25mm solid {RULE};
 font:500 4.8pt PP;color:#A8B4C4}}
.foot b{{font:600 5.6pt EM;font-weight:600}}
'''


def main():
    items = {x['id']: x for x in json.load(open('items-light.json'))['data']}
    pages = ''.join(page(p, items, n + 1, len(PAGES)) for n, p in enumerate(PAGES))
    open('menu.html', 'w').write(
        '<!doctype html><meta charset=utf-8><title>Crepe &amp; More Menu</title>'
        f'<style>{CSS}</style>{pages}')

    def secs(p):
        groups = p['bands'] if p.get('bands') else p['cols']
        for g in groups:
            for e in g:
                for a, en, ids in (e if isinstance(e, list) else [e]):
                    yield a, en, ids

    used = {i for p in PAGES for _, _, ids in secs(p) for i in ids}
    used |= {i for p in PAGES for i in p.get('extras', [])}
    grid = used - set(PAGES[1]['extras'])
    print(f'grid items: {len(grid)}   extras: {len(PAGES[1]["extras"])}')
    print('grid items missing an image:',
          [i for i in grid if not img_for(i)[0]] or 'none')
    skipped = [(x['id'], x['name_en'], x['price'], x['available'])
               for x in items.values() if x['id'] not in used]
    print(f'\nleft out ({len(skipped)}):')
    for i, n, pr, av in sorted(skipped, key=lambda r: (r[3], r[0])):
        print(f'  id={i:<5} {n[:42]:<44} {pr:>6.0f} SR  available={av}')


if __name__ == '__main__':
    main()
