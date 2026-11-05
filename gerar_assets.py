"""Gerador de assets padronizados para RPG 2D top-down (32x32, paleta fixa).

Uso:  python3 gerar_assets.py
Saída: pasta rpg_assets_amostra/ ao lado deste script.
Para mudar o estilo, edite PALETA ou T (tamanho do tile) e rode de novo.
"""
from PIL import Image, ImageDraw
import math, json, os

T = 32
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rpg_assets_amostra")

# ---------------------------------------------------------------- paleta
PALETA = {
    "ol":  (34, 28, 40),     # contorno
    "g0": (44, 92, 56),  "g1": (72, 134, 62),  "g2": (108, 172, 72),  "g3": (160, 206, 98),
    "d0": (102, 66, 46), "d1": (146, 100, 62), "d2": (184, 138, 88),  "d3": (216, 182, 124),
    "w0": (34, 60, 118), "w1": (46, 94, 166),  "w2": (72, 140, 210),  "w3": (186, 228, 244),
    "s0": (70, 74, 92),  "s1": (110, 116, 132), "s2": (156, 162, 174), "s3": (206, 210, 214),
    "sk": (242, 198, 156), "sk0": (204, 150, 114), "sk2": (252, 222, 188),
    "t0": (32, 88, 96), "t1": (52, 132, 134), "t2": (96, 178, 170),
    "k0": (40, 34, 50), "k1": (62, 52, 72), "k2": (96, 84, 108), "au2": (250, 220, 132),
    "v0": (88, 58, 112), "v1": (132, 90, 156), "v2": (176, 132, 196),
    "m0": (176, 80, 120), "m1": (226, 132, 164), "m2": (244, 186, 206),
    "o0": (150, 60, 32), "o1": (200, 96, 48), "o2": (232, 140, 80),
    "h0": (92, 50, 34),  "h1": (134, 76, 44),  "h2": (176, 108, 60),
    "r0": (140, 40, 52), "r1": (196, 66, 68), "r2": (234, 118, 98),
    "p0": (48, 56, 98),  "p1": (78, 90, 146),
    "au": (236, 188, 70), "au0": (176, 122, 42),
    "wh": (244, 240, 230),
}
SOMBRA = (20, 30, 24, 80)  # sombra translúcida (única cor fora da paleta)


def hsh(x, y, s=0):
    n = (x * 374761393 + y * 668265263 + s * 982451653) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def grid_to_img(g):
    img = Image.new("RGBA", (len(g[0]), len(g)))
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            if c:
                img.putpixel((x, y), PALETA[c] + (255,))
    return img


# ---------------------------------------------------------------- texturas base
def grass_grid(v=0):
    g = [[None] * T for _ in range(T)]
    for y in range(T):
        for x in range(T):
            r = hsh(x, y, 11 + v)
            g[y][x] = "g0" if r < 0.06 else "g2" if r < 0.14 else "g3" if r < 0.155 else "g1"
    tufos = [[(6, 9), (21, 6), (14, 23), (26, 19)], [(9, 15), (24, 26)], [(4, 4), (18, 13), (27, 27)]][v]
    for tx, ty in tufos:
        for dx, dy, c in [(0, 0, "g2"), (2, 0, "g2"), (1, -1, "g3"), (0, 1, "g0"), (1, 1, "g0"), (2, 1, "g0")]:
            g[(ty + dy) % T][(tx + dx) % T] = c
    return g


def dirt_grid():
    g = [[None] * T for _ in range(T)]
    for y in range(T):
        for x in range(T):
            r = hsh(x, y, 23)
            g[y][x] = "d0" if r < 0.07 else "d2" if r < 0.16 else "d1"
    for px, py in [(5, 7), (19, 4), (11, 20), (26, 15), (22, 27)]:
        g[py][px] = "d3"
        g[(py + 1) % T][px] = "d0"
    return g


def water_grid(f=0):
    g = [[None] * T for _ in range(T)]
    for y in range(T):
        for x in range(T):
            yy, ph = y % 8, y // 8
            s = math.sin(2 * math.pi * x / 16 + ph * 1.7 + f * math.pi)
            c = "w1"
            if yy == 2 and s > 0.5: c = "w2"
            if yy == 3 and s > 0.8: c = "w3"
            if yy == 6 and s < -0.6: c = "w0"
            g[y][x] = c
    return g


def stone_grid():
    g = [[None] * T for _ in range(T)]
    for y in range(T):
        for x in range(T):
            by, yy = y // 8, y % 8
            xo = (x + (by % 2) * 4) % T
            bx, xx = xo // 8, xo % 8
            claro = hsh(bx, by, 5) < 0.3
            if yy == 7 or xx == 7:
                c = "s0"
            elif yy == 0 or xx == 0:
                c = "s3" if claro else "s2"
            else:
                c = "s2" if claro else "s1"
                if hsh(x, y, 9) < 0.05: c = "s0"
            g[y][x] = c
    return g


# ---------------------------------------------------------------- transições (Wang por cantos)
# máscara: TL=1, TR=2, BL=4, BR=8  (bit ligado = terreno "de cima": terra/água)
def smooth(t): return t * t * (3 - 2 * t)


