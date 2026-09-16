#!/usr/bin/env python3
"""Build the single-page web menu for Crepe & More - Al Rashid Mall.

One scrolling page, one section per full-width row, sized for an iPad held in
portrait. Item names, prices and photos come from the same data as the PDF
build (see build.py); prices in build.PRICE override the API where the
restaurant's own price list disagrees.

Both languages ship in the markup. The header switch sets data-lang on <html>,
and CSS decides which language is the heading and which is the small line under
it, and flips the page between RTL and LTR. The choice is remembered per
device: the page opens in English, and switches to Arabic only if that device
has chosen Arabic before.

Output goes to site/ : index.html, img/, fonts/, logo.png
"""
import json, os, re, shutil, html
from fontTools import subset
from fontTools.ttLib import TTFont

import build   # AR / EN / PRICE overrides and the item data

BLUE, INK, MUTED, RULE = '#2E5D95', '#1F3D63', '#8D9CB0', '#CBD6E5'
OUT = 'site'
HOURS_AR, HOURS_EN = '١٠ ص – ١٢ م', '10 AM – 12 AM'
BRANCH_AR, BRANCH_EN = 'الراشد مول', 'Al Rashid Mall'
TITLE_AR = 'كريب أند مور · الراشد مول — القائمة'
TITLE_EN = 'Crepe & More · Al Rashid Mall — Menu'

# section order, grouped; ids match the PDF build
GROUPS = [
    ('الطعام', 'FOOD', [
        ('كريب',        'CREPE',        [117, 1, 93, 2, 3, 89, 4]),
        ('بان كيك',     'PANCAKE',      [139, 7, 140, 138]),
        ('وافل',        'WAFFLE',       [133, 143, 142, 123]),
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
        ('موهيتو',        'MOJITO',      [173, 172, 67, 171]),
        ('ميلك شيك',      'MILKSHAKE',   [53, 54, 55, 56, 57, 58]),
        ('عصائر و سموثي', 'JUICE & SMOOTHIE', [59, 60, 61, 63, 64, 62, 176]),
    ]),
]
EXTRAS = []          # the إضافات strip was dropped from the menu
GROUP_SKIP = {'FOOD'}          # the page opens on food, so it needs no label

# Calories from the restaurant's own published list. Where an item is on the
# menu but absent from that list, the API's own figure is used as a fallback
# (see cal()); a few items have no figure anywhere and simply show none.
CAL = {
    117: 450, 1: 224, 93: 754, 2: 1150, 3: 420, 89: 380,
    139: 450, 7: 560, 140: 450, 138: 560,
    133: 240, 143: 520, 123: 180,
    21: 4, 22: 4, 161: 5, 23: 70, 24: 70, 25: 80, 20: 4, 26: 60, 27: 20,
    29: 180, 28: 200, 30: 140, 31: 260, 32: 180, 33: 50, 34: 50, 36: 5,
    50: 5, 40: 150, 167: 5, 41: 320, 42: 250, 43: 250, 44: 250, 51: 150,
    53: 465, 54: 550, 55: 450, 56: 470, 57: 420, 58: 410,
    173: 220, 172: 200, 67: 210, 171: 190,
    45: 300, 46: 350, 47: 350, 48: 375,
    59: 80, 60: 40, 61: 120, 64: 150, 62: 200, 147: 160, 63: 40, 158: 200,
    52: 150, 149: 140,
    17: 400, 18: 450, 19: 450,
    83: 300, 84: 400, 85: 400, 86: 500, 145: 150, 146: 200, 144: 350,
    129: 470, 12: 520, 14: 380, 164: 450,
}


E = html.escape


def slug(en):
    return re.sub(r'[^a-z0-9]+', '-', en.lower()).strip('-')


def name_ar(i, items):
    return build.AR.get(i, (items[i]['name_ar'] or '').strip())


def name_en(i, items):
    return build.EN.get(i, (items[i]['name_en'] or '').strip())


def cal(i, items):
    """Their list first, then the API's own figure; None if neither has one."""
    if i in CAL:
        return CAL[i]
    v = items[i].get('calories')
    return int(v) if v else None


