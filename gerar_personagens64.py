"""Personagens jogáveis e inimigos em 64x64, na mesma paleta e com o mesmo contorno dos outros assets.

Saída (em rpg_assets_amostra/):
  herois_64.png  -> 3 blocos de 320x320 (Lia, Davi, Nina), cada um com 5 colunas x 5 linhas de 64x64
                    linhas 0-3: andar (baixo, esquerda, direita, cima) com colunas passo A / parado / passo B
                    linha 4: poses de batalha viradas para a esquerda: pronto, ataque, magia, ferido, caído
  slimes_64.png  -> 4 colunas (normal, achatado, ataque, ferido) x 3 linhas (verde, azul, rubro)
"""
import os
from PIL import Image
from gerar_assets import Canvas, hsh, OUT

SKIN = ("sk0", "sk", "sk2")
CHARS = [
    dict(name="lia", tunic=("r0", "r1", "r2"), hair=("h0", "h1", "h2"), eye="w1", style="ponytail"),
    dict(name="davi", tunic=("t0", "t1", "t2"), hair=("k0", "k1", "k2"), eye="d0", style="spiky"),
    dict(name="nina", tunic=("g0", "g1", "g2"), hair=("au0", "au", "au2"), eye="g0", style="long"),
]


def R(c, x0, y0, x1, y1, col):
    c.rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), col)


def ell(c, cx, cy, rx, ry, fn):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            dx, dy = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            if dx * dx + dy * dy < 1:
                col = fn(dx, dy, x, y)
                if col: c.px(x, y, col)


def shade3(cols, bias=0.0):
    def f(dx, dy, x, y):
        l = -(dx * 0.6 + dy * 0.8) + bias
        return cols[2] if l > 0.5 else cols[0] if l < -0.45 else cols[1]
    return f


def hair_shade(h, cut=None):
    h0, h1, h2 = h
    def f(dx, dy, x, y):
        if cut is not None and y > cut: return None
        if -0.75 < dx < 0.05 and -0.8 < dy < -0.45: return h2
        if dx > 0.55 or dy > 0.75: return h0
        return h1
    return f


# ---------------------------------------------------------------- vista de frente / costas
def legs_front(c, step):
    for i, lx in enumerate((25, 33)):
        lifted = (step == 1 and i == 0) or (step == 2 and i == 1)
        bot = 54 - (2 if lifted else 0)
        R(c, lx, 46, lx + 5, bot, "p1"); R(c, lx + 4, 46, lx + 5, bot, "p0")
        R(c, lx - 1, bot + 1, lx + 5, bot + 4, "d0"); R(c, lx, bot + 1, lx + 3, bot + 1, "d1")


def torso_front(c, cfg, b, back):
    t0, t1, t2 = cfg["tunic"]
    R(c, 23, 31 + b, 40, 45 + b, t1); R(c, 37, 31 + b, 40, 45 + b, t0); R(c, 23, 31 + b, 24, 41 + b, t2)
    R(c, 22, 44 + b, 41, 47 + b, t1); R(c, 38, 44 + b, 41, 47 + b, t0); R(c, 22, 47 + b, 41, 47 + b, t0)
    R(c, 23, 42 + b, 40, 43 + b, "d0")
    if back:
        R(c, 31, 33 + b, 32, 41 + b, t0)
    else:
        R(c, 29, 31 + b, 34, 32 + b, "sk"); R(c, 30, 33 + b, 33, 33 + b, "sk"); R(c, 31, 34 + b, 32, 34 + b, "sk0")
        for x, y in [(28, 31), (29, 33), (30, 34), (35, 31), (34, 33), (33, 34)]: c.px(x, y + b, t2)
        R(c, 30, 42 + b, 33, 43 + b, "au"); R(c, 31, 42 + b, 32, 42 + b, "au0")


def arms_front(c, cfg, b, step):
    t0, t1, _ = cfg["tunic"]
    sw = {0: (0, 0), 1: (-2, 2), 2: (2, -2)}[step]
    for ax, dy, col in ((19, sw[0], t1), (41, sw[1], t0)):
        R(c, ax, 32 + b + dy, ax + 3, 38 + b + dy, col)
        R(c, ax, 39 + b + dy, ax + 3, 42 + b + dy, "sk"); R(c, ax, 43 + b + dy, ax + 3, 44 + b + dy, "sk0")


