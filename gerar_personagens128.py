"""Personagens e inimigos em 128x128 (heróis, NPCs e slimes), mesma paleta e contorno de 1px.

Saída (em rpg_assets_amostra/):
  herois_128.png -> 3 blocos de 640x640 (Lia, Davi, Nina); 5 colunas x 5 linhas de 128
                    linhas 0-3: andar (baixo, esquerda, direita, cima), colunas passo A / parado / passo B
                    linha 4: poses de batalha viradas para a esquerda: pronto, ataque, magia, ferido, caído
  npcs_128.png   -> 5 blocos de 384x512 (guarda, ancião, Lina, fazendeiro, mercadora); 3 colunas x 4 linhas
  slimes_128.png -> 4 colunas (normal, achatado, ataque, ferido) x 3 linhas (verde, azul, rubro)
"""
import os
from PIL import Image
from gerar_assets import Canvas, hsh, OUT

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
clamp = lambda v, a=0.0, b=1.0: max(a, min(b, v))


# ---------------------------------------------------------------- acabamento
import re
_FAM_ALIAS = {"wh": "s"}
DEEP = {"sk": "skd", "r": "rd", "t": "td", "g": "gd", "h": "hd", "d": "hd", "k": "ol", "p": "pd", "au": "aud",
        "s": "sd", "v": "vd", "m": "md", "o": "od", "w": "wd"}
RAMPS = {
    "sk": ["sk2", "sk", "sk0", "skd"], "r": ["r2", "r1", "r0", "rd"], "t": ["t2", "t1", "t0", "td"],
    "g": ["g3", "g2", "g1", "g0", "gd"], "h": ["h2", "h1", "h0", "hd"], "d": ["d3", "d2", "d1", "d0", "hd"],
    "k": ["k2", "k1", "k0", "ol"], "p": ["p1", "p0", "pd"], "au": ["au2", "au", "au0", "aud"],
    "s": ["wh", "s3", "s2", "s1", "s0", "sd"], "v": ["v2", "v1", "v0", "vd"], "m": ["m2", "m1", "m0", "md"],
    "o": ["o2", "o1", "o0", "od"], "w": ["w3", "w2", "w1", "w0", "wd"],
}


def fam(col):
    if col is None: return None
    f = re.match(r"[a-z]+", col).group(0)
    if f == "skd": return "sk"
    if f in ("rd", "td", "gd", "hd", "pd", "aud", "sd", "vd", "md", "od", "wd"): f = f[:-1]
    return _FAM_ALIAS.get(f, f)


def darker(col, steps=1):
    r = RAMPS.get(fam(col))
    if not r or col not in r: return col
    return r[min(len(r) - 1, r.index(col) + steps)]


def tone(cols, v, x, y):
    """Sombreado em faixas sólidas (cel shading), sem pontilhado; a faixa mais escura usa a sombra profunda do material."""
    if v >= 0.95:
        return DEEP.get(fam(cols[-1]), cols[-1])
    n = len(cols)
    return cols[min(n - 1, int(clamp(v) / 0.95 * n))]


PROTECT = {"ol", "wh"}


def finish(c):
    """Acabamento: limpa pixels soltos, sombra de contato, contorno colorido (sel-out) e suavização de cantos."""
    P = c.p
    # 1) pixels soltos dentro do mesmo material (exceto pele e detalhes)
    fix = {}
    for (x, y), col in P.items():
        if col in PROTECT or fam(col) == "sk": continue
        ns = [P.get((x + 1, y)), P.get((x - 1, y)), P.get((x, y + 1)), P.get((x, y - 1))]
        if None not in ns and len(set(ns)) == 1 and ns[0] != col and fam(ns[0]) == fam(col):
            fix[(x, y)] = ns[0]
    P.update(fix)
    # 2) sombra de contato: logo abaixo de outra peça o material escurece um tom
    shade = {}
    for (x, y), col in P.items():
        above = P.get((x, y - 1))
        if above is None or above in PROTECT or col in PROTECT: continue
        if fam(above) != fam(col) and fam(above) not in ("w",) and RAMPS.get(fam(col)):
            shade[(x, y)] = darker(col)
    P.update(shade)
    # 3) contorno colorido: lado iluminado (cima/esquerda) com a sombra profunda do material, lado da sombra em preto
    out = {}
    for (x, y), col in list(P.items()):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q in P or not (0 <= q[0] < c.w and 0 <= q[1] < c.h): continue
            out.setdefault(q, []).append(((-dx, -dy), col))
    for q, lst in out.items():
        dirs = {d for d, _ in lst}
        col = lst[0][1]
        lit = DEEP.get(fam(col), "ol")
        if col == lit or col == "ol": lit = "ol"
        if len(dirs) >= 2 and (0, 1) not in dirs and (-1, 0) not in dirs:
            P[q] = lit                       # canto em degrau do lado iluminado: tom intermediário
        elif dirs <= {(0, 1), (1, 0)}:
            P[q] = lit                       # forma está abaixo/à direita: borda de cima/esquerda, iluminada
        else:
            P[q] = "ol"