def price(i, items):
    v = build.PRICE.get(i, items[i]['price'])
    return int(v) if float(v).is_integer() else round(float(v), 2)


def bi(ar, en):
    """Both languages side by side; CSS picks which one leads."""
    return (f'<span class="ar" lang="ar" dir="rtl">{E(ar)}</span>'
            f'<span class="en" lang="en" dir="ltr">{E(en)}</span>')


def cell(i, items):
    src = f'img/{i}.jpg'
    img = (f'<img src="{src}" alt="{E(name_en(i, items))}"'
           f' loading="lazy" decoding="async">'
           if os.path.exists(f'{OUT}/{src}') else '')
    return (f'<li class="item">'
            f'<div class="shot">{img}</div>'
            f'<p class="n ar" lang="ar" dir="rtl">{E(name_ar(i, items))}</p>'
            f'<p class="n en" lang="en" dir="ltr">{E(name_en(i, items))}</p>'
            f'<p class="price" dir="ltr">{price(i, items)}<span>SR</span></p>'
            f'{kcal(i, items)}'
            f'</li>')


def kcal(i, items):
    c = cal(i, items)
    if not c:
        return ''
    return (f'<p class="kcal" dir="ltr"><span>{c}</span>'
            f'<em class="ar" lang="ar">سعرة</em>'
            f'<em class="en" lang="en">kcal</em></p>')


def shead(ar, en):
    return f'<div class="sh"><h2 class="st">{bi(ar, en)}</h2><i></i></div>'


def build_html(items):
    nav, body = [], []
    for g_ar, g_en, secs in GROUPS:
        if g_en not in GROUP_SKIP:
            body.append(f'<h2 class="group" id="{slug(g_en)}">{bi(g_ar, g_en)}</h2>')
        for s_ar, s_en, ids in secs:
            sid = slug(s_en)
            nav.append(f'<a href="#{sid}">{bi(s_ar, s_en)}</a>')
            cells = ''.join(cell(i, items) for i in ids if i in items)
            body.append(f'<section id="{sid}">{shead(s_ar, s_en)}'
                        f'<ul class="grid">{cells}</ul></section>')

    ex = ''.join(
        f'<li><span class="ar" lang="ar" dir="rtl">{E(name_ar(i, items))}</span>'
        f'<span class="en" lang="en" dir="ltr">{E(name_en(i, items))}</span>'
        f'<span class="price" dir="ltr">{price(i, items)}<span>SR</span></span></li>'
        for i in EXTRAS if i in items)
    if ex:
        nav.append(f'<a href="#extras">{bi("إضافات", "EXTRAS")}</a>')
        body.append(f'<section id="extras">{shead("إضافات", "EXTRAS")}'
                    f'<ul class="extras">{ex}</ul></section>')

    return f'''<!doctype html>
<html lang="en" dir="ltr" data-lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(TITLE_EN)}</title>
<meta name="description" content="قائمة كريب أند مور - فرع الراشد مول. Crepe &amp; More menu, Al Rashid Mall.">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<meta name="theme-color" content="#ffffff">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Crepe &amp; More">
<link rel="icon" href="logo.png">
<link rel="apple-touch-icon" href="logo.png">
<script>
/* Apply the saved language before first paint so the page never flashes in the
   wrong one. localStorage can throw in private mode, hence the try. */
(function(){{try{{var l=localStorage.getItem('menuLang');if(l==='en'||l==='ar'){{
var r=document.documentElement;r.setAttribute('data-lang',l);
r.setAttribute('lang',l);r.setAttribute('dir',l==='ar'?'rtl':'ltr');}}}}catch(e){{}}}})();
</script>
<style>{CSS}</style>
</head>
<body>
<header class="top">
 <div class="bar">
  <img class="logo" src="logo.png" alt="Crepe &amp; More">
  <div class="where">{bi(BRANCH_AR, BRANCH_EN)}</div>
  <div class="hours">{bi(HOURS_AR, HOURS_EN)}</div>
  <button class="langsw" type="button">
   <span class="ar" lang="ar" dir="rtl">عربي</span>
   <span class="en" lang="en" dir="ltr">English</span>
  </button>
 </div>
 <nav class="jump">{''.join(nav)}</nav>
</header>
<main>{''.join(body)}</main>
<footer>
 <p class="note">{bi('الأسعار بالريال السعودي', 'Prices in Saudi Riyal')}</p>
 <p class="sub">{bi('كريب أند مور — فرع الراشد مول', 'Crepe & More — Al Rashid Mall')}</p>
</footer>
<script>
(function(){{
 var r=document.documentElement;
 var T={{ar:{json.dumps(TITLE_AR, ensure_ascii=False)},en:{json.dumps(TITLE_EN, ensure_ascii=False)}}};
 var btn=document.querySelector('.langsw');
 var L={{ar:'Switch to English',en:'التبديل إلى العربية'}};
 function set(l){{
  r.setAttribute('data-lang',l);r.setAttribute('lang',l);
  r.setAttribute('dir',l==='ar'?'rtl':'ltr');
  document.title=T[l];btn.setAttribute('aria-label',L[l]);
  try{{localStorage.setItem('menuLang',l)}}catch(e){{}}
 }}
 set(r.getAttribute('data-lang')||'en');
 btn.addEventListener('click',function(){{
  set(r.getAttribute('data-lang')==='ar'?'en':'ar');
 }});
}})();
</script>
</body>
</html>'''