def corner_val(mask, x, y):
    uu = min(max((x + 0.5) / T, 0), 1); vv = min(max((y + 0.5) / T, 0), 1)
    u, v = smooth(uu), smooth(vv)
    tl, tr, bl, br = mask & 1, (mask >> 1) & 1, (mask >> 2) & 1, (mask >> 3) & 1
    val = tl * (1 - u) * (1 - v) + tr * u * (1 - v) + bl * (1 - u) * v + br * u * v
    return val + (hsh(x // 2, y // 2, 77) - 0.5) * 0.35 * math.sin(math.pi * uu) * math.sin(math.pi * vv)


def transition(mask, base, over, kind):
    ins = {(x, y): corner_val(mask, x, y) > 0.5 for x in range(-2, T + 2) for y in range(-2, T + 2)}
    g = [[None] * T for _ in range(T)]
    n1 = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    n2 = [(2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, 1), (1, -1), (-1, -1)]
    for y in range(T):
        for x in range(T):
            near1 = lambda want: any(ins[(x + dx, y + dy)] == want for dx, dy in n1)
            near2 = lambda want: any(ins[(x + dx, y + dy)] == want for dx, dy in n2)
            if ins[(x, y)]:
                c = over[y][x]
                if kind == "terra":
                    if near1(False): c = "d0"
                else:
                    if near1(False): c = "w3"
                    elif near2(False): c = "w2"
            else:
                c = base[y][x]
                if kind == "terra":
                    if near1(True): c = "g2"
                else:
                    if near1(True): c = "d2"
                    elif near2(True): c = "d3"
            g[y][x] = c
    return g


# ---------------------------------------------------------------- canvas p/ sprites
class Canvas:
    def __init__(s, w, h): s.w, s.h, s.p, s.sh = w, h, {}, set()
    def px(s, x, y, c):
        if 0 <= x < s.w and 0 <= y < s.h: s.p[(x, y)] = c
    def rect(s, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): s.px(x, y, c)
    def outline(s):
        add = [(x + dx, y + dy) for (x, y) in s.p for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]
               if (x + dx, y + dy) not in s.p and 0 <= x + dx < s.w and 0 <= y + dy < s.h]
        for q in add: s.p[q] = "ol"
    def shadow_ellipse(s, cx, cy, rx, ry):
        for y in range(s.h):
            for x in range(s.w):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 < 1 and (x, y) not in s.p:
                    s.sh.add((x, y))
    def mirrored(s):
        m = Canvas(s.w, s.h)
        m.p = {(s.w - 1 - x, y): c for (x, y), c in s.p.items()}
        m.sh = {(s.w - 1 - x, y) for (x, y) in s.sh}
        return m
    def img(s):
        im = Image.new("RGBA", (s.w, s.h), (0, 0, 0, 0))
        for q in s.sh: im.putpixel(q, SOMBRA)
        for q, c in s.p.items(): im.putpixel(q, PALETA[c] + (255,))
        return im


def shaded_blob(c, circles, pal, light_bias=0.0, seed=1):
    """Preenche união de círculos com sombreamento (luz vinda de cima-esquerda)."""
    for y in range(c.h):
        for x in range(c.w):
            best = None
            for (cx, cy, r) in circles:
                d = math.hypot(x + .5 - cx, y + .5 - cy) / r
                if d < 1 and (best is None or d < best[0]): best = (d, cx, cy, r)
            if best:
                d, cx, cy, r = best
                l = -((x + .5 - cx) + (y + .5 - cy)) / (r * 1.4) + light_bias + (hsh(x, y, seed) - .5) * .25
                c.px(x, y, pal[3] if l > .45 else pal[2] if l > .1 else pal[1] if l > -.4 else pal[0])


# ---------------------------------------------------------------- personagem
def legs_front(c, step):
    for lx, lifted in [(12, step == 1), (17, step == 2)]:
        top, bottom = 24, 27 - (1 if lifted else 0)
        c.rect(lx, top, lx + 2, bottom, "p1"); c.px(lx + 2, top, "p0")
        c.rect(lx, bottom + 1, lx + 2, bottom + 2, "d0")


def char_front(step, back=False):
    c = Canvas(32, 32); b = -1 if step else 0
    legs_front(c, step)
    c.rect(11, 16 + b, 20, 23 + b, "r1"); c.rect(19, 16 + b, 20, 23 + b, "r0")
    c.rect(11, 22 + b, 20, 22 + b, "d0")
    if not back: c.rect(15, 22 + b, 16, 22 + b, "au")
    for ax, ay in [(9, {1: -1, 2: 1}.get(step, 0)), (21, {1: 1, 2: -1}.get(step, 0))]:
        c.rect(ax, 16 + b + ay, ax + 1, 18 + b + ay, "r0" if ax == 21 else "r1")
        c.rect(ax, 19 + b + ay, ax + 1, 20 + b + ay, "sk")
    if back:
        c.rect(10, 3 + b, 21, 15 + b, "h1"); c.rect(10, 13 + b, 21, 15 + b, "h0")
        c.rect(20, 5 + b, 21, 15 + b, "h0"); c.rect(12, 4 + b, 16, 4 + b, "h2")
        c.rect(14, 7 + b, 14, 11 + b, "h0"); c.rect(17, 8 + b, 17, 12 + b, "h0")
    else:
        c.rect(10, 4 + b, 21, 15 + b, "sk"); c.rect(20, 8 + b, 21, 15 + b, "sk0")
        c.rect(10, 3 + b, 21, 7 + b, "h1"); c.rect(12, 4 + b, 16, 4 + b, "h2")
        c.rect(10, 8 + b, 11, 12 + b, "h0"); c.rect(20, 8 + b, 21, 12 + b, "h0")
        for fx in (12, 13, 15, 17, 18): c.px(fx, 8 + b, "h1")
        for ex in (13, 18): c.rect(ex, 10 + b, ex, 11 + b, "ol")
        c.px(15, 13 + b, "sk0"); c.px(16, 13 + b, "sk0")
    c.outline(); c.shadow_ellipse(16, 30, 7, 2)
    return c


def char_side(step):  # virado para a direita
    c = Canvas(32, 32); b = -1 if step else 0
    if step == 0:
        c.rect(14, 24, 17, 27, "p1"); c.rect(14, 28, 18, 29, "d0")
    else:
        fc, bc = ("p1", "p0") if step == 1 else ("p0", "p1")
        c.rect(11, 24, 13, 26, bc); c.rect(10, 27, 13, 28, "d0")
        c.rect(17, 24, 19, 26, fc); c.rect(17, 27, 20, 28, "d0")
    c.rect(12, 16 + b, 19, 23 + b, "r1"); c.rect(12, 16 + b, 13, 23 + b, "r0")
    c.rect(12, 22 + b, 19, 22 + b, "d0")
    ax = {0: 15, 1: 13, 2: 17}[step]
    c.rect(ax, 16 + b, ax + 1, 19 + b, "r0"); c.rect(ax, 20 + b, ax + 1, 21 + b, "sk")
    c.rect(11, 4 + b, 21, 15 + b, "sk"); c.rect(11, 13 + b, 13, 15 + b, "sk0")
    c.rect(11, 3 + b, 21, 7 + b, "h1"); c.rect(13, 4 + b, 18, 4 + b, "h2")
    c.rect(11, 8 + b, 15, 13 + b, "h0"); c.rect(16, 8 + b, 16, 9 + b, "h1")
    c.rect(19, 10 + b, 19, 11 + b, "ol"); c.px(16, 11 + b, "sk0")
    c.outline(); c.shadow_ellipse(16, 30, 7, 2)
    return c


# ---------------------------------------------------------------- props
def tree():
    c = Canvas(64, 64)
    c.rect(28, 42, 35, 57, "d1"); c.rect(33, 42, 35, 57, "d0"); c.rect(29, 44, 29, 52, "d2")
    c.rect(25, 55, 27, 57, "d1"); c.rect(36, 55, 38, 57, "d0")
    shaded_blob(c, [(32, 26, 17), (19, 33, 10), (45, 33, 10), (32, 13, 11), (24, 19, 9), (41, 20, 9)],
                ["g0", "g1", "g2", "g3"], seed=3)
    c.outline(); c.shadow_ellipse(32, 58, 14, 4)
    return c


def rock():
    c = Canvas(32, 32)
    shaded_blob(c, [(16, 20, 10), (11, 22, 7), (21, 21, 7)], ["s0", "s1", "s2", "s3"], seed=4)
    c.outline(); c.shadow_ellipse(17, 28, 12, 3)
    return c


def bush():
    c = Canvas(32, 32)
    shaded_blob(c, [(16, 18, 9), (9, 21, 6), (23, 21, 6), (16, 13, 6)], ["g0", "g1", "g2", "g3"], seed=6)
    for bx, by in [(12, 17), (19, 20), (15, 23), (21, 15)]:
        c.px(bx, by, "r1"); c.px(bx + 1, by + 1, "r0")
    c.outline(); c.shadow_ellipse(16, 28, 11, 3)
    return c


def chest(open_=False):
    c = Canvas(32, 32)
    c.rect(7, 15, 24, 26, "d1"); c.rect(7, 25, 24, 26, "d0"); c.rect(22, 15, 24, 26, "d0")
    for bx in (10, 21): c.rect(bx, 15, bx, 26, "au0")
    if open_:
        c.rect(7, 6, 24, 11, "d0"); c.rect(8, 7, 23, 7, "d1")
        c.rect(8, 12, 23, 14, "ol")
        for gx in (10, 13, 16, 19, 21): c.px(gx, 13, "au"); c.px(gx + 1, 12, "au")
        c.rect(7, 15, 24, 15, "au")
    else:
        c.rect(7, 9, 24, 14, "d2"); c.rect(7, 9, 24, 10, "d3"); c.rect(22, 9, 24, 14, "d1")
        for bx in (10, 21): c.rect(bx, 9, bx, 14, "au0")
        c.rect(7, 14, 24, 14, "au")
        c.rect(15, 13, 16, 17, "au"); c.px(15, 16, "ol"); c.px(16, 16, "au0")
    c.outline(); c.shadow_ellipse(16, 28, 11, 2)
    return c


def sign():
    c = Canvas(32, 32)
    c.rect(15, 18, 16, 28, "d1"); c.rect(16, 18, 16, 28, "d0")
    c.rect(6, 7, 25, 18, "d2"); c.rect(6, 7, 25, 7, "d3"); c.rect(6, 17, 25, 18, "d1")
    for ly, x0, x1 in [(10, 9, 22), (13, 9, 18), (15, 9, 20)]: c.rect(x0, ly, x1, ly, "d0")
    c.outline(); c.shadow_ellipse(16, 29, 6, 2)
    return c


def flowers():
    c = Canvas(32, 32)
    for i, (fx, fy) in enumerate([(6, 7), (20, 5), (13, 15), (25, 18), (7, 24), (19, 26)]):
        petal = ["wh", "r1", "au"][i % 3]
        center = "au0" if petal == "au" else "au"
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]: c.px(fx + dx, fy + dy, petal)
        c.px(fx, fy, center); c.px(fx, fy + 2, "g0")
    return c


