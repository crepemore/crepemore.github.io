#!/usr/bin/env python3
"""Build the two TV menu boards -> site/tv1/ (food) and site/tv2/ (drinks).

A wall screen is read from across the room and nobody touches it, so these are
not the tablet page scaled up: type is sized for distance and each screen
slides through its half of the menu on its own, one board at a time.

The split is food on one screen, drinks on the other - the natural division for
two screens side by side, and it keeps every section whole.

The header is deliberately bare: logo and which board this is. The branch name
and opening hours are not on it, because a customer standing in the shop
already knows both, and the room they take is better spent on the menu.

Each page is laid out against a fixed 1920x1080 stage that is scaled to
whatever the panel reports, so a 1080p and a 4K TV render identically. Items
carry both languages at once; there is no switch, because there is nothing to
tap. Photos are shared with the tablet page (../img/), so replacing a photo
updates every screen.

site/tv/ is kept as a small chooser so the older single-board link still works.
"""
import json, os, html
import build            # AR / EN / PRICE overrides
import build_web as W   # section order, name/price/calorie helpers

BLUE, INK, MUTED, RULE = '#2E5D95', '#1F3D63', '#8D9CB0', '#CBD6E5'
PER_ROW = 5              # items across the stage
MAX_ROWS = 2             # rows of items per board - what fits the stage
MAX_SECTIONS = 2         # per board, so a board never looks like a jumble
DWELL_MS = 11000         # how long each board stays up
EXTRAS = W.EXTRAS

E = html.escape

PAGES = [
    dict(dir='tv1', ar='الطعام', en='FOOD',
         title='Crepe & More — Food board', group=0, extras=False),
    dict(dir='tv2', ar='المشروبات', en='DRINKS',
         title='Crepe & More — Drinks board', group=1, extras=True),
]


def item(i, items):
    img = (f'<img src="../img/{i}.jpg" alt="">'
           if os.path.exists(f'site/img/{i}.jpg') else '')
    c = W.cal(i, items)
    kcal = f'<p class="k">{c}<span> kcal</span></p>' if c else '<p class="k"></p>'
    return (f'<li><div class="sh">{img}</div>'
            f'<p class="a">{E(W.name_ar(i, items))}</p>'
            f'<p class="e">{E(W.name_en(i, items))}</p>'
            f'<p class="p">{W.price(i, items)}<span>SR</span></p>'
            f'{kcal}</li>')


def rows_for(n):
    return -(-n // PER_ROW)          # ceil


def sections_of(p):
    """This half of the menu, plus the extras strip on the drinks screen."""
    out = [(a, e, list(ids)) for a, e, ids in W.GROUPS[p['group']][2]]
    if p['extras']:
        out.append(('إضافات', 'EXTRAS', list(EXTRAS)))
    return out


def boards(p):
    """Pack sections into boards, keeping menu order.

    Capacity is counted in rows of items, not items: Frappe (4) plus Milkshake
    (6) is ten items but three rows, which overflows the stage. A section is
    only split across boards when it cannot fit one on its own."""
    out, cur, used = [], [], 0

    def flush():
        nonlocal cur, used
        if cur:
            out.append(cur); cur, used = [], 0

    for s_ar, s_en, ids in sections_of(p):
        if s_en == 'EXTRAS':                       # one compact strip, one row
            if used + 1 > MAX_ROWS or len(cur) >= MAX_SECTIONS:
                flush()
            cur.append((s_ar, s_en, ids)); used += 1
            continue
        if rows_for(len(ids)) > MAX_ROWS:           # needs boards of its own
            flush()
            per = MAX_ROWS * PER_ROW
            for k in range(0, len(ids), per):
                out.append([(s_ar, s_en, ids[k:k + per])])
            continue
        r = rows_for(len(ids))
        if used + r > MAX_ROWS or len(cur) >= MAX_SECTIONS:
            flush()
        cur.append((s_ar, s_en, ids)); used += r
    flush()
    return out


def section_html(s_ar, s_en, ids, items):
    if s_en == 'EXTRAS':
        body = ''.join(
            f'<li><b>{E(W.name_ar(i, items))}</b>'
            f'<em>{E(W.name_en(i, items))}</em>'
            f'<span>{W.price(i, items)}<i>SR</i></span></li>'
            for i in ids if i in items)
        ul = f'<ul class="x">{body}</ul>'
    else:
        ul = f'<ul>{"".join(item(i, items) for i in ids)}</ul>'
    return (f'<section><div class="t"><h2>{E(s_ar)}</h2>'
            f'<span>{E(s_en)}</span><i></i></div>{ul}</section>')


def page(p, items):
    bs = boards(p)
    panels = ''.join(
        f'<div class="board{" on" if n == 0 else ""}">'
        + ''.join(section_html(a, e, ids, items) for a, e, ids in b)
        + '</div>' for n, b in enumerate(bs))
    dots = ''.join(f'<i{" class=on" if n == 0 else ""}></i>'
                   for n in range(len(bs)))
    return f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(p['title'])}</title>
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="../logo.png">
<style>{CSS}</style>
</head>
<body>
<div id="stage">
 <header>
  <img src="../logo.png" alt="Crepe &amp; More">
  <div class="s"><b>{p['ar']}</b><span>{p['en']}</span></div>
 </header>
 <main>{panels}</main>
 <footer><div class="dots">{dots}</div>
  <p>الأسعار بالريال السعودي · Prices in Saudi Riyal</p></footer>