CSS = f'''
@font-face{{font-family:EM;src:url('fonts/em-600.ttf') format('truetype');font-weight:600;font-display:swap}}
@font-face{{font-family:EM;src:url('fonts/em-700.ttf') format('truetype');font-weight:700;font-display:swap}}
@font-face{{font-family:PP;src:url('fonts/pp-500.ttf') format('truetype');font-weight:500;font-display:swap}}
@font-face{{font-family:PP;src:url('fonts/pp-700.ttf') format('truetype');font-weight:700;font-display:swap}}

*{{box-sizing:border-box;margin:0;padding:0}}
:root{{color-scheme:light;--blue:{BLUE};--ink:{INK};--muted:{MUTED};--rule:{RULE};
 --pad:clamp(12px,3vw,28px)}}
html{{color-scheme:light;background:#fff;scroll-behavior:smooth;
 -webkit-text-size-adjust:100%}}
body{{background:#fff;color:var(--ink);font-family:EM,PP,system-ui,sans-serif;
 -webkit-tap-highlight-color:transparent}}

/* ---- header ---- */
.top{{position:sticky;top:0;z-index:10;background:#fff;
 border-bottom:1px solid var(--rule);padding-top:env(safe-area-inset-top)}}
/* the brand bar keeps a fixed layout in both languages: logo left, switch
   right. Only the text inside it swaps language. */
.bar{{direction:ltr;display:flex;align-items:center;gap:clamp(8px,2.2vw,20px);
 padding:10px var(--pad) 8px;max-width:1500px;margin:0 auto}}
.where{{text-align:left}}
.logo{{height:clamp(26px,5vw,44px);width:auto;display:block;flex:none}}
.where{{margin-inline-end:auto;min-width:0}}
.hours{{text-align:end;flex:none}}
.where,.hours{{display:flex;flex-direction:column;line-height:1.15}}

/* ---- language switch ---- */
.langsw{{flex:none;font-weight:700;font-size:clamp(11px,1.7vw,14px);color:#fff;
 background:var(--blue);border:0;border-radius:999px;cursor:pointer;
 padding:8px clamp(12px,1.9vw,18px);min-height:36px;line-height:1;
 white-space:nowrap;-webkit-appearance:none}}
.langsw:active{{opacity:.85}}
.langsw .ar{{font-family:EM}}
.langsw .en{{font-family:PP;letter-spacing:.03em}}
/* show the language you would switch to, not the one you are on */
[data-lang=ar] .langsw .ar{{display:none}}
[data-lang=en] .langsw .en{{display:none}}

/* ---- quick jump ---- */
.jump{{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;
 padding:0 var(--pad) 9px;max-width:1500px;margin:0 auto}}
.jump::-webkit-scrollbar{{display:none}}
.jump a{{flex:none;text-decoration:none;background:#EEF3F9;border-radius:999px;
 padding:5px clamp(9px,1.6vw,14px);white-space:nowrap;color:var(--blue)}}
.jump a:active{{background:var(--blue);color:#fff}}

main{{max-width:1500px;margin:0 auto;padding:0 var(--pad) 8px}}

/* ---- group divider (DRINKS) ---- */
.group{{display:flex;align-items:baseline;gap:10px;
 margin:clamp(22px,4vw,40px) 0 clamp(10px,1.6vw,16px)}}
.group::after{{content:"";flex:1;height:2px;background:var(--blue);opacity:.22}}

/* ---- section heading ---- */
section{{scroll-margin-top:clamp(96px,18vw,140px)}}
.sh{{display:flex;align-items:center;gap:10px;
 margin:clamp(16px,2.6vw,26px) 0 clamp(8px,1.4vw,14px)}}
.st{{display:flex;align-items:baseline;gap:9px;min-width:0}}
.sh i{{flex:1;height:1px}}

/* ---- items ---- */
.grid{{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;
 gap:clamp(10px,1.8vw,22px) clamp(6px,1.2vw,16px)}}
.item{{flex:0 0 auto;width:clamp(118px,22vw,200px);
 display:flex;flex-direction:column;align-items:center;text-align:center}}
.shot{{order:0;width:100%;height:clamp(100px,20vw,190px);display:flex;
 align-items:flex-end;justify-content:center}}
.shot img{{max-width:100%;max-height:100%;object-fit:contain;display:block}}
.item .n{{line-height:1.25}}
.item .price{{order:3;font:700 clamp(12px,1.9vw,17px) PP;color:var(--blue);margin-top:5px}}
.item .price span{{font:700 .62em PP;margin-inline-start:2px;letter-spacing:.04em}}
.item .kcal{{order:4;display:flex;justify-content:center;align-items:baseline;gap:3px;
 margin-top:3px;font:500 clamp(8px,1.1vw,10.5px) PP;color:#A9B5C4}}
.item .kcal em{{font-style:normal}}
.item .kcal .ar{{font-family:EM;font-size:1.1em}}
[data-lang=ar] .item .kcal .en{{display:none}}
[data-lang=en] .item .kcal .ar{{display:none}}

/* ---- extras ---- */
.extras{{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;
 gap:clamp(8px,1.4vw,14px) clamp(14px,3vw,34px)}}
.extras li{{display:flex;align-items:baseline;gap:7px}}
.extras .price{{order:3;font:700 clamp(12px,1.8vw,16px) PP;color:var(--blue)}}
.extras .price span{{font:700 .62em PP;margin-inline-start:2px}}

footer{{margin-top:clamp(26px,4vw,44px);border-top:1px solid var(--rule);
 padding:14px var(--pad) calc(20px + env(safe-area-inset-bottom));text-align:center}}
footer p{{display:flex;justify-content:center}}
footer .sub{{margin-top:4px}}

/* ================= language swap =================
   Every label ships in both languages; these rules pick which one leads. */

/* one language only in the jump strip and footer */
[data-lang=ar] .jump .en,[data-lang=ar] footer .en{{display:none}}
[data-lang=en] .jump .ar,[data-lang=en] footer .ar{{display:none}}
[data-lang=ar] .jump a{{font:600 clamp(11px,1.8vw,14px) EM}}
[data-lang=en] .jump a{{font:600 clamp(10px,1.5vw,12.5px) PP;letter-spacing:.06em}}
[data-lang=ar] footer .note{{font:600 clamp(10px,1.4vw,13px) EM;color:var(--muted)}}
[data-lang=en] footer .note{{font:500 clamp(10px,1.35vw,12.5px) PP;color:var(--muted)}}
[data-lang=ar] footer .sub{{font:600 clamp(9px,1.2vw,11px) EM;color:#B6C0CE}}
[data-lang=en] footer .sub{{font:500 clamp(9px,1.2vw,11px) PP;color:#B6C0CE}}

/* branch + hours: lead language large, the other small beneath */
[data-lang=ar] .where .ar{{order:1;font:700 clamp(14px,2.5vw,19px) EM;color:var(--blue)}}
[data-lang=ar] .where .en{{order:2;font:500 clamp(8px,1.3vw,10px) PP;
 letter-spacing:.14em;color:var(--muted);text-transform:uppercase}}
[data-lang=en] .where .en{{order:1;font:700 clamp(13px,2.2vw,18px) PP;color:var(--blue)}}
[data-lang=en] .where .ar{{order:2;font:600 clamp(9px,1.4vw,11px) EM;color:var(--muted)}}
[data-lang=ar] .hours .ar{{order:1;font:700 clamp(12px,2vw,16px) EM;color:var(--ink)}}
[data-lang=ar] .hours .en{{order:2;font:500 clamp(8px,1.3vw,10px) PP;
 letter-spacing:.1em;color:var(--muted)}}
[data-lang=en] .hours .en{{order:1;font:700 clamp(11px,1.8vw,14px) PP;color:var(--ink)}}
[data-lang=en] .hours .ar{{order:2;font:600 clamp(9px,1.4vw,11px) EM;color:var(--muted)}}

/* section + group headings */
[data-lang=ar] .st .ar,[data-lang=ar] .group .ar{{order:1}}
[data-lang=ar] .st .en,[data-lang=ar] .group .en{{order:2}}
[data-lang=en] .st .en,[data-lang=en] .group .en{{order:1}}
[data-lang=en] .st .ar,[data-lang=en] .group .ar{{order:2}}
[data-lang=ar] .st .ar{{font:700 clamp(15px,2.9vw,25px) EM;color:var(--blue);white-space:nowrap}}
[data-lang=ar] .st .en{{font:500 clamp(8px,1.2vw,11px) PP;letter-spacing:.2em;
 color:var(--muted);white-space:nowrap}}
[data-lang=en] .st .en{{font:700 clamp(14px,2.5vw,22px) PP;color:var(--blue);
 letter-spacing:.02em;white-space:nowrap}}
[data-lang=en] .st .ar{{font:600 clamp(11px,1.7vw,15px) EM;color:var(--muted);white-space:nowrap}}
[data-lang=ar] .group .ar{{font:700 clamp(22px,4.6vw,38px) EM;color:var(--blue)}}
[data-lang=ar] .group .en{{font:500 clamp(9px,1.4vw,12px) PP;letter-spacing:.3em;color:var(--muted)}}
[data-lang=en] .group .en{{font:700 clamp(20px,4vw,34px) PP;color:var(--blue);letter-spacing:.02em}}
[data-lang=en] .group .ar{{font:600 clamp(13px,2.2vw,18px) EM;color:var(--muted)}}

/* the heading rule runs away from the text, whichever side that is */
[data-lang=ar] .sh i{{background:linear-gradient(to left,var(--blue),var(--rule))}}
[data-lang=en] .sh i{{background:linear-gradient(to right,var(--blue),var(--rule))}}

/* item names */
[data-lang=ar] .item .n.ar{{order:1;font:600 clamp(12px,1.9vw,17px) EM;
 color:var(--ink);margin-top:7px}}
[data-lang=ar] .item .n.en{{order:2;font:500 clamp(8px,1.15vw,11px) PP;
 color:var(--muted);letter-spacing:.02em;margin-top:2px}}
[data-lang=en] .item .n.en{{order:1;font:600 clamp(11px,1.75vw,16px) PP;
 color:var(--ink);margin-top:7px}}
[data-lang=en] .item .n.ar{{order:2;font:600 clamp(9.5px,1.4vw,12.5px) EM;
 color:var(--muted);margin-top:2px}}

/* extras entries */
[data-lang=ar] .extras .ar{{order:1;font:600 clamp(12px,1.8vw,16px) EM;color:var(--ink)}}
[data-lang=ar] .extras .en{{order:2;font:500 clamp(8px,1.1vw,10px) PP;color:var(--muted)}}
[data-lang=en] .extras .en{{order:1;font:600 clamp(11px,1.6vw,15px) PP;color:var(--ink)}}
[data-lang=en] .extras .ar{{order:2;font:600 clamp(9.5px,1.3vw,12px) EM;color:var(--muted)}}

/* very narrow phones: the hours would crowd the switch out */
@media (max-width:420px){{.hours{{display:none}}}}

/* Some TV browsers (Android TV, Tizen, webOS) and phone "auto dark theme"
   features repaint a light page dark. This is a white-branded menu whose
   product photos are cut out onto white, so a dark ground breaks it. Re-assert
   the light ground in every mode those features use. */
@media (prefers-color-scheme:dark){{
 html,body{{background:#fff;color:var(--ink)}}
 .top{{background:#fff}}
 .langsw{{background:var(--blue);color:#fff}}
 .jump a{{background:#EEF3F9;color:var(--blue)}}
 .item .n.ar,.item .n.en{{color:inherit}}
}}
@media (forced-colors:active){{
 html,body,.top,main,section,.item,.shot{{forced-color-adjust:none;background:#fff}}
 body,.item .n{{color:var(--ink)}}
 .jump a{{forced-color-adjust:none;background:#EEF3F9;color:var(--blue)}}
 .langsw{{forced-color-adjust:none;background:var(--blue);color:#fff}}
 .item .price,.extras .price,.st .ar,.st .en,.group .ar,.group .en{{
  forced-color-adjust:none;color:var(--blue)}}
 .item .kcal,.item .n.en{{forced-color-adjust:none;color:#A9B5C4}}
 .shot img{{forced-color-adjust:none}}
}}
'''