SLIME_CORES = {"verde": ["g0", "g1", "g2", "g3"], "azul": ["w0", "w1", "w2", "w3"], "rubro": ["r0", "r1", "r2", "wh"]}


def slime(cores, frame=0):
    """Slime em forma de gota; frame 1 = achatado (animação de pulo)."""
    c = Canvas(32, 32)
    rx, h = (11, 15) if frame == 0 else (13, 12)
    base = 28
    for y in range(c.h):
        for x in range(c.w):
            dx, dy = (x + .5 - 16) / rx, (y + .5 - base) / h
            if y < base and dx * dx + dy * dy < 1:
                l = -(dx * 0.9 + dy * 1.1) * 0.6 + (hsh(x, y, 8) - .5) * .2
                c.px(x, y, cores[3] if l > .62 else cores[2] if l > .25 else cores[1] if l > -.15 else cores[0])
    top = base - h
    for gx, gy in [(11, top + 4), (12, top + 3), (13, top + 3), (11, top + 5)]: c.px(gx, gy, cores[3])
    ey = base - (7 if frame == 0 else 6)
    for ex in (12, 19):
        c.rect(ex, ey, ex + 1, ey + 2, "ol"); c.px(ex, ey, "wh")
    c.rect(15, ey + 3, 16, ey + 3, cores[0])
    c.outline(); c.shadow_ellipse(16, 29, rx + 1, 2)
    return c