</div>
<script>
(function(){{
 var stage=document.getElementById('stage');
 function fit(){{
  var s=Math.min(innerWidth/1920, innerHeight/1080);
  stage.style.transform='scale('+s+')';
  stage.style.left=((innerWidth-1920*s)/2)+'px';
  stage.style.top=((innerHeight-1080*s)/2)+'px';
 }}
 addEventListener('resize',fit); fit();

 var boards=document.querySelectorAll('.board'),
     dots=document.querySelectorAll('.dots i'), at=0, timer;
 function show(n){{
  boards[at].className='board'; dots[at].className='';
  at=(n+boards.length)%boards.length;
  boards[at].className='board on'; dots[at].className='on';
 }}
 function next(){{ show(at+1); }}
 function go(n){{ show(n); clearInterval(timer); timer=setInterval(next,{DWELL_MS}); }}
 timer=setInterval(next,{DWELL_MS});

 // handy while positioning the screen: step through by hand
 addEventListener('keydown',function(e){{
  if(e.key==='ArrowRight'||e.key==='ArrowDown'||e.key===' ') go(at+1);
  if(e.key==='ArrowLeft'||e.key==='ArrowUp') go(at-1);
 }});
 addEventListener('click',function(){{ go(at+1); }});
}})();
</script>
</body>
</html>'''


CHOOSER = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Crepe &amp; More — TV boards</title>
<meta name="color-scheme" content="light">
<link rel="icon" href="../logo.png">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html{{color-scheme:light;background:#fff}}
body{{background:#fff;color:{INK};font-family:system-ui,sans-serif;
 min-height:100vh;display:flex;flex-direction:column;align-items:center;
 justify-content:center;gap:34px;padding:40px;text-align:center}}
img{{height:74px}}
p{{color:{MUTED};font-size:19px;max-width:46ch;line-height:1.5}}
.r{{display:flex;gap:22px;flex-wrap:wrap;justify-content:center}}
a{{display:block;min-width:290px;padding:30px 44px;border-radius:18px;
 background:{BLUE};color:#fff;text-decoration:none;font-size:34px;font-weight:700}}
a span{{display:block;font-size:16px;font-weight:500;opacity:.8;margin-top:8px;
 letter-spacing:.14em}}
</style></head>
<body>
<img src="../logo.png" alt="Crepe &amp; More">
<p>Two screens. Open one link on each TV and put the browser in full screen.</p>
<div class="r">
 <a href="../tv1/">الطعام<span>FOOD BOARD</span></a>
 <a href="../tv2/">المشروبات<span>DRINKS BOARD</span></a>
</div>
</body></html>'''