def ell(c, cx, cy, rx, ry, cols, bias=0.0, cut=None, cutmin=None, edge=True, xmin=None):
    pts = []
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        if (cut is not None and y > cut) or (cutmin is not None and y < cutmin): continue
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if xmin is not None and x < xmin: continue
            dx, dy = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            if dx * dx + dy * dy < 1: pts.append((x, y, dx, dy))
    S = {(x, y) for x, y, _, _ in pts}
    for x, y, dx, dy in pts:
        v = 0.45 + 0.5 * (dx * 0.6 + dy * 0.75) + bias
        if edge and ((x + 1, y) not in S or (x, y + 1) not in S): v = 1.0
        c.px(x, y, tone(cols, v, x, y))
    return S


def rect(c, x0, y0, x1, y1, cols, axis="x", bias=0.0, edge=True):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u = (x - x0) / max(1, x1 - x0) if axis == "x" else (y - y0) / max(1, y1 - y0)
            v = 0.15 + 0.7 * u + bias
            if edge and (x == x1 or y == y1): v = 1.0
            c.px(x, y, tone(cols, v, x, y))


def flat(c, x0, y0, x1, y1, col):
    c.rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), col)


def star(c, x, y, col, r=2):
    for i in range(-r, r + 1): c.px(x + i, y, col); c.px(x, y + i, col)
    c.px(x, y, "wh")


SKIN = ("sk2", "sk", "sk0")
PANTS = ("p1", "p1", "p0")
BOOTS = ("d1", "d0", "d0")

CHARS = [
    dict(tunic=("r2", "r1", "r0"), hair=("h2", "h1", "h0"), eye=("w2", "w0"), style="ponytail"),
    dict(tunic=("t2", "t1", "t0"), hair=("k2", "k1", "k0"), eye=("d1", "ol"), style="spiky"),
    dict(tunic=("g2", "g1", "g0"), hair=("au2", "au", "au0"), eye=("g2", "g0"), style="long"),
]
NPCS = [
    dict(tunic=("s2", "s1", "s0"), hair=("k2", "k1", "k0"), eye=("d1", "ol"), style="short", extra="helmet"),
    dict(tunic=("v2", "v1", "v0"), hair=("wh", "s3", "s2"), eye=("d1", "ol"), style="short", extra="beard", robe=True),
    dict(tunic=("m2", "m1", "m0"), hair=("o2", "o1", "o0"), eye=("g2", "g0"), style="pigtails", robe="dress"),
    dict(tunic=("d2", "d1", "d0"), hair=("h2", "h1", "h0"), eye=("d1", "ol"), style="short", extra="hat"),
    dict(tunic=("au2", "au", "au0"), hair=("k2", "k1", "k0"), eye=("d1", "ol"), style="bun", extra="apron"),
]


# ---------------------------------------------------------------- cabelo
def strands(c, hair, x0, x1, y0, y1, step=6, lean=0.0):
    col = hair[2]
    for sx in range(x0, x1 + 1, step):
        for y in range(y0, y1 + 1):
            x = int(sx + (y - y0) * lean * (sx - (x0 + x1) / 2) / max(1, (x1 - x0)))
            if c.p.get((x, y)) in hair[:2]: c.px(x, y, col)


def shine(c, hair, cx, cy, rx, ry):
    for y in range(int(cy - ry), int(cy + ry)):
        for x in range(int(cx - rx), int(cx + rx * 0.35)):
            dx, dy = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            r = (dx * dx + dy * dy) ** .5
            if 0.5 < r < 0.7 and dy < 0.05 and c.p.get((x, y)) in hair[1:] + (DEEP.get(fam(hair[-1])),):
                c.px(x, y, hair[0])


def bangs(c, hair, b, x0, x1, short, base=34, side=20):
    for x in range(x0, x1 + 1):
        tooth = 6 - abs((x % 8) - 4) * 1.5
        L = int(4 + tooth) if short[0] <= x <= short[1] else int(side + tooth / 2)
        u = (x - x0) / max(1, x1 - x0)
        for y in range(base + b, base + b + L + 1):
            v = 0.2 + 0.6 * u + (0.3 if y >= base + b + L - 1 else 0)
            c.px(x, y, tone(hair, v, x, y))