# ---------------------------------------------------------------- vila
TELHADOS = {"vermelho": ["r0", "r1", "r2", "wh"], "azul": ["w0", "w1", "w2", "w3"], "verde": ["g0", "g1", "g2", "g3"]}


def house(roof, icon=None):
    """Casa 3x3 tiles (96x96). Porta no tile do meio da linha de baixo."""
    c = Canvas(96, 96)
    c.rect(10, 50, 85, 89, "d3")
    for bx in (10, 47, 84): c.rect(bx, 50, bx + 1, 89, "d1")
    c.rect(10, 84, 85, 89, "s1"); c.rect(10, 84, 85, 84, "s2")
    for sx in range(13, 84, 8): c.px(sx, 87, "s0")
    for wx in (18, 64):
        c.rect(wx, 60, wx + 13, 72, "d0"); c.rect(wx + 1, 61, wx + 12, 71, "w2")
        c.rect(wx + 1, 61, wx + 5, 64, "w3"); c.rect(wx + 6, 61, wx + 7, 71, "d0"); c.rect(wx + 1, 66, wx + 12, 66, "d0")
        c.rect(wx - 1, 73, wx + 14, 74, "d1")
    c.rect(39, 62, 56, 89, "d0"); c.rect(40, 63, 55, 89, "d1")
    for px_ in (44, 48, 52): c.rect(px_, 63, px_, 89, "d0")
    c.rect(53, 76, 54, 77, "au")
    for y in range(4, 51):
        for x in range(4, 92):
            if y < 8: col = roof[3] if y > 4 else roof[2]
            elif y >= 47: col = roof[0]
            else:
                ry, row = (y - 8) % 6, (y - 8) // 6
                seam = (x + (6 if row % 2 else 0)) % 12 == 0
                col = roof[0] if ry == 5 or seam else roof[2] if ry == 0 else roof[1]
            c.px(x, y, col)
    c.rect(70, 0, 78, 14, "s1"); c.rect(70, 0, 78, 1, "s2"); c.rect(76, 2, 78, 14, "s0")
    if icon:
        c.rect(40, 52, 55, 60, "d2"); c.rect(40, 52, 55, 52, "d3")
        if icon == "lua":
            for x, y in [(47, 53), (46, 54), (45, 55), (45, 56), (45, 57), (46, 58), (47, 59), (48, 59), (49, 58)]: c.px(x, y, "au")
        if icon == "pocao":
            c.rect(47, 53, 48, 54, "s2"); c.rect(46, 55, 49, 59, "r1"); c.px(46, 55, "r2")
    c.outline(); c.shadow_ellipse(48, 91, 42, 4)
    return c


def well():
    c = Canvas(32, 32)
    for y in range(32):
        for x in range(32):
            dx, dy = (x + .5 - 16) / 12, (y + .5 - 23) / 7
            if dx * dx + dy * dy < 1:
                if ((x + .5 - 16) / 8) ** 2 + ((y + .5 - 22) / 4) ** 2 < 1:
                    c.px(x, y, "w0" if y > 21 else "ol")
                else:
                    c.px(x, y, "s3" if dy < -0.5 else "s2" if dx < 0.3 else "s1")
    for x0 in (5, 25):
        c.rect(x0, 6, x0 + 1, 21, "d1"); c.rect(x0 + 1, 8, x0 + 1, 21, "d0")
    c.rect(3, 3, 28, 7, "r1"); c.rect(3, 3, 28, 3, "r2"); c.rect(3, 7, 28, 8, "r0")
    c.rect(15, 9, 15, 14, "d0"); c.rect(13, 14, 18, 17, "au0"); c.rect(13, 14, 18, 14, "au")
    c.outline(); c.shadow_ellipse(16, 30, 13, 2)
    return c