def bangs(c, h, b, x0, x1, base=17, short=(25, 38), deep=3, side=6):
    h0, h1, h2 = h
    for x in range(x0, x1 + 1):
        if short[0] <= x <= short[1]:
            L = 2 + (1 if (x // 2) % 3 == 0 else 0)
        else:
            L = side
        R(c, x, base + b, x, base + b + L, h1); c.px(x, base + b + L, h0)


def head_front(c, cfg, b, back):
    h0, h1, h2 = cfg["hair"]; st = cfg["style"]
    R(c, 29, 28 + b, 34, 31 + b, "sk0")
    ell(c, 32, 20 + b, 11, 10.5, shade3(SKIN))
    if back:
        if st == "long": R(c, 20, 22 + b, 43, 42 + b, h1); [R(c, x, 26 + b, x, 42 + b, h0) for x in (24, 29, 34, 39)]; R(c, 20, 42 + b, 43, 42 + b, h0)
        ell(c, 32, 18 + b, 12.5, 11.5, hair_shade(cfg["hair"]))
        R(c, 25, 27 + b, 38, 29 + b, h1); R(c, 25, 29 + b, 38, 29 + b, h0)
        if st == "ponytail":
            R(c, 29, 24 + b, 34, 40 + b, h1); R(c, 33, 24 + b, 34, 40 + b, h0); R(c, 30, 41 + b, 33, 42 + b, h0)
            R(c, 28, 22 + b, 35, 24 + b, "r1"); c.px(28, 22 + b, "r2")
    else:
        for ex in (26, 35):
            R(c, ex, 21 + b, ex + 2, 21 + b, "ol"); R(c, ex, 22 + b, ex + 2, 24 + b, cfg["eye"])
            R(c, ex, 24 + b, ex + 2, 24 + b, "ol"); c.px(ex, 22 + b, "wh")
        R(c, 31, 28 + b, 32, 28 + b, "sk0"); c.px(32, 26 + b, "sk0")
        for x in (24, 25, 38, 39): c.px(x, 26 + b, "r2")
        ell(c, 32, 16 + b, 12.5, 9, hair_shade(cfg["hair"], cut=18 + b))
        bangs(c, cfg["hair"], b, 21, 43, side=10 if st != "long" else 12)
        if st == "long":
            R(c, 18, 20 + b, 22, 40 + b, h1); R(c, 41, 20 + b, 45, 40 + b, h0); R(c, 18, 40 + b, 22, 40 + b, h0)
            R(c, 21, 12 + b, 23, 14 + b, "r2"); c.px(22, 13 + b, "wh")
    if st == "ponytail" and not back:
        R(c, 40, 8 + b, 44, 11 + b, "r1"); c.px(42, 9 + b, "r0"); R(c, 41, 8 + b, 41, 8 + b, "r2")
    if st == "spiky":
        for i, cx in enumerate((24, 30, 36, 41)):
            for dy in range(5):
                w = max(0, 2 - dy // 2)
                R(c, cx - w, 8 - dy + b, cx + w, 8 - dy + b, h2 if i == 0 else h1)


def front(cfg, step, back=False):
    c = Canvas(64, 64); b = -1 if step else 0
    legs_front(c, step)
    torso_front(c, cfg, b, back)
    arms_front(c, cfg, b, step)
    head_front(c, cfg, b, back)
    c.outline(); c.shadow_ellipse(32, 59, 12, 3)
    return c


# ---------------------------------------------------------------- vista lateral (direita) e poses
def legs_side(c, step):
    if step == 0:
        R(c, 29, 46, 34, 54, "p1"); R(c, 29, 46, 30, 54, "p0")
        R(c, 28, 55, 37, 58, "d0"); R(c, 29, 55, 35, 55, "d1")
        return
    fc, bc = ("p1", "p0") if step == 1 else ("p0", "p1")
    R(c, 24, 46, 28, 53, bc); R(c, 21, 54, 28, 57, "d0")
    R(c, 34, 46, 38, 53, fc); R(c, 35, 54, 42, 57, "d0"); R(c, 36, 54, 40, 54, "d1")


def torso_side(c, cfg, b, lean=0):
    t0, t1, t2 = cfg["tunic"]
    R(c, 26 + lean, 31 + b, 38 + lean, 45 + b, t1); R(c, 26 + lean, 31 + b, 28 + lean, 45 + b, t0)
    R(c, 29 + lean, 31 + b, 37 + lean, 31 + b, t2)
    R(c, 25 + lean, 44 + b, 39 + lean, 47 + b, t1); R(c, 25 + lean, 47 + b, 39 + lean, 47 + b, t0)
    R(c, 26 + lean, 42 + b, 38 + lean, 43 + b, "d0"); R(c, 36 + lean, 42 + b, 37 + lean, 43 + b, "au")
    R(c, 35 + lean, 31 + b, 37 + lean, 32 + b, "sk")


def head_side(c, cfg, b, hx=0, eyes="open"):
    h0, h1, h2 = cfg["hair"]; st = cfg["style"]
    if st == "ponytail":
        for i, (px_, py) in enumerate([(21, 20), (19, 25), (18, 30), (19, 35)]):
            ell(c, px_ + hx, py + b, 3.4, 3.4, lambda dx, dy, x, y: h0 if dx > 0.3 or dy > 0.4 else h1)
    if st == "long":
        R(c, 20 + hx, 18 + b, 30 + hx, 41 + b, h1); R(c, 20 + hx, 18 + b, 21 + hx, 41 + b, h0); R(c, 20 + hx, 41 + b, 30 + hx, 41 + b, h0)
    R(c, 31 + hx, 28 + b, 35 + hx, 31 + b, "sk0")
    ell(c, 33 + hx, 20 + b, 10.5, 10.5, shade3(SKIN))
    R(c, 43 + hx, 23 + b, 44 + hx, 24 + b, "sk"); c.px(44 + hx, 24 + b, "sk0")
    if eyes == "open":
        R(c, 38 + hx, 21 + b, 39 + hx, 21 + b, "ol"); R(c, 38 + hx, 22 + b, 39 + hx, 24 + b, cfg["eye"])
        R(c, 38 + hx, 24 + b, 39 + hx, 24 + b, "ol"); c.px(38 + hx, 22 + b, "wh")
    elif eyes == "hurt":
        for x, y in [(39, 21), (38, 22), (39, 23)]: c.px(x + hx, y + b, "ol")
    else:
        R(c, 37 + hx, 23 + b, 39 + hx, 23 + b, "ol")
    c.px(40 + hx, 28 + b, "sk0"); c.px(39 + hx, 26 + b, "r2"); c.px(40 + hx, 26 + b, "r2")
    ell(c, 31 + hx, 16 + b, 12.5, 9, hair_shade(cfg["hair"], cut=18 + b))
    ell(c, 26 + hx, 22 + b, 6.5, 7.5, lambda dx, dy, x, y: h0 if dy > 0.5 else h1)
    R(c, 30 + hx, 21 + b, 31 + hx, 24 + b, "sk0")
    bangs(c, cfg["hair"], b, 33 + hx, 43 + hx, short=(33 + hx, 43 + hx))
    if st == "ponytail": R(c, 21 + hx, 16 + b, 24 + hx, 19 + b, "r1"); c.px(22 + hx, 16 + b, "r2")
    if st == "spiky":
        for i, (cx, top) in enumerate([(22, 10), (27, 6), (33, 5), (39, 7)]):
            for dy in range(5):
                w = max(0, 2 - dy // 2)
                R(c, cx - w + hx, top + 4 - dy + b, cx + w + hx, top + 4 - dy + b, h1 if i else h0)
    if st == "long": R(c, 34 + hx, 10 + b, 36 + hx, 12 + b, "r2"); c.px(35 + hx, 11 + b, "wh")


def arm_side(c, cfg, b, x, col=None):
    t0, t1, _ = cfg["tunic"]
    R(c, x, 32 + b, x + 3, 38 + b, col or t0); R(c, x, 39 + b, x + 3, 42 + b, "sk"); R(c, x, 43 + b, x + 3, 44 + b, "sk0")


def side(cfg, step):
    c = Canvas(64, 64); b = -1 if step else 0
    legs_side(c, step)
    torso_side(c, cfg, b)
    head_side(c, cfg, b)
    arm_side(c, cfg, b, {0: 31, 1: 28, 2: 34}[step])
    c.outline(); c.shadow_ellipse(32, 59, 12, 3)
    return c


def pose_attack(cfg):
    c = Canvas(64, 64); t0, t1, _ = cfg["tunic"]
    legs_side(c, 1)
    R(c, 22, 34, 25, 39, t0); R(c, 22, 40, 25, 42, "sk")           # braço de trás puxado
    torso_side(c, cfg, 0, lean=1)
    head_side(c, cfg, 0, hx=2)
    R(c, 37, 33, 44, 36, t1); R(c, 45, 33, 48, 36, "sk")           # braço esticado
    R(c, 48, 30, 49, 39, "au0"); R(c, 47, 30, 50, 30, "au")         # guarda da espada
    for i in range(13):
        R(c, 50 + i, 32 - i, 51 + i, 33 - i, "s3"); c.px(51 + i, 34 - i, "s1")
    c.px(63, 20, "wh")
    c.outline(); c.shadow_ellipse(32, 59, 13, 3)
    return c


def pose_cast(cfg):
    c = Canvas(64, 64); t0, t1, _ = cfg["tunic"]
    legs_side(c, 0)
    R(c, 27, 22, 30, 31, t0); R(c, 27, 16, 30, 21, "sk")            # braço de trás erguido
    torso_side(c, cfg, 0)
    head_side(c, cfg, 0, eyes="closed")
    R(c, 37, 31, 40, 34, t1); R(c, 41, 25, 44, 31, t1); R(c, 44, 19, 47, 24, "sk"); R(c, 44, 19, 47, 19, "sk0")
    for x, y, col in [(48, 13, "wh"), (44, 11, "w3"), (51, 17, "w3"), (52, 11, "au"), (28, 11, "au"), (47, 8, "w3")]:
        c.px(x, y, col); c.px(x + 1, y, col)
    c.outline(); c.shadow_ellipse(32, 59, 12, 3)
    return c


def pose_hurt(cfg):
    c = Canvas(64, 64); t0, t1, _ = cfg["tunic"]
    legs_side(c, 0)
    R(c, 21, 30, 24, 36, t0); R(c, 19, 27, 22, 30, "sk")
    torso_side(c, cfg, 1, lean=-2)
    head_side(c, cfg, 1, hx=-4, eyes="hurt")
    R(c, 35, 33, 38, 38, t1); R(c, 38, 37, 41, 40, "sk")
    for x, y in [(46, 12), (48, 16), (45, 18)]: c.px(x, y, "wh")
    c.outline(); c.shadow_ellipse(32, 59, 12, 3)
    return c


def pose_ko(cfg):
    c = Canvas(64, 64); t0, t1, t2 = cfg["tunic"]; h0, h1, h2 = cfg["hair"]
    R(c, 7, 49, 12, 57, "d0"); R(c, 13, 49, 26, 56, "p1"); R(c, 13, 49, 26, 50, "p0")
    R(c, 26, 46, 42, 57, t1); R(c, 26, 55, 42, 57, t0); R(c, 26, 46, 42, 46, t2)
    R(c, 30, 46, 31, 57, "d0"); R(c, 30, 50, 31, 52, "au")
    R(c, 30, 58, 40, 59, "sk")
    if cfg["style"] == "long": R(c, 46, 42, 60, 58, h1)
    ell(c, 50, 51, 8.5, 8.5, shade3(SKIN))
    ell(c, 54, 50, 8, 8.5, lambda dx, dy, x, y: (h0 if dx > 0.5 else h1) if dx > -0.1 else None)
    for y in (48, 53): R(c, 46, y, 48, y, "ol")
    c.px(44, 51, "sk0")
    c.outline(); c.shadow_ellipse(33, 59, 24, 3)
    return c


def hero_sheet(cfg):
    sheet = Image.new("RGBA", (5 * 64, 5 * 64))
    for col, step in enumerate([1, 0, 2]):
        r = side(cfg, step)
        for row, spr in enumerate([front(cfg, step), r.mirrored(), r, front(cfg, step, back=True)]):
            sheet.alpha_composite(spr.img(), (col * 64, row * 64))
    for col, spr in enumerate([side(cfg, 0), pose_attack(cfg), pose_cast(cfg), pose_hurt(cfg), pose_ko(cfg)]):
        sheet.alpha_composite(spr.mirrored().img(), (col * 64, 4 * 64))
    return sheet


# ---------------------------------------------------------------- slimes 64
SLIME_PAL = {"verde": ["g0", "g1", "g2", "g3"], "azul": ["w0", "w1", "w2", "w3"], "rubro": ["r0", "r1", "r2", "wh"]}


def slime64(kind, frame):
    """frame 0 normal, 1 achatado, 2 ataque (esticado para a frente), 3 ferido. Olham para a direita."""
    c = Canvas(64, 64); pal = SLIME_PAL[kind]
    rx, h, lean = {0: (22, 27, 0), 1: (25, 22, 0), 2: (19, 33, 6), 3: (26, 19, -3)}[frame]
    base = 58
    if kind == "azul": h += 5
    top = base - h
    for y in range(top - 2, base):
        t = (base - y) / h
        if t > 1: continue
        w = (1 - t * t) ** 0.5
        if kind == "azul": w *= (1 - 0.55 * max(0, t - 0.35))
        cx = 32 + lean * t
        for x in range(64):
            dx = (x + .5 - cx) / (rx * max(w, 0.001))
            if abs(dx) < 1:
                l = -(dx * 0.8) + (t - 0.5) * 1.2 + (hsh(x, y, 31) - .5) * .25
                col = pal[3] if l > 1.0 else pal[2] if l > 0.25 else pal[1] if l > -0.55 else pal[0]
                if y >= base - 3: col = pal[0]
                c.px(x, y, col)
    if kind == "rubro":
        for sx in (-9, 0, 9):
            px0 = int(32 + lean + sx); h0 = 6 if sx == 0 else 4
            for dy in range(h0):
                w2 = max(0, (h0 - dy) // 2)
                R(c, px0 - w2, top + 1 - dy, px0 + w2, top + 1 - dy, pal[2] if dy < h0 - 1 else pal[3])
    if kind == "azul":
        R(c, int(32 + lean * .9) - 1, top - 4, int(32 + lean * .9), top - 2, pal[2])
    gx, gy = int(32 + lean * .6 - rx * .45), int(top + h * .28)
    for x, y in [(0, 0), (1, 0), (2, 0), (0, 1), (-1, 1), (-1, 2), (0, 2)]: c.px(gx + x, gy + y, pal[3])
    c.px(gx + 3, gy - 1, "wh")
    for bx, by in [(-8, 10), (6, 6), (-2, 4)]:
        R(c, int(32 + bx), base - by, int(33 + bx), base - by + 1, pal[2])
    ey = int(base - h * 0.5); ex = int(32 + lean * .5)
    for e in (ex + 1, ex + 11):
        if frame == 3:
            for x, y in [(0, 0), (1, 1), (2, 2), (2, 0), (0, 2)]: c.px(e + x, ey + y, "ol")
        else:
            R(c, e, ey, e + 3, ey + 5, "ol"); R(c, e + 1, ey + 1, e + 2, ey + 2, "wh")
            if frame == 2: R(c, e - 1, ey - 3, e + 1, ey - 3, "ol"); c.px(e + 2, ey - 2, "ol")
    my = ey + 8
    if frame == 2: R(c, ex + 5, my, ex + 9, my + 3, "ol"); R(c, ex + 6, my + 2, ex + 8, my + 3, "r1")
    elif frame == 3: R(c, ex + 5, my + 1, ex + 8, my + 1, "ol")
    else: R(c, ex + 6, my, ex + 8, my, "ol"); c.px(ex + 5, my - 1, "ol"); c.px(ex + 9, my - 1, "ol")
    c.outline(); c.shadow_ellipse(32 + lean // 2, 60, rx + 3, 3)
    return c


def main():
    sheet = Image.new("RGBA", (3 * 320, 320))
    for i, cfg in enumerate(CHARS):
        sheet.alpha_composite(hero_sheet(cfg), (i * 320, 0))
    sheet.save(os.path.join(OUT, "herois_64.png"))
    sl = Image.new("RGBA", (4 * 64, 3 * 64))
    for row, k in enumerate(["verde", "azul", "rubro"]):
        for f in range(4):
            sl.alpha_composite(slime64(k, f).img(), (f * 64, row * 64))
    sl.save(os.path.join(OUT, "slimes_64.png"))
    print("ok -> herois_64.png, slimes_64.png")


if __name__ == "__main__":
    main()
