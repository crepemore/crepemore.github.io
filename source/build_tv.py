#!/usr/bin/env python3
"""Build the TV menu board -> site/tv/index.html

A wall-mounted 55" screen is read from across the room and nobody touches it,
so this is not the tablet page scaled up: nothing scrolls, type is sized for
distance, and the board cycles through the menu on its own.

The design is laid out against a fixed 1920x1080 stage and scaled to whatever
the TV reports, so it fills a 1080p or a 4K panel identically. Items carry both
languages at once - there is no switch, because there is nothing to tap.

Photos are shared with the tablet page (../img/), so replacing a photo updates
both.
"""
import json, os, re, shutil, html
import build            # AR / EN / PRICE overrides
import build_web as W   # section order, name/price/calorie helpers

OUT = 'site/tv'
BLUE, INK, MUTED, RULE = '#2E5D95', '#1F3D63', '#8D9CB0', '#CBD6E5'
PER_ROW = 5          # items across the stage
MAX_ROWS = 2         # rows of items per board - what actually fits the stage
MAX_SECTIONS = 2     # per board, so a board never looks like a jumble
DWELL_MS = 11000     # how long each board stays up

E = html.escape


def rows_for(n):
    return -(-n // PER_ROW)          # ceil


def boards():
    """Pack sections into boards, keeping menu order.

    Capacity is counted in rows of items, not items: Frappe (4) plus Milkshake
    (6) is ten items but three rows, which overflows the stage. A section is
    only split across boards when it cannot fit one on its own."""
    out, cur, used = [], [], 0

    def flush():
        nonlocal cur, used
        if cur:
            out.append(cur); cur, used = [], 0

    for _, _, secs in W.GROUPS:
        for s_ar, s_en, ids in secs:
            if rows_for(len(ids)) > MAX_ROWS:      # needs boards of its own
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


def item(i, items):
    src = f'../img/{i}.jpg'
    img = (f'<img src="{src}" alt="">'
           if os.path.exists(f'site/img/{i}.jpg') else '')
    c = W.cal(i, items)
    kcal = f'<p class="k">{c}<span> kcal</span></p>' if c else '<p class="k"></p>'
    return (f'<li><div class="sh">{img}</div>'
            f'<p class="a">{E(W.name_ar(i, items))}</p>'
            f'<p class="e">{E(W.name_en(i, items))}</p>'
            f'<p class="p">{W.price(i, items)}<span>SR</span></p>'
            f'{kcal}</li>')


def build(items):
    bs = boards()
    panels = ''
    for n, board in enumerate(bs):
        secs = ''
        for s_ar, s_en, ids in board:
            secs += (f'<section><div class="t">'
                     f'<h2>{E(s_ar)}</h2><span>{E(s_en)}</span><i></i></div>'
                     f'<ul>{"".join(item(i, items) for i in ids)}</ul></section>')
        panels += f'<div class="board{" on" if n == 0 else ""}">{secs}</div>'

    dots = ''.join(f'<i{" class=on" if n == 0 else ""}></i>' for n in range(len(bs)))
    return f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Crepe &amp; More — TV menu board</title>
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
  <div class="w"><b>الراشد مول</b><span>AL RASHID MALL</span></div>
  <div class="h"><b>١٠ ص – ١٢ م</b><span>10 AM – 12 AM</span></div>
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
 function go(n){{ show(n); clearInterval(timer); timer=setInterval(next,{DWELL_MS}); }}
 function next(){{ show(at+1); }}
 timer=setInterval(next,{DWELL_MS});

 // let someone step through it by hand while setting the screen up
 addEventListener('keydown',function(e){{
  if(e.key==='ArrowRight'||e.key==='ArrowDown'||e.key===' ') go(at+1);
  if(e.key==='ArrowLeft'||e.key==='ArrowUp') go(at-1);
 }});
 addEventListener('click',function(){{ go(at+1); }});
}})();
</script>
</body>
</html>'''


CSS = f'''
@font-face{{font-family:EM;src:url('../fonts/em-600.ttf') format('truetype');font-weight:600}}
@font-face{{font-family:EM;src:url('../fonts/em-700.ttf') format('truetype');font-weight:700}}
@font-face{{font-family:PP;src:url('../fonts/pp-500.ttf') format('truetype');font-weight:500}}
@font-face{{font-family:PP;src:url('../fonts/pp-700.ttf') format('truetype');font-weight:700}}