CSS = f'''
@font-face{{font-family:EM;src:url('../fonts/em-600.ttf') format('truetype');font-weight:600}}
@font-face{{font-family:EM;src:url('../fonts/em-700.ttf') format('truetype');font-weight:700}}
@font-face{{font-family:PP;src:url('../fonts/pp-500.ttf') format('truetype');font-weight:500}}
@font-face{{font-family:PP;src:url('../fonts/pp-700.ttf') format('truetype');font-weight:700}}

*{{box-sizing:border-box;margin:0;padding:0}}
html{{color-scheme:light;background:#fff}}
body{{background:#fff;color:{INK};font-family:EM,PP,sans-serif;overflow:hidden;
 width:100vw;height:100vh}}

#stage{{position:absolute;width:1920px;height:1080px;transform-origin:0 0;
 background:#fff;display:flex;flex-direction:column;padding:0 64px}}

/* bare header: the logo, and which board this is. No rule underneath - the
   menu starts straight after it. */
header{{flex:none;height:96px;display:flex;align-items:center;direction:ltr}}
header img{{height:64px;width:auto}}
header .s{{margin-left:auto;text-align:right;line-height:1.05}}
header .s b{{display:block;font:700 44px EM;color:{BLUE}}}
header .s span{{display:block;font:700 16px PP;letter-spacing:.3em;color:{MUTED}}}

main{{flex:1;position:relative;min-height:0}}
.board{{position:absolute;inset:0;display:flex;flex-direction:column;
 justify-content:center;gap:18px;opacity:0;visibility:hidden;
 transition:opacity .5s ease}}
.board.on{{opacity:1;visibility:visible}}

.t{{display:flex;align-items:baseline;gap:18px;margin:0 0 10px}}
.t h2{{font:700 42px/1.1 EM;color:{BLUE};white-space:nowrap}}
.t span{{direction:ltr;font:700 20px PP;letter-spacing:.26em;color:{MUTED};white-space:nowrap}}
.t i{{flex:1;height:2px;background:linear-gradient(to left,{BLUE},{RULE})}}

section ul{{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;
 gap:26px 18px}}
section li{{width:336px;display:flex;flex-direction:column;align-items:center;
 text-align:center}}
.sh{{width:100%;height:204px;display:flex;align-items:flex-end;justify-content:center}}
.sh img{{max-width:100%;max-height:100%;object-fit:contain;display:block}}
.a{{font:600 34px/1.2 EM;color:{INK};margin-top:12px}}
.e{{direction:ltr;font:500 21px/1.25 PP;color:{MUTED};margin-top:3px}}
.p{{direction:ltr;font:700 42px PP;color:{BLUE};margin-top:8px}}
.p span{{font:700 .55em PP;margin-left:4px;letter-spacing:.04em}}
.k{{direction:ltr;font:500 20px PP;color:#A9B5C4;margin-top:3px;min-height:24px}}

/* extras strip */
ul.x{{gap:20px 46px}}
ul.x li{{width:auto;flex-direction:row;align-items:baseline;gap:12px}}
ul.x b{{font:600 32px EM;color:{INK}}}
ul.x em{{direction:ltr;font:500 19px PP;color:{MUTED};font-style:normal}}
ul.x span{{direction:ltr;font:700 32px PP;color:{BLUE}}}
ul.x i{{font:700 .55em PP;font-style:normal;margin-left:3px}}

footer{{flex:none;height:62px;display:flex;align-items:center;
 justify-content:space-between;direction:ltr}}
footer p{{font:600 19px EM;color:{MUTED};direction:rtl}}
.dots{{display:flex;gap:9px}}
.dots i{{width:11px;height:11px;border-radius:50%;background:{RULE};
 transition:background .3s,width .3s}}
.dots i.on{{background:{BLUE};width:30px;border-radius:6px}}
'''


def main():
    items = {x['id']: x for x in json.load(open('items-light.json'))['data']}
    for p in PAGES:
        d = f"site/{p['dir']}"
        os.makedirs(d, exist_ok=True)
        open(f'{d}/index.html', 'w', encoding='utf-8').write(page(p, items))
        bs = boards(p)
        n = sum(len(ids) for b in bs for _, _, ids in b)
        print(f"{p['dir']}/  {p['en']:<7} {len(bs)} boards, {n} items, "
              f"{len(bs)*DWELL_MS/1000:.0f}s loop "
              f"({os.path.getsize(f'{d}/index.html')//1024}KB)")
        for k, b in enumerate(bs, 1):
            print(f"      board {k}: "
                  + ' + '.join(f'{e}({len(i)})' for _, e, i in b))

    os.makedirs('site/tv', exist_ok=True)
    open('site/tv/index.html', 'w', encoding='utf-8').write(CHOOSER)
    print('\ntv/ kept as a chooser linking to both boards')


if __name__ == '__main__':
    main()