# ---------------------------------------------------------------- rosto
def eye(c, ex, ey, cols, w=7, hurt=False, closed=False, side_flick=-1):
    if closed:
        flat(c, ex, ey + 5, ex + w - 1, ey + 5, "ol"); flat(c, ex + 1, ey + 6, ex + w - 2, ey + 6, "sk0"); return
    if hurt:
        for i in range(4): c.px(ex + w - 2 - i, ey + 2 + i, "ol"); c.px(ex + w - 2 - i, ey + 8 - i, "ol")
        return
    flat(c, ex - 1, ey, ex + w, ey + 1, "ol"); c.px(ex - 1 if side_flick < 0 else ex + w, ey + 2, "ol")
    for y in range(ey + 2, ey + 9):
        for x in range(ex, ex + w):
            c.px(x, y, cols[1] if y < ey + 5 else cols[0])
    flat(c, ex + 2, ey + 3, ex + w - 3, ey + 7, "ol")
    flat(c, ex + 1, ey + 2, ex + 2, ey + 3, "wh"); c.px(ex + w - 2, ey + 7, "wh")
    flat(c, ex + 1, ey + 9, ex + w - 2, ey + 9, "sk0")


def blush(c, x, y, w=5):
    for i in range(w):
        for j in range(2):
            if (i + j) % 2 == 0: c.px(x + i, y + j, "r2")


# ---------------------------------------------------------------- frente / costas
def legs_front(c, cfg, step):
    for i, lx in enumerate((50, 67)):
        lifted = (step == 1 and i == 0) or (step == 2 and i == 1)
        bot = 106 - (4 if lifted else 0)
        if cfg.get("robe") is True:
            rect(c, lx, bot - 4, lx + 10, bot, PANTS)
        else:
            rect(c, lx, 92, lx + 10, bot, PANTS); flat(c, lx + 3, 99, lx + 6, 99, "p0")
        rect(c, lx - 1, bot + 1, lx + 10, bot + 9, BOOTS, axis="y")
        flat(c, lx, bot + 1, lx + 6, bot + 1, "d2"); c.px(lx + 4, bot + 4, "d2"); c.px(lx + 6, bot + 4, "d2")


def torso_front(c, cfg, b, back):
    t = cfg["tunic"]; robe = cfg.get("robe")
    bottom = 106 if robe is True else 100 if robe == "dress" else 91
    rect(c, 46, 62 + b, 81, bottom + b, t)
    if robe:
        for x in range(40, 88):
            fl = int(abs(x - 64) * 0.0)
        rect(c, 42, 86 + b, 85, bottom + 2 + b, t)
        for fx in (52, 64, 76): flat(c, fx, 90 + b, fx, bottom + 2 + b, t[2])
    else:
        rect(c, 44, 88 + b, 83, 95 + b, t)
        for (x0, x1) in ((52, 50), (64, 64), (76, 78)):
            for y in range(89, 96): c.px(int(x0 + (x1 - x0) * (y - 89) / 6), y + b, t[2])
    flat(c, 47, 63 + b, 49, 80 + b, t[0])
    if cfg.get("extra") == "apron" and not back:
        rect(c, 52, 72 + b, 75, 98 + b, ("wh", "s3", "s2")); flat(c, 52, 72 + b, 75, 73 + b, "s2")
    if back:
        flat(c, 63, 66 + b, 64, 82 + b, t[2])
    else:
        for i in range(9):
            w = 6 - int(i * 0.7)
            flat(c, 64 - w, 62 + b + i, 63 + w, 62 + b + i, "sk" if i < 7 else "sk0")
            c.px(64 - w - 1, 62 + b + i, t[0]); c.px(64 + w, 62 + b + i, t[0])
    if not robe or robe == "dress":
        y = (84 if not robe else 80) + b
        flat(c, 46, y, 81, y + 3, "d0")
        for x in range(47, 81, 3): c.px(x, y + 1, "d1")
        if not back:
            rect(c, 60, y - 1, 67, y + 4, ("au2", "au", "au0")); flat(c, 62, y + 1, 65, y + 2, "au0"); c.px(61, y, "wh")


def arms_front(c, cfg, b, step):
    t = cfg["tunic"]
    sw = {0: (0, 0), 1: (-4, 4), 2: (4, -4)}[step]
    for ax, dy, bias in ((38, sw[0], -0.15), (82, sw[1], 0.2)):
        rect(c, ax, 64 + b + dy, ax + 7, 77 + b + dy, t, bias=bias)
        flat(c, ax, 76 + b + dy, ax + 7, 77 + b + dy, t[0])
        rect(c, ax + 1, 78 + b + dy, ax + 6, 85 + b + dy, SKIN, bias=bias)
        ell(c, ax + 3.5, 88 + b + dy, 4.2, 3.6, SKIN, bias=bias)
        c.px(ax + 3, 89 + b + dy, "sk0")