*{{box-sizing:border-box;margin:0;padding:0}}
html{{color-scheme:light;background:#fff}}
body{{background:#fff;color:{INK};font-family:EM,PP,sans-serif;overflow:hidden;
 width:100vw;height:100vh}}

/* fixed stage, scaled by script to fill whatever the TV reports */
#stage{{position:absolute;width:1920px;height:1080px;transform-origin:0 0;
 background:#fff;display:flex;flex-direction:column;padding:0 64px}}

header{{flex:none;height:132px;display:flex;align-items:center;gap:26px;
 border-bottom:3px solid {BLUE};direction:ltr}}
header img{{height:78px;width:auto}}
header .w{{margin-right:auto;line-height:1.1;text-align:left}}
header .w b{{display:block;font:700 40px EM;color:{BLUE}}}
header .w span{{display:block;font:500 17px PP;letter-spacing:.2em;color:{MUTED}}}
header .h{{text-align:right;line-height:1.1}}
header .h b{{display:block;font:700 32px EM;color:{INK}}}
header .h span{{display:block;font:500 16px PP;letter-spacing:.14em;color:{MUTED}}}

main{{flex:1;position:relative;min-height:0}}
.board{{position:absolute;inset:0;display:flex;flex-direction:column;
 justify-content:center;gap:18px;opacity:0;visibility:hidden;
 transition:opacity .5s ease}}
.board.on{{opacity:1;visibility:visible}}

.t{{display:flex;align-items:baseline;gap:18px;margin-bottom:6px}}
.t h2{{font:700 46px EM;color:{BLUE};white-space:nowrap}}
.t span{{direction:ltr;font:700 21px PP;letter-spacing:.26em;color:{MUTED};white-space:nowrap}}
.t i{{flex:1;height:2px;background:linear-gradient(to left,{BLUE},{RULE})}}

.board ul{{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;
 gap:22px 18px}}
.board li{{width:340px;display:flex;flex-direction:column;align-items:center;
 text-align:center}}
.sh{{width:100%;height:176px;display:flex;align-items:flex-end;justify-content:center}}
.sh img{{max-width:100%;max-height:100%;object-fit:contain;display:block}}
.a{{font:600 32px/1.2 EM;color:{INK};margin-top:10px}}
.e{{direction:ltr;font:500 21px/1.25 PP;color:{MUTED};margin-top:3px}}
.p{{direction:ltr;font:700 38px PP;color:{BLUE};margin-top:6px}}
.p span{{font:700 .55em PP;margin-left:4px;letter-spacing:.04em}}
.k{{direction:ltr;font:500 20px PP;color:#A9B5C4;margin-top:2px;min-height:24px}}

footer{{flex:none;height:76px;display:flex;align-items:center;
 justify-content:space-between;border-top:2px solid {RULE};direction:ltr}}
footer p{{font:600 20px EM;color:{MUTED};direction:rtl}}
.dots{{display:flex;gap:9px}}
.dots i{{width:11px;height:11px;border-radius:50%;background:{RULE};
 transition:background .3s,width .3s}}
.dots i.on{{background:{BLUE};width:30px;border-radius:6px}}
'''


def main():
    items = {x['id']: x for x in json.load(open('items-light.json'))['data']}
    os.makedirs(OUT, exist_ok=True)
    open(f'{OUT}/index.html', 'w', encoding='utf-8').write(build(items))

    bs = boards()
    total = sum(len(ids) for b in bs for _, _, ids in b)
    print(f'{len(bs)} boards, {total} items, '
          f'{len(bs) * DWELL_MS / 1000 / 60:.1f} min per full cycle\n')
    for n, b in enumerate(bs, 1):
        who = ' + '.join(f'{en}({len(ids)})' for _, en, ids in b)
        print(f'  board {n:>2}: {who}')
    print(f'\nwrote {OUT}/index.html '
          f'({os.path.getsize(f"{OUT}/index.html")//1024}KB)')


if __name__ == '__main__':
    main()