def used_ids():
    return [i for _, _, secs in GROUPS for _, _, s in secs for i in s] + EXTRAS


def subset_fonts(text_ar, text_latin):
    os.makedirs(f'{OUT}/fonts', exist_ok=True)
    jobs = [('fonts/ElMessiri-SemiBold.ttf', 'em-600.ttf', text_ar + text_latin),
            ('fonts/ElMessiri-Bold.ttf',     'em-700.ttf', text_ar + text_latin),
            ('fonts/Poppins-Medium.ttf',     'pp-500.ttf', text_latin),
            ('fonts/Poppins-Bold.ttf',       'pp-700.ttf', text_latin)]
    for src, dst, chars in jobs:
        font = TTFont(src)
        s = subset.Subsetter(options=subset.Options(
            layout_features='*', notdef_outline=True, drop_tables=['FFTM']))
        s.populate(unicodes={ord(c) for c in set(chars)})
        s.subset(font)
        font.save(f'{OUT}/fonts/{dst}')
        print(f'  {dst:<12} {os.path.getsize(src)//1024:>4}KB -> '
              f'{os.path.getsize(f"{OUT}/fonts/{dst}")//1024:>3}KB')


def main():
    items = {x['id']: x for x in json.load(open('items-light.json'))['data']}
    ids = used_ids()

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(f'{OUT}/img', exist_ok=True)
    shutil.copy('logo_blue.png', f'{OUT}/logo.png')

    missing = []
    for i in ids:
        if os.path.exists(f'jpg/{i}.jpg'):
            shutil.copy(f'jpg/{i}.jpg', f'{OUT}/img/{i}.jpg')
        elif i not in EXTRAS:
            missing.append(i)

    page = build_html(items)
    open(f'{OUT}/index.html', 'w', encoding='utf-8').write(page)

    txt = re.sub(r'<[^>]+>', ' ',
                 re.sub(r'<(style|script)>.*?</\1>', ' ', page, flags=re.S))
    txt += HOURS_AR + HOURS_EN + TITLE_AR + TITLE_EN + 'عربيEN'
    txt += '0123456789٠١٢٣٤٥٦٧٨٩'
    ar = ''.join(c for c in txt if '؀' <= c <= 'ۿ')
    latin = ''.join(c for c in txt if c.isascii() and c.isprintable())
    print('fonts:')
    subset_fonts(ar, latin)

    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _, fs in os.walk(OUT) for f in fs)
    print(f'\nitems: {len([i for i in ids if i not in EXTRAS])} + {len(EXTRAS)} extras')
    print('images missing:', missing or 'none')
    print(f'index.html {os.path.getsize(f"{OUT}/index.html")//1024}KB'
          f'   site total {total//1024}KB')


if __name__ == '__main__':
    main()