def fence():
    c = Canvas(32, 32)
    c.rect(0, 15, 31, 16, "d2"); c.rect(0, 17, 31, 17, "d1")
    c.rect(0, 22, 31, 23, "d2"); c.rect(0, 24, 31, 24, "d1")
    for px_ in (4, 20):
        c.rect(px_, 10, px_ + 3, 27, "d1"); c.rect(px_, 10, px_ + 3, 11, "d3"); c.rect(px_ + 3, 12, px_ + 3, 27, "d0")
    c.outline()
    return c


def barrel():
    c = Canvas(32, 32)
    c.rect(9, 10, 22, 27, "d1"); c.rect(9, 10, 11, 27, "d2"); c.rect(20, 10, 22, 27, "d0")
    for by in (13, 23): c.rect(9, by, 22, by + 1, "s1")
    c.rect(10, 7, 21, 10, "d2"); c.rect(11, 8, 20, 9, "d0")
    c.outline(); c.shadow_ellipse(16, 29, 9, 2)
    return c


# ---------------------------------------------------------------- interiores
def plank_grid(v=0):
    g = [[None] * T for _ in range(T)]
    for y in range(T):
        for x in range(T):
            row, yy = y // 8, y % 8
            off = (row * 13 + v * 7) % 16
            seam = (x - off) % 16 == 0
            r = hsh(x, y, 40 + v)
            g[y][x] = "d1" if yy == 7 or seam else "d3" if r < 0.05 else "d0" if r < 0.07 else "d2"
    return g


def wall_grid(window=False):
    g = [[None] * T for _ in range(T)]
    for y in range(T):
        for x in range(T):
            if y == 0: c = "d0"
            elif y < 3: c = "d1"
            elif y >= 30: c = "d0"
            elif y == 20: c = "d0"
            elif y > 20: c = "d0" if x % 8 == 0 else "d2" if y == 21 else "d1"
            else: c = "s3" if hsh(x, y, 44) < 0.06 else "wh"
            g[y][x] = c
    if window:
        for y in range(4, 18):
            for x in range(8, 24):
                edge = y in (4, 17) or x in (8, 23)
                cross = x in (15, 16) or y == 10
                g[y][x] = "d0" if edge or cross else ("w3" if (x < 12 and y < 8) else "w2")
        for y in range(4, 19):
            for x in (5, 6, 7, 24, 25, 26):
                g[y][x] = "r0" if x in (7, 24) else "r1"
    return g


def border_grid():
    return [["ol"] * T for _ in range(T)]


def door_grid():
    g = plank_grid(1)
    for y in range(8, 26):
        for x in range(5, 27):
            edge = y in (8, 25) or x in (5, 26)
            g[y][x] = "au" if edge else ("r0" if (x + y) % 6 == 0 else "r1")
    return g


def rug_tiles():
    """Tapete 96x96 fatiado em 9 pedaços (cantos, bordas, centro) que repetem sem emenda."""
    S = 96
    g = [[None] * S for _ in range(S)]
    for y in range(S):
        for x in range(S):
            d = min(x, y, S - 1 - x, S - 1 - y)
            if d < 2: c = "au0"
            elif d < 4: c = "au"
            elif d < 6: c = "r0"
            else:
                px, py = x % 16, y % 16
                c = "r0" if abs(px - 8) + abs(py - 8) == 5 else "au" if (px, py) == (8, 8) else "r1"
            g[y][x] = c
    for cx, cy in [(0, 0), (S - 1, 0), (0, S - 1), (S - 1, S - 1)]:
        g[cy][cx] = None
    pieces = []
    for ty in range(3):
        for tx in range(3):
            pieces.append([row[tx * T:(tx + 1) * T] for row in g[ty * T:(ty + 1) * T]])
    return pieces


def bed():
    c = Canvas(32, 64)
    c.rect(3, 4, 28, 60, "d1"); c.rect(3, 4, 28, 14, "d0"); c.rect(5, 6, 26, 7, "d1")
    c.rect(5, 14, 26, 56, "wh"); c.rect(8, 16, 23, 24, "wh"); c.rect(8, 23, 23, 24, "s3")
    c.rect(5, 27, 26, 56, "r1"); c.rect(5, 27, 26, 30, "r2"); c.rect(24, 31, 26, 56, "r0")
    c.rect(3, 56, 28, 60, "d0")
    c.outline()
    return c