def head_front(c, cfg, b, back):
    hair = cfg["hair"]; st = cfg["style"]; ex = cfg.get("extra")
    if st == "long" or st == "pigtails":
        if st == "long" and not back:
            for x0 in (36, 82):
                rect(c, x0, 40 + b, x0 + 9, 80 + b, hair); strands(c, hair, x0 + 1, x0 + 8, 44 + b, 80 + b, step=3)
        else:
            for px_ in (34, 94):
                ell(c, px_, 60 + b, 7, 14, hair); strands(c, hair, px_ - 5, px_ + 5, 48 + b, 74 + b, step=4)
                ell(c, px_, 44 + b, 4, 4, ("r2", "r1", "r0"))
    rect(c, 58, 56 + b, 69, 63 + b, ("sk", "sk0", "sk0"))
    ell(c, 64, 40 + b, 22, 21, SKIN, bias=-0.22)
    if back:
        if st == "long": rect(c, 36, 40 + b, 91, 82 + b, hair); strands(c, hair, 38, 90, 44 + b, 82 + b, step=5)
        ell(c, 64, 36 + b, 25, 23, hair, bias=-0.1); strands(c, hair, 42, 88, 18 + b, 58 + b, step=5, lean=0.4)
        shine(c, hair, 64, 34 + b, 25, 23)
        rect(c, 50, 54 + b, 78, 59 + b, hair, axis="y")
        if st == "ponytail":
            rect(c, 58, 48 + b, 69, 80 + b, hair); strands(c, hair, 60, 68, 50 + b, 80 + b, step=3)
            ell(c, 63.5, 83 + b, 5, 4, hair)
            ell(c, 58, 45 + b, 5, 4, ("r2", "r1", "r0")); ell(c, 70, 45 + b, 5, 4, ("r2", "r1", "r0")); flat(c, 62, 43 + b, 65, 47 + b, "r0")
        if st == "bun": ell(c, 64, 14 + b, 9, 8, hair); shine(c, hair, 64, 14 + b, 9, 8)
    else:
        eye(c, 51, 41 + b, cfg["eye"], side_flick=-1); eye(c, 70, 41 + b, cfg["eye"], side_flick=1)
        c.px(64, 52 + b, "sk0"); c.px(63, 53 + b, "sk0")
        flat(c, 61, 57 + b, 66, 57 + b, "sk0"); flat(c, 62, 58 + b, 65, 58 + b, "r0"); c.px(60, 56 + b, "sk0"); c.px(67, 56 + b, "sk0")
        blush(c, 47, 54 + b); blush(c, 76, 54 + b)
        if ex == "beard":
            ell(c, 64, 62 + b, 16, 14, ("wh", "s3", "s2"), cutmin=52 + b); strands(c, ("wh", "s3", "s2"), 52, 76, 56 + b, 75 + b, step=4)
            flat(c, 58, 55 + b, 69, 56 + b, "s3"); flat(c, 61, 58 + b, 66, 58 + b, "s2")
        ell(c, 64, 32 + b, 25, 18, hair, bias=-0.1, cut=37 + b); strands(c, hair, 42, 86, 15 + b, 36 + b, step=6, lean=0.5)
        shine(c, hair, 64, 32 + b, 25, 18)
        bangs(c, hair, b, 41, 87, short=(49, 79), side=20 if st not in ("long",) else 24)
        if st == "long":
            ell(c, 44, 26 + b, 3, 3, ("wh", "r2", "r1")); c.px(44, 26 + b, "au")
        if st == "bun": ell(c, 64, 12 + b, 9, 8, hair); shine(c, hair, 64, 12 + b, 9, 8)
    if st == "ponytail" and not back:
        ell(c, 80, 16 + b, 5, 4, ("r2", "r1", "r0")); ell(c, 90, 16 + b, 5, 4, ("r2", "r1", "r0")); flat(c, 84, 14 + b, 86, 18 + b, "r0")
    if st == "spiky":
        for i, cx in enumerate((48, 60, 72, 83)):
            for dy in range(11):
                w = max(0, 5 - dy // 2)
                for x in range(cx - w, cx + w + 1):
                    c.px(x, 18 - dy + b, tone(hair, 0.2 + 0.6 * (x - cx + w) / max(1, 2 * w), x, 18 - dy + b))
    if ex == "helmet":
        ell(c, 64, 30 + b, 27, 18, ("s3", "s2", "s1"), cut=34 + b); flat(c, 38, 32 + b, 90, 35 + b, "au0"); flat(c, 38, 32 + b, 90, 32 + b, "au")
        ell(c, 56, 20 + b, 6, 3, ("wh", "s3", "s3"), edge=False)
    if ex == "hat":
        ell(c, 64, 33 + b, 36, 7, ("au2", "au", "au0")); ell(c, 64, 22 + b, 20, 13, ("au2", "au", "au0"), cut=31 + b)
        flat(c, 45, 27 + b, 83, 30 + b, "r1"); flat(c, 45, 30 + b, 83, 30 + b, "r0")
        for x in range(30, 98, 4): c.px(x, 33 + b, "au0")


def front(cfg, step, back=False):
    c = Canvas(128, 128); b = -2 if step else 0
    if cfg["style"] == "long" and not back:
        rect(c, 38, 40 + b, 89, 84 + b, cfg["hair"], bias=0.25)
    legs_front(c, cfg, step)
    torso_front(c, cfg, b, back)
    arms_front(c, cfg, b, step)
    head_front(c, cfg, b, back)
    finish(c); c.shadow_ellipse(64, 118, 25, 5)
    return c


# ---------------------------------------------------------------- lateral (direita)
def legs_side(c, cfg, step):
    robe = cfg.get("robe") is True
    if step == 0:
        if not robe: rect(c, 58, 92, 69, 107, PANTS)
        rect(c, 56, 108, 75, 116, BOOTS, axis="y"); flat(c, 58, 108, 70, 108, "d2")
        return
    fc, bc = (PANTS, ("p0", "p0", "p0")) if step == 1 else (("p0", "p0", "p0"), PANTS)
    if not robe:
        rect(c, 48, 92, 57, 105, bc); rect(c, 68, 92, 77, 105, fc)
    rect(c, 42, 106, 57, 114, BOOTS, axis="y"); rect(c, 70, 106, 85, 114, BOOTS, axis="y")
    flat(c, 72, 106, 82, 106, "d2")


def torso_side(c, cfg, b, lean=0):
    t = cfg["tunic"]; robe = cfg.get("robe")
    bottom = 106 if robe is True else 100 if robe == "dress" else 91
    rect(c, 52 + lean, 62 + b, 77 + lean, bottom + b, t, bias=-0.1)
    flat(c, 52 + lean, 62 + b, 55 + lean, bottom + b, t[2])
    rect(c, 50 + lean, 88 + b, 79 + lean, (bottom + 4 if robe else 95) + b, t)
    if cfg.get("extra") == "apron": rect(c, 66 + lean, 72 + b, 78 + lean, 98 + b, ("wh", "s3", "s2"))
    if not robe or robe == "dress":
        y = (84 if not robe else 80) + b
        flat(c, 52 + lean, y, 77 + lean, y + 3, "d0")
        for x in range(53 + lean, 77 + lean, 3): c.px(x, y + 1, "d1")
        rect(c, 72 + lean, y - 1, 76 + lean, y + 4, ("au2", "au", "au0"))
    flat(c, 70 + lean, 62 + b, 75 + lean, 64 + b, "sk")


def head_side(c, cfg, b, hx=0, eyes="open"):
    hair = cfg["hair"]; st = cfg["style"]; ex = cfg.get("extra")
    if st == "ponytail":
        for (px_, py) in [(42, 40), (38, 50), (36, 60), (38, 70)]:
            ell(c, px_ + hx, py + b, 7, 7, hair)
        strands(c, hair, 32 + hx, 46 + hx, 34 + b, 77 + b, step=3)
        ell(c, 46 + hx, 34 + b, 4, 4, ("r2", "r1", "r0"))
    if st == "long":
        rect(c, 40 + hx, 36 + b, 61 + hx, 82 + b, hair); strands(c, hair, 41 + hx, 60 + hx, 40 + b, 82 + b, step=4)
    if st == "pigtails":
        ell(c, 44 + hx, 60 + b, 7, 14, hair); strands(c, hair, 39 + hx, 49 + hx, 48 + b, 74 + b, step=4); ell(c, 46 + hx, 44 + b, 4, 4, ("r2", "r1", "r0"))
    rect(c, 62 + hx, 56 + b, 71 + hx, 63 + b, ("sk", "sk0", "sk0"))
    ell(c, 66 + hx, 40 + b, 21, 21, SKIN, bias=-0.22)
    ell(c, 86 + hx, 47 + b, 3, 3, SKIN)
    if ex == "beard":
        ell(c, 72 + hx, 60 + b, 14, 12, ("wh", "s3", "s2"), cutmin=52 + b); strands(c, ("wh", "s3", "s2"), 62 + hx, 84 + hx, 55 + b, 72 + b, step=4)
    if eyes == "open": eye(c, 76 + hx, 41 + b, cfg["eye"], w=5, side_flick=1)
    elif eyes == "hurt": eye(c, 76 + hx, 41 + b, cfg["eye"], w=5, hurt=True)
    else: eye(c, 76 + hx, 41 + b, cfg["eye"], w=5, closed=True)
    if ex != "beard": flat(c, 79 + hx, 57 + b, 82 + hx, 57 + b, "sk0")
    blush(c, 77 + hx, 54 + b, 4)
    ell(c, 62 + hx, 32 + b, 25, 18, hair, bias=-0.1, cut=37 + b); strands(c, hair, 40 + hx, 84 + hx, 15 + b, 36 + b, step=6, lean=0.5)
    ell(c, 52 + hx, 44 + b, 13, 15, hair); strands(c, hair, 42 + hx, 62 + hx, 34 + b, 58 + b, step=4)
    shine(c, hair, 62 + hx, 32 + b, 25, 18)
    ell(c, 61 + hx, 46 + b, 3.2, 4.6, SKIN); c.px(61 + hx, 46 + b, "sk0")
    bangs(c, hair, b, 66 + hx, 86 + hx, short=(66 + hx, 86 + hx))
    if st == "spiky":
        for i, (cx, top) in enumerate([(44, 20), (54, 12), (66, 10), (78, 14)]):
            for dy in range(11):
                w = max(0, 5 - dy // 2)
                for x in range(cx - w, cx + w + 1):
                    c.px(x + hx, top + 10 - dy + b, tone(hair, 0.2 + 0.6 * (x - cx + w) / max(1, 2 * w), x, top + 10 - dy))
    if st == "long": ell(c, 70 + hx, 22 + b, 3, 3, ("wh", "r2", "r1"))
    if st == "bun": ell(c, 54 + hx, 16 + b, 9, 8, hair); shine(c, hair, 54 + hx, 16 + b, 9, 8)
    if ex == "helmet":
        ell(c, 64 + hx, 30 + b, 27, 18, ("s3", "s2", "s1"), cut=34 + b); flat(c, 38 + hx, 32 + b, 90 + hx, 35 + b, "au0")
    if ex == "hat":
        ell(c, 66 + hx, 33 + b, 34, 7, ("au2", "au", "au0")); ell(c, 64 + hx, 22 + b, 19, 13, ("au2", "au", "au0"), cut=31 + b)
        flat(c, 46 + hx, 27 + b, 82 + hx, 30 + b, "r1")


def arm_side(c, cfg, b, x, bias=0.1):
    t = cfg["tunic"]
    rect(c, x, 64 + b, x + 7, 77 + b, t, bias=bias); flat(c, x, 76 + b, x + 7, 77 + b, t[0])
    rect(c, x + 1, 78 + b, x + 6, 85 + b, SKIN); ell(c, x + 3.5, 88 + b, 4.2, 3.6, SKIN)


def side(cfg, step):
    c = Canvas(128, 128); b = -2 if step else 0
    legs_side(c, cfg, step)
    torso_side(c, cfg, b)
    head_side(c, cfg, b)
    arm_side(c, cfg, b, {0: 62, 1: 56, 2: 68}[step])
    finish(c); c.shadow_ellipse(64, 118, 25, 5)
    return c


# ---------------------------------------------------------------- poses de batalha (direita; espelhadas depois)
def pose_attack(cfg):
    c = Canvas(128, 128); t = cfg["tunic"]
    legs_side(c, cfg, 1)
    rect(c, 44, 68, 51, 79, t, bias=0.3); rect(c, 45, 80, 50, 85, SKIN)
    torso_side(c, cfg, 0, lean=2)
    head_side(c, cfg, 0, hx=4)
    rect(c, 74, 66, 89, 73, t, axis="y"); rect(c, 90, 66, 95, 73, SKIN, axis="y")
    rect(c, 96, 60, 99, 79, ("au2", "au", "au0")); flat(c, 94, 60, 101, 61, "au")
    for i in range(27):
        x, y = 100 + i, 66 - i
        c.px(x, y - 1, "wh"); c.px(x, y, "s3"); c.px(x, y + 1, "s3"); c.px(x, y + 2, "s2"); c.px(x + 1, y + 2, "s1")
    star(c, 124, 40, "w3", 3)
    finish(c); c.shadow_ellipse(64, 118, 27, 5)
    return c


def pose_cast(cfg):
    c = Canvas(128, 128); t = cfg["tunic"]
    legs_side(c, cfg, 0)
    rect(c, 54, 44, 61, 63, t, bias=0.3); ell(c, 57.5, 38, 4.5, 6, SKIN)
    torso_side(c, cfg, 0)
    head_side(c, cfg, 0, eyes="closed")
    rect(c, 74, 62, 85, 69, t); rect(c, 88, 48, 95, 63, t); ell(c, 92, 42, 5, 6, SKIN)
    for x, y, col, r in [(98, 26, "wh", 3), (90, 22, "w3", 2), (106, 34, "w3", 2), (108, 20, "au", 2), (56, 22, "au", 2), (96, 12, "w3", 3), (114, 30, "wh", 1)]:
        star(c, x, y, col, r)
    finish(c); c.shadow_ellipse(64, 118, 25, 5)
    return c


def pose_hurt(cfg):
    c = Canvas(128, 128); t = cfg["tunic"]
    legs_side(c, cfg, 0)
    rect(c, 42, 60, 49, 72, t, bias=0.3); ell(c, 42, 56, 4.5, 4.5, SKIN)
    torso_side(c, cfg, 2, lean=-4)
    head_side(c, cfg, 2, hx=-8, eyes="hurt")
    rect(c, 70, 66, 77, 76, t); rect(c, 76, 74, 83, 80, SKIN)
    for x, y in [(92, 24), (96, 32), (90, 36)]: star(c, x, y, "wh", 2)
    finish(c); c.shadow_ellipse(64, 118, 25, 5)
    return c


def pose_ko(cfg):
    c = Canvas(128, 128); t = cfg["tunic"]; hair = cfg["hair"]
    rect(c, 14, 98, 25, 114, BOOTS); rect(c, 26, 98, 53, 112, PANTS, axis="y")
    rect(c, 52, 92, 85, 114, t, axis="y"); flat(c, 60, 92, 63, 114, "d0"); rect(c, 59, 100, 64, 105, ("au2", "au", "au0"))
    rect(c, 60, 114, 82, 118, SKIN, axis="y")
    if cfg["style"] in ("long", "pigtails"): rect(c, 92, 84, 120, 116, hair, axis="y")
    ell(c, 100, 102, 17, 17, SKIN)
    ell(c, 108, 100, 16, 17, hair, xmin=98); strands(c, hair, 100, 122, 86, 116, step=4)
    for y in (96, 106): flat(c, 92, y, 96, y, "ol")
    c.px(88, 102, "sk0")
    if cfg.get("extra") == "hat": ell(c, 118, 96, 7, 20, ("au2", "au", "au0"))
    finish(c); c.shadow_ellipse(66, 119, 48, 5)
    return c


def walk_sheet(cfg):
    sheet = Image.new("RGBA", (3 * 128, 4 * 128))
    for col, step in enumerate([1, 0, 2]):
        r = side(cfg, step)
        for row, spr in enumerate([front(cfg, step), r.mirrored(), r, front(cfg, step, back=True)]):
            sheet.alpha_composite(spr.img(), (col * 128, row * 128))
    return sheet


def hero_sheet(cfg):
    sheet = Image.new("RGBA", (5 * 128, 5 * 128))
    sheet.alpha_composite(walk_sheet(cfg), (0, 0))
    for col, spr in enumerate([side(cfg, 0), pose_attack(cfg), pose_cast(cfg), pose_hurt(cfg), pose_ko(cfg)]):
        sheet.alpha_composite(spr.mirrored().img(), (col * 128, 4 * 128))
    return sheet


# ---------------------------------------------------------------- slimes 128
SLIME_PAL = {"verde": ("g3", "g2", "g1", "g0"), "azul": ("w3", "w2", "w1", "w0"), "rubro": ("r2", "r2", "r1", "r0")}


def slime128(kind, frame):
    c = Canvas(128, 128); pal = SLIME_PAL[kind]
    rx, h, lean = {0: (44, 54, 0), 1: (50, 44, 0), 2: (38, 66, 12), 3: (52, 38, -6)}[frame]
    base = 116
    if kind == "azul": h += 4
    top = base - h
    body = set()
    for y in range(top - 2, base):
        t = (base - y) / h
        if t > 1: continue
        w = (1 - t * t) ** 0.5
        if kind == "azul": w *= (1 - 0.4 * max(0, t - 0.45))
        cx = 64 + lean * t
        for x in range(128):
            dx = (x + .5 - cx) / (rx * max(w, 0.001))
            if abs(dx) < 1:
                body.add((x, y))
                v = 0.45 + 0.45 * dx - (t - 0.45) * 0.7
                if y >= base - 6: v = max(v, 0.85)
                rim = abs(dx) > 0.88 and dx > 0
                c.px(x, y, pal[3] if rim else tone(pal, v, x, y))
    # núcleo translúcido e bolhas
    for (bx, by, r) in [(-14, 22, 4), (10, 14, 3), (-2, 10, 2), (18, 26, 2)]:
        x0, y0 = int(64 + lean * 0.2 + bx), base - by
        for y in range(y0 - r, y0 + r + 1):
            for x in range(x0 - r, x0 + r + 1):
                if (x - x0) ** 2 + (y - y0) ** 2 <= r * r and (x, y) in body: c.px(x, y, pal[1])
        c.px(x0 - r // 2, y0 - r // 2, pal[0])
    if kind == "rubro":
        for sx in (-18, 0, 18):
            px0 = int(64 + lean + sx); hh = 12 if sx == 0 else 8
            for dy in range(hh):
                ww = max(0, (hh - dy) // 2)
                for x in range(px0 - ww, px0 + ww + 1):
                    c.px(x, top + 2 - dy, tone(pal, 0.3 + 0.5 * (x - px0 + ww) / max(1, 2 * ww), x, top + 2 - dy))
    if kind == "azul":
        ell(c, 64 + lean * .9, top - 5, 3, 4.5, pal[:3])
    # brilho especular
    gx, gy = int(64 + lean * .6 - rx * .45), int(top + h * .26)
    for y in range(gy - 5, gy + 6):
        for x in range(gx - 7, gx + 8):
            if ((x - gx) / 7) ** 2 + ((y - gy) / 4.5) ** 2 < 1 and (x, y) in body:
                c.px(x, y, pal[0] if ((x - gx) / 7) ** 2 + ((y - gy) / 4.5) ** 2 < 0.45 else pal[1])
    star(c, gx + 9, gy - 3, "wh", 1)
    # olhos e boca (olham para a direita)
    ey = int(base - h * 0.52); ex = int(64 + lean * .5)
    for e in (ex + 2, ex + 22):
        if frame == 3:
            for i in range(7): c.px(e + i, ey + i, "ol"); c.px(e + 6 - i, ey + i, "ol")
        else:
            for y in range(ey, ey + 11):
                for x in range(e, e + 7):
                    if ((x + .5 - e - 3.5) / 3.6) ** 2 + ((y + .5 - ey - 5.5) / 5.6) ** 2 < 1: c.px(x, y, "ol")
            flat(c, e + 1, ey + 2, e + 3, ey + 4, "wh"); c.px(e + 4, ey + 8, "wh")
            if frame == 2:
                for i in range(6): c.px(e - 2 + i, ey - 5 + (i // 2 if e == ex + 2 else (5 - i) // 2), "ol")
    my = ey + 16
    if frame == 2:
        for y in range(my, my + 8):
            for x in range(ex + 10, ex + 20):
                if ((x + .5 - ex - 15) / 5) ** 2 + ((y + .5 - my - 4) / 4) ** 2 < 1: c.px(x, y, "ol")
        flat(c, ex + 12, my + 5, ex + 17, my + 6, "r1")
    elif frame == 3:
        for i in range(8): c.px(ex + 11 + i, my + 2 + (i % 2), "ol")
    else:
        flat(c, ex + 12, my + 1, ex + 17, my + 1, "ol"); c.px(ex + 11, my, "ol"); c.px(ex + 18, my, "ol")
        blush(c, ex - 4, my - 3, 4); blush(c, ex + 28, my - 3, 4)
    finish(c); c.shadow_ellipse(64 + lean // 2, 120, rx + 6, 5)
    return c


def main():
    hs = Image.new("RGBA", (3 * 640, 640))
    for i, cfg in enumerate(CHARS): hs.alpha_composite(hero_sheet(cfg), (i * 640, 0))
    hs.save(os.path.join(OUT, "herois_128.png"))
    ns = Image.new("RGBA", (5 * 384, 512))
    for i, cfg in enumerate(NPCS): ns.alpha_composite(walk_sheet(cfg), (i * 384, 0))
    ns.save(os.path.join(OUT, "npcs_128.png"))
    sl = Image.new("RGBA", (4 * 128, 3 * 128))
    for row, k in enumerate(["verde", "azul", "rubro"]):
        for f in range(4): sl.alpha_composite(slime128(k, f).img(), (f * 128, row * 128))
    sl.save(os.path.join(OUT, "slimes_128.png"))
    print("ok -> herois_128.png, npcs_128.png, slimes_128.png")


if __name__ == "__main__":
    main()