def shelf(potions=False):
    c = Canvas(32, 64)
    c.rect(3, 4, 28, 60, "d0"); c.rect(2, 2, 29, 5, "d1"); c.rect(2, 2, 29, 2, "d2")
    c.rect(5, 7, 26, 58, "ol")
    cores = ["r1", "w2", "g2", "au0", "r0", "w1", "g1"]
    for i, sy in enumerate((20, 36, 52)):
        c.rect(5, sy, 26, sy + 2, "d2")
        x = 6
        while x < 25:
            if potions:
                col = cores[(x + i) % 3 * 1]
                c.rect(x, sy - 7, x + 3, sy - 1, ["r1", "w2", "g2"][(x // 5 + i) % 3]); c.rect(x + 1, sy - 9, x + 2, sy - 8, "s3")
                c.px(x, sy - 7, "wh"); x += 5
            else:
                w = 2 + int(hsh(x, sy, 3) * 3); h = 8 + int(hsh(x, sy, 4) * 5)
                c.rect(x, sy - h, min(x + w - 1, 25), sy - 1, cores[int(hsh(x, i, 5) * len(cores))]); x += w + 1
    c.outline()
    return c


def fireplace():
    c = Canvas(64, 64)
    for y in range(10, 61):
        for x in range(4, 60):
            by, yy = (y - 10) // 6, (y - 10) % 6
            xx = (x - 4 + (by % 2) * 6) % 12
            c.px(x, y, "s0" if yy == 5 or xx == 11 else ("s2" if hsh(x // 12, by, 2) < .4 else "s1"))
    c.rect(2, 6, 61, 12, "d1"); c.rect(2, 6, 61, 7, "d2"); c.rect(2, 12, 61, 12, "d0")
    c.rect(16, 28, 47, 60, "ol")
    c.rect(19, 52, 44, 56, "d0"); c.rect(21, 52, 42, 53, "d1")
    flames = [(31, 36), (27, 42), (36, 40), (24, 47), (31, 45), (39, 47)]
    for fx, fy in flames:
        for dy in range(0, 52 - fy):
            half = max(0, (dy * 2) // 5)
            for dx in range(-half, half + 1):
                c.px(fx + dx, fy + dy, "wh" if abs(dx) < 1 and dy > 4 else "au" if abs(dx) <= half // 2 else "r1")
    c.outline()
    return c


def table():
    c = Canvas(32, 32)
    c.rect(4, 8, 27, 19, "d2"); c.rect(4, 8, 27, 9, "d3"); c.rect(4, 20, 27, 23, "d1")
    c.rect(6, 24, 8, 28, "d0"); c.rect(23, 24, 25, 28, "d0")
    c.rect(10, 11, 12, 15, "wh"); c.px(13, 12, "wh"); c.rect(17, 12, 22, 15, "au0"); c.rect(18, 12, 21, 12, "au")
    c.outline(); c.shadow_ellipse(16, 29, 12, 2)
    return c


def chair():
    c = Canvas(32, 32)
    c.rect(10, 4, 21, 14, "d1"); c.rect(12, 6, 13, 13, "d2"); c.rect(18, 6, 19, 13, "d2")
    c.rect(9, 15, 22, 20, "d2"); c.rect(9, 15, 22, 15, "d3")
    c.rect(10, 21, 11, 27, "d0"); c.rect(20, 21, 21, 27, "d0")
    c.outline(); c.shadow_ellipse(16, 28, 7, 2)
    return c


def counter():
    c = Canvas(32, 32)
    c.rect(0, 6, 31, 12, "d3"); c.rect(0, 12, 31, 13, "d2")
    c.rect(0, 14, 31, 28, "d1"); c.rect(0, 14, 31, 14, "d0")
    for x in (0, 15, 16): c.rect(x, 15, x, 28, "d0")
    c.rect(3, 17, 12, 25, "d2"); c.rect(19, 17, 28, 25, "d2"); c.rect(0, 28, 31, 29, "d0")
    c.outline()
    return c


def plant():
    c = Canvas(32, 32)
    shaded_blob(c, [(16, 13, 8), (10, 16, 5), (22, 16, 5)], ["g0", "g1", "g2", "g3"], seed=12)
    c.rect(11, 20, 20, 28, "d1"); c.rect(10, 19, 21, 21, "d2"); c.rect(18, 22, 20, 28, "d0")
    c.outline(); c.shadow_ellipse(16, 29, 7, 2)
    return c


def vase():
    c = Canvas(32, 32)
    shaded_blob(c, [(16, 20, 8)], ["d0", "d1", "d2", "d3"], seed=13)
    c.rect(13, 9, 18, 12, "d1"); c.rect(12, 8, 19, 9, "d2"); c.rect(13, 19, 18, 19, "au0")
    c.outline(); c.shadow_ellipse(16, 28, 8, 2)
    return c


def gato():
    c = Canvas(32, 32)
    shaded_blob(c, [(17, 21, 8), (11, 18, 5)], ["d1", "au0", "au", "d3"], seed=14)
    for x, y in [(8, 13), (9, 12), (9, 13), (13, 13), (14, 12), (14, 13)]: c.px(x, y, "au0")
    c.rect(9, 18, 10, 18, "ol"); c.rect(12, 18, 13, 18, "ol"); c.px(11, 20, "r1")
    for x in (16, 19, 22): c.rect(x, 15, x, 18, "d1")
    for x, y in [(24, 25), (23, 26), (21, 27), (19, 27), (17, 27)]: c.px(x, y, "au0")
    c.outline(); c.shadow_ellipse(16, 28, 10, 2)
    return c


# ---------------------------------------------------------------- montagem
def paste_grid(sheet, g, tx, ty): sheet.alpha_composite(grid_to_img(g), (tx * T, ty * T))


def main():
    os.makedirs(OUT, exist_ok=True)
    grass = [grass_grid(v) for v in range(3)]
    dirt, stone = dirt_grid(), stone_grid()
    water = [water_grid(f) for f in range(2)]

    # --- tileset de terreno: 8 x 7 tiles
    ts = Image.new("RGBA", (8 * T, 7 * T))
    for i, g in enumerate([grass[0], grass[1], grass[2], dirt, stone, water[0], water[1]]):
        paste_grid(ts, g, i, 0)
    paste_grid(ts, grass[0], 7, 0); ts.alpha_composite(flowers().img(), (7 * T, 0))
    trans = {"terra": {}, "agua0": {}, "agua1": {}}
    for m in range(16):
        trans["terra"][m] = transition(m, grass[0], dirt, "terra")
        trans["agua0"][m] = transition(m, grass[0], water[0], "agua")
        trans["agua1"][m] = transition(m, grass[0], water[1], "agua")
        paste_grid(ts, trans["terra"][m], m % 8, 1 + m // 8)
        paste_grid(ts, trans["agua0"][m], m % 8, 3 + m // 8)
        paste_grid(ts, trans["agua1"][m], m % 8, 5 + m // 8)
    ts.save(os.path.join(OUT, "tileset_terreno.png"))

    # --- personagem: 3 colunas (passo A, parado, passo B) x 4 linhas (baixo, esquerda, direita, cima)
    ch = Image.new("RGBA", (3 * 32, 4 * 32))
    for col, step in enumerate([1, 0, 2]):
        right = char_side(step)
        for row, spr in enumerate([char_front(step), right.mirrored(), right, char_front(step, back=True)]):
            ch.alpha_composite(spr.img(), (col * 32, row * 32))
    ch.save(os.path.join(OUT, "personagem_heroi.png"))

    # --- props: 6 x 2 tiles
    pr = Image.new("RGBA", (6 * T, 2 * T))
    pr.alpha_composite(tree().img(), (0, 0))
    for (tx, ty), spr in {(2, 0): rock(), (3, 0): bush(), (4, 0): chest(), (5, 0): chest(True),
                          (2, 1): sign(), (3, 1): flowers()}.items():
        pr.alpha_composite(spr.img(), (tx * T, ty * T))
    pr.save(os.path.join(OUT, "props.png"))

    # --- slimes: 2 frames x 3 cores (verde, azul, rubro)
    sl = Image.new("RGBA", (2 * 32, 3 * 32))
    for row, nome in enumerate(["verde", "azul", "rubro"]):
        for f in range(2):
            sl.alpha_composite(slime(SLIME_CORES[nome], f).img(), (f * 32, row * 32))
    sl.save(os.path.join(OUT, "slimes.png"))

    # --- vila: 3 casas (96x96), poço, cerca, barril (32x32)
    vl = Image.new("RGBA", (12 * T, 3 * T))
    vl.alpha_composite(house(TELHADOS["vermelho"], "lua").img(), (0, 0))
    vl.alpha_composite(house(TELHADOS["azul"], "pocao").img(), (96, 0))
    vl.alpha_composite(house(TELHADOS["verde"]).img(), (192, 0))
    for i, spr in enumerate([well(), fence(), barrel()]):
        vl.alpha_composite(spr.img(), (288 + i * 32, 0))
    vl.save(os.path.join(OUT, "vila.png"))

    # --- interiores: tiles (8 x 3) e móveis (8 x 2)
    it = Image.new("RGBA", (8 * T, 3 * T))
    for i, g in enumerate([plank_grid(0), plank_grid(1), wall_grid(), wall_grid(True), border_grid(), door_grid()]):
        paste_grid(it, g, i, 0)
    for i, g in enumerate(rug_tiles()):
        paste_grid(it, g, i % 8, 1 + i // 8)
    it.save(os.path.join(OUT, "interior_tiles.png"))
    mv = Image.new("RGBA", (8 * T, 2 * T))
    for spr, (x, y) in [(bed(), (0, 0)), (shelf(), (32, 0)), (shelf(True), (64, 0)), (fireplace(), (96, 0)),
                        (table(), (160, 0)), (chair(), (160, 32)), (counter(), (192, 0)), (plant(), (192, 32)),
                        (vase(), (224, 0)), (gato(), (224, 32))]:
        mv.alpha_composite(spr.img(), (x, y))
    mv.save(os.path.join(OUT, "moveis.png"))

    # --- paleta
    keys = list(PALETA)
    pal = Image.new("RGBA", (len(keys) * 16, 16))
    for i, k in enumerate(keys): pal.paste(PALETA[k] + (255,), (i * 16, 0, i * 16 + 16, 16))
    pal.save(os.path.join(OUT, "paleta.png"))

    # --- metadados
    meta = {
        "tile_size": T,
        "tileset_terreno.png": {
            "colunas": 8, "linhas": 7,
            "linha0": ["grama_a", "grama_b", "grama_c", "terra", "pedra", "agua_f0", "agua_f1", "grama_flores"],
            "linhas1-2": "transições grama->terra, índice = máscara de cantos (TL=1, TR=2, BL=4, BR=8)",
            "linhas3-4": "transições grama->água frame 0 (mesma máscara)",
            "linhas5-6": "transições grama->água frame 1 (mesma máscara)",
            "tile_id_transicao": "id = linha_inicial*8 + mascara",
        },
        "personagem_heroi.png": {"frame": [32, 32], "colunas": ["passo_a", "parado", "passo_b"],
                                 "linhas": ["baixo", "esquerda", "direita", "cima"],
                                 "animacao_andar": [0, 1, 2, 1], "fps_sugerido": 8},
        "props.png": {"arvore": [0, 0, 64, 64], "pedra": [64, 0, 32, 32], "arbusto": [96, 0, 32, 32],
                      "bau_fechado": [128, 0, 32, 32], "bau_aberto": [160, 0, 32, 32],
                      "placa": [64, 32, 32, 32], "flores": [96, 32, 32, 32]},
        "vila.png": {"pousada": [0, 0, 96, 96], "loja": [96, 0, 96, 96], "casa": [192, 0, 96, 96], "poco": [288, 0, 32, 32], "cerca": [320, 0, 32, 32], "barril": [352, 0, 32, 32], "porta": "tile do meio da linha de baixo"},
        "interior_tiles.png": {"linha0": ["piso_a", "piso_b", "parede", "parede_janela", "borda", "porta_saida"], "linhas1-2": "tapete em 9 partes: SE, S, SD, E, C, D, IE, I, ID"},
        "moveis.png": {"cama": [0, 0, 32, 64], "estante": [32, 0, 32, 64], "prateleira_pocoes": [64, 0, 32, 64], "lareira": [96, 0, 64, 64],
                       "mesa": [160, 0, 32, 32], "cadeira": [160, 32, 32, 32], "balcao": [192, 0, 32, 32], "planta": [192, 32, 32, 32],
                       "vaso": [224, 0, 32, 32], "gato": [224, 32, 32, 32]},
        "slimes.png": {"frame": [32, 32], "colunas": ["normal", "achatado"], "linhas": ["verde", "azul", "rubro"]},
        "paleta": {k: "#%02x%02x%02x" % v for k, v in PALETA.items()},
    }
    with open(os.path.join(OUT, "assets.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # --- mapa de demonstração
    W, H = 20, 14
    cg = [[0] * (W + 1) for _ in range(H + 1)]
    for y in range(H + 1):
        for x in range(W + 1):
            if ((x - 15) / 4.3) ** 2 + ((y - 4) / 3.3) ** 2 < 1: cg[y][x] = 2
    for x in range(0, 13): cg[9][x] = cg[10][x] = 1
    for y in range(10, H + 1): cg[y][11] = cg[y][12] = 1
    for y in range(2, 8):
        for x in range(1, 7): cg[y][x] = 1
    for y in range(7, 10): cg[y][3] = cg[y][4] = 1
    mp = Image.new("RGBA", (W * T, H * T))
    for ty in range(H):
        for tx in range(W):
            cs = [cg[ty][tx], cg[ty][tx + 1], cg[ty + 1][tx], cg[ty + 1][tx + 1]]
            if 2 <= tx <= 4 and 3 <= ty <= 5:
                g = stone
            elif 2 in cs:
                g = trans["agua0"][sum(1 << i for i, c in enumerate(cs) if c == 2)]
            else:
                m = sum(1 << i for i, c in enumerate(cs) if c == 1)
                if m: g = trans["terra"][m]
                else:
                    r = hsh(tx, ty, 99); g = grass[0 if r < .6 else 1 if r < .85 else 2]
            paste_grid(mp, g, tx, ty)
    for fx, fy in [(8, 2), (9, 6), (15, 12), (1, 12), (17, 9), (6, 7)]:
        mp.alpha_composite(flowers().img(), (fx * T, fy * T))
    objs = [(tree(), 0, 10), (tree(), 14, 10), (tree(), 17, 11), (tree(), 7, -1), (tree(), 18, -1),
            (rock(), 10, 1), (rock(), 19, 7), (bush(), 8, 12), (bush(), 0, 7), (bush(), 9, 4),
            (chest(), 3, 4), (sign(), 13, 8), (char_front(0), 6, 9), (char_side(1), 11, 12)]
    objs.sort(key=lambda o: o[2] * T + o[0].h)
    for spr, tx, ty in objs:
        mp.alpha_composite(spr.img(), (tx * T, ty * T))
    mp.resize((W * T * 2, H * T * 2), Image.NEAREST).save(os.path.join(OUT, "preview_mapa.png"))

    # --- catálogo ampliado 3x
    S = 3
    parts = [("Tileset de terreno (linha 1: bases | 2-3: grama/terra | 4-7: grama/agua, 2 frames)", ts),
             ("Personagem (passo A / parado / passo B  x  baixo, esquerda, direita, cima)", ch),
             ("Props", pr), ("Paleta", pal)]
    width = max(p[1].width for p in parts) * S + 40
    height = sum(p[1].height * S + 50 for p in parts) + 20
    cat = Image.new("RGBA", (width, height), (40, 36, 48, 255))
    d = ImageDraw.Draw(cat); y = 20
    for label, im in parts:
        d.text((20, y), label, fill=(230, 230, 230)); y += 22
        big = im.resize((im.width * S, im.height * S), Image.NEAREST)
        cat.alpha_composite(big, (20, y)); y += big.height + 28
    cat.save(os.path.join(OUT, "catalogo.png"))
    print("ok ->", OUT)


if __name__ == "__main__":
    main()
