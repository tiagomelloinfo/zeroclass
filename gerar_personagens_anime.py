"""Personagens 128x128 em estilo JRPG / anime (chibi): cabeça grande, olhos expressivos, cabelo em mechas.

Gera os mesmos arquivos usados pelo jogo (substitui a versão anterior):
  herois_128.png -> 3 blocos de 640x640 (Lia, Davi, Nina); 5 colunas x 5 linhas de 128
                    linhas 0-3: andar (baixo, esquerda, direita, cima), colunas passo A / parado / passo B
                    linha 4: poses de batalha viradas para a esquerda: pronto, ataque, magia, ferido, caído
  npcs_128.png   -> 5 blocos de 384x512 (guarda, ancião, Lina, fazendeiro, mercadora); 3 colunas x 4 linhas
  slimes_128.png -> mesmos slimes da versão anterior (gerar_personagens128.py)
Usa o mesmo acabamento (cel shading, sombra de contato e contorno colorido) de gerar_personagens128.py.
"""
import os
from PIL import Image
from gerar_assets import Canvas, OUT
from gerar_personagens128 import tone, ell, rect, flat, star, finish, slime128

SKIN = ("sk2", "sk", "sk0")
PANTS = ("p1", "p1", "p0")
BOOTS = ("d1", "d0", "d0")
GLOVES = ("d2", "d1", "d0")
WHITE = ("wh", "s3", "s2")


# ---------------------------------------------------------------- primitivas
def poly(c, pts, cols, bias=0.0, axis="x", edge=True, hl=None):
    ys = [p[1] for p in pts]; xs = [p[0] for p in pts]
    y0, y1 = int(min(ys)), int(max(ys)); x0, x1 = min(xs), max(xs)
    S = set(); n = len(pts)
    for y in range(y0, y1 + 1):
        yc = y + 0.5; inter = []
        for i in range(n):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
            if (ay <= yc < by) or (by <= yc < ay):
                inter.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        inter.sort()
        for k in range(0, len(inter) - 1, 2):
            for x in range(int(round(inter[k])), int(round(inter[k + 1]))):
                S.add((x, y))
    for (x, y) in S:
        u = (x - x0) / max(1, x1 - x0) if axis == "x" else (y - y0) / max(1, y1 - y0)
        v = 0.15 + 0.7 * u + bias
        if edge and ((x + 1, y) not in S or (x, y + 1) not in S): v = 1.0
        if hl and (x - 1, y) not in S and (x, y - 1) in S:
            c.px(x, y, hl); continue
        c.px(x, y, tone(cols, v, x, y))
    return S


def sh(pts, dx=0, dy=0, mirror=False):
    """Desloca (e opcionalmente espelha em x=64) uma lista de pontos."""
    return [((128 - x if mirror else x) + dx, y + dy) for x, y in pts]


def lock(c, hair, pts, b=0, bias=-0.1):
    return poly(c, sh(pts, 0, b), hair, bias=bias, hl=hair[0])


def angel_ring(c, hair, cx, cy, b, x0, x1, curve=3.0):
    for x in range(x0, x1 + 1):
        y = cy + b + (x // 4) % 2 + int(((x - cx) / 24) ** 2 * curve)
        for yy in (y, y + 1):
            if c.p.get((x, yy)) in hair[1:]: c.px(x, yy, hair[0])


# ---------------------------------------------------------------- rosto
def face_front(c, b, cx=64):
    S = set()
    for y in range(14, 64):
        if y < 38: hw = max(0.0, 24 ** 2 - (y + 0.5 - 38) ** 2) ** 0.5
        else:
            t = (y - 38) / 25; hw = 24 * max(0.0, 1 - t * t) ** 0.5 * (1 - 0.32 * t)
        for x in range(int(round(cx - hw)), int(round(cx + hw)) + 1): S.add((x, y + b))
    for (x, y) in S:
        dx = (x - cx) / 24; yy = y - b
        v = 0.42 if dx < 0.6 else 0.7
        if dx < -0.45 and 44 < yy < 56: v = 0.1
        if (x + 1, y) not in S or (x, y + 1) not in S: v = 1.0
        c.px(x, y, tone(SKIN, v, x, y))


def face_side(c, b, hx=0):
    S = set(); cx = 66 + hx
    for y in range(15, 64):
        if y < 38:
            hw = max(0.0, 23 ** 2 - (y + 0.5 - 38) ** 2) ** 0.5; xl, xr = cx - hw, cx + hw
        else:
            t = (y - 38) / 25
            xl = cx - 23 * max(0.0, 1 - t * t) ** 0.5 * (1 - 0.2 * t); xr = cx + 23 * (1 - 0.48 * t)
        for x in range(int(round(xl)), int(round(xr)) + 1): S.add((x, y + b))
    for i, w in enumerate((1, 2, 2, 1)):
        for x in range(w): S.add((int(cx + 20 - 1 * i) + x + 1, 46 + i + b))
    for (x, y) in S:
        v = 0.42 if x < cx + 6 else 0.3
        if (x + 1, y) not in S or (x, y + 1) not in S: v = 1.0
        c.px(x, y, tone(SKIN, v, x, y))


def anime_eye(c, x, y, eye, outer="left", w=9):
    """Olho anime: cílio grosso com 'risquinho' no canto externo, íris em degradê, dois brilhos e um pouco de branco."""
    lt, md, dk = eye
    flat(c, x - 1, y, x + w, y + 1, "ol")
    if outer == "left": c.px(x - 2, y + 1, "ol"); c.px(x - 3, y + 2, "ol"); c.px(x - 2, y + 2, "ol")
    else: c.px(x + w + 1, y + 1, "ol"); c.px(x + w + 2, y + 2, "ol"); c.px(x + w + 1, y + 2, "ol")
    ix0, ix1 = (x + 1, x + w - 2) if outer == "left" else (x + 1, x + w - 2)
    for yy in range(y + 2, y + 11):
        for xx in range(ix0, ix1 + 1):
            if yy == y + 10 and xx in (ix0, ix1): continue
            c.px(xx, yy, dk if yy < y + 5 else md if yy < y + 8 else lt)
    inner = x + w - 1 if outer == "left" else x
    flat(c, inner, y + 4, inner, y + 9, "wh")
    cxp = (ix0 + ix1) // 2
    flat(c, cxp - 1, y + 4, cxp + 1, y + 7, "ol")
    flat(c, ix0 + 1, y + 3, ix0 + 2, y + 5, "wh"); c.px(ix1 - 1, y + 8, "wh")
    flat(c, x + 2, y + 11, x + w - 3, y + 11, "skd")


def eye_side(c, x, y, eye):
    lt, md, dk = eye
    flat(c, x - 1, y, x + 6, y + 1, "ol"); c.px(x + 7, y + 2, "ol")
    for yy in range(y + 2, y + 11):
        for xx in range(x, x + 5):
            if yy == y + 10 and xx in (x, x + 4): continue
            c.px(xx, yy, dk if yy < y + 5 else md if yy < y + 8 else lt)
    flat(c, x + 1, y + 4, x + 2, y + 7, "ol"); flat(c, x, y + 3, x + 1, y + 4, "wh"); c.px(x + 3, y + 8, "wh")
    flat(c, x + 1, y + 11, x + 4, y + 11, "skd")


def closed_eye(c, x, y, w=9, happy=True):
    for i in range(w):
        dy = -abs(i - w // 2) // 2 if happy else 0
        c.px(x + i, y + 7 + dy, "ol")


def hurt_eye(c, x, y):
    for i in range(5): c.px(x + i, y + 3 + i // 2, "ol"); c.px(x + i, y + 9 - i // 2, "ol")


def blush(c, x, y):
    for i in range(3): c.px(x + i * 3, y + 1, "r2"); c.px(x + i * 3 + 1, y, "r2")


def mouth(c, kind, x, y):
    if kind == "smile":
        c.px(x, y, "skd"); flat(c, x + 1, y + 1, x + 3, y + 1, "skd"); c.px(x + 4, y, "skd")
    elif kind == "open":
        flat(c, x, y, x + 4, y, "rd"); flat(c, x + 1, y + 1, x + 3, y + 2, "rd"); flat(c, x + 1, y + 2, x + 3, y + 2, "r1")
    elif kind == "ouch":
        flat(c, x, y, x + 4, y + 3, "rd"); flat(c, x + 1, y + 2, x + 3, y + 3, "r1")
    else:
        flat(c, x, y + 1, x + 3, y + 1, "skd")


# ---------------------------------------------------------------- cabelo por estilo (frente)
BANGS = {
    "ponytail": [[(36, 24), (50, 20), (42, 50)], [(45, 20), (58, 20), (51, 46)], [(53, 20), (66, 20), (60, 48)],
                 [(61, 20), (74, 20), (69, 44)], [(69, 20), (82, 20), (77, 48)], [(77, 20), (92, 24), (87, 50)]],
    "spiky": [[(36, 24), (52, 20), (38, 50)], [(48, 20), (62, 20), (55, 47)], [(58, 20), (72, 20), (71, 46)],
              [(68, 20), (84, 22), (88, 48)]],
    "long": [[(36, 22), (48, 20), (40, 46)], [(44, 20), (56, 20), (50, 44)], [(52, 20), (64, 20), (58, 44)],
             [(60, 20), (72, 20), (66, 44)], [(68, 20), (80, 20), (76, 44)], [(76, 20), (92, 22), (88, 46)]],
    "pigtails": [[(36, 24), (50, 20), (44, 46)], [(46, 20), (60, 20), (54, 44)], [(56, 20), (70, 20), (66, 46)],
                 [(66, 20), (80, 20), (76, 44)], [(76, 20), (92, 24), (86, 48)]],
    "short": [[(36, 26), (52, 20), (44, 42)], [(48, 20), (64, 20), (58, 40)], [(60, 20), (76, 20), (72, 42)],
              [(72, 20), (92, 26), (86, 44)]],
    "bun": [[(36, 26), (54, 20), (40, 48)], [(50, 20), (66, 20), (58, 40)], [(62, 20), (80, 20), (76, 42)],
            [(76, 20), (92, 26), (88, 46)]],
}
SIDELOCK = [(35, 28), (46, 28), (47, 50), (41, 66), (35, 54)]


def hair_back_layer(c, cfg, b, view):
    """Partes do cabelo que ficam atrás do rosto/corpo."""
    hair = cfg["hair"]; st = cfg["style"]
    if view == "front":
        if st == "ponytail":
            lock(c, hair, [(78, 12), (96, 18), (104, 44), (98, 74), (92, 54), (86, 30)], b, bias=0.2)
        if st == "long":
            for x0 in range(34, 92, 9):
                lock(c, hair, [(x0, 30), (x0 + 11, 30), (x0 + 10, 96), (x0 + 5, 102), (x0, 96)], b, bias=0.25)
        if st == "pigtails":
            for m in (False, True):
                lock(c, hair, sh([(36, 30), (30, 32), (22, 50), (24, 72), (30, 84), (32, 64), (38, 44)], mirror=m), b)
    if view == "side":
        if st == "ponytail":
            lock(c, hair, [(52, 14), (40, 18), (28, 34), (24, 60), (30, 82), (36, 62), (42, 38), (54, 26)], b)
        if st == "long":
            for x0 in range(34, 50, 8):
                lock(c, hair, [(x0, 30), (x0 + 10, 30), (x0 + 9, 96), (x0 + 4, 102), (x0, 96)], b, bias=0.1)
        if st == "pigtails":
            lock(c, hair, [(46, 30), (38, 32), (30, 50), (32, 72), (38, 84), (40, 64), (46, 44)], b)


def hair_front(c, cfg, b):
    hair = cfg["hair"]; st = cfg["style"]
    ell(c, 64, 32 + b, 28, 24, hair, bias=-0.05, cut=34 + b)
    if st == "spiky":
        for pts in ([(36, 30), (46, 16), (24, 12)], [(42, 20), (56, 12), (44, 0)], [(54, 14), (70, 12), (64, -2)],
                    [(66, 12), (80, 16), (84, 0)], [(76, 16), (92, 28), (104, 12)]):
            lock(c, hair, pts, b)
    for pts in BANGS[st]: lock(c, hair, pts, b)
    if st in ("ponytail", "long", "pigtails", "spiky", "bun"):
        for m in (False, True):
            pts = SIDELOCK if st != "long" else [(34, 28), (45, 28), (46, 52), (44, 80), (38, 86), (34, 70)]
            if st == "spiky": pts = [(36, 28), (46, 28), (46, 46), (40, 58), (36, 48)]
            lock(c, hair, sh(pts, mirror=m), b, bias=0.05 if m else -0.15)
    angel_ring(c, hair, 64, 25, b, 42, 82)
    if st == "ponytail":
        poly(c, sh([(80, 10), (90, 4), (92, 16)], 0, b), ("r2", "r1", "r0")); poly(c, sh([(94, 16), (100, 6), (102, 20)], 0, b), ("r2", "r1", "r0"))
        ell(c, 91, 13 + b, 3, 3, ("r1", "r0", "r0"))
    if st == "long":
        for dx, dy in ((0, -3), (3, 0), (0, 3), (-3, 0)): ell(c, 42 + dx, 24 + dy + b, 2.5, 2.5, ("wh", "m2", "m1"))
        c.px(42, 24 + b, "au")
    if st == "pigtails":
        for x in (34, 94): ell(c, x, 32 + b, 4, 4, ("m2", "m1", "m0"))
    if st == "bun":
        ell(c, 64, 8 + b, 11, 9, hair, bias=-0.1); angel_ring(c, hair, 64, 4, b, 56, 70, curve=1)
        flat(c, 70, 0 + b, 72, 14 + b, "r1"); flat(c, 70, 0 + b, 72, 1 + b, "au")


def hair_back_view(c, cfg, b):
    hair = cfg["hair"]; st = cfg["style"]
    if st == "long":
        for x0 in range(34, 92, 9):
            lock(c, hair, [(x0, 30), (x0 + 11, 30), (x0 + 10, 96), (x0 + 5, 102), (x0, 96)], b)
    ell(c, 64, 34 + b, 29, 26, hair, bias=-0.05)
    for x0 in range(36, 88, 10):
        lock(c, hair, [(x0, 40), (x0 + 12, 40), (x0 + 6, 66)], b)
    angel_ring(c, hair, 64, 22, b, 42, 84)
    if st == "spiky":
        for pts in ([(36, 30), (46, 16), (24, 12)], [(42, 20), (56, 12), (44, 0)], [(54, 14), (70, 12), (64, -2)],
                    [(66, 12), (80, 16), (84, 0)], [(76, 16), (92, 28), (104, 12)]):
            lock(c, hair, pts, b)
    if st == "ponytail":
        lock(c, hair, [(56, 20), (72, 20), (74, 60), (68, 90), (62, 96), (56, 70)], b)
        poly(c, sh([(52, 16), (62, 20), (54, 26)], 0, b), ("r2", "r1", "r0")); poly(c, sh([(76, 16), (66, 20), (74, 26)], 0, b), ("r2", "r1", "r0"))
        ell(c, 64, 21 + b, 3, 3, ("r1", "r0", "r0"))
    if st == "pigtails":
        for m in (False, True):
            lock(c, hair, sh([(36, 30), (30, 32), (22, 50), (24, 72), (30, 84), (32, 64), (38, 44)], mirror=m), b)
            ell(c, 34 if not m else 94, 32 + b, 4, 4, ("m2", "m1", "m0"))
    if st == "bun": ell(c, 64, 10 + b, 11, 9, hair); flat(c, 56, 4 + b, 58, 18 + b, "r1")


def hair_side(c, cfg, b, hx=0):
    hair = cfg["hair"]; st = cfg["style"]
    ell(c, 62 + hx, 32 + b, 28, 23, hair, bias=-0.05, cut=36 + b)
    ell(c, 52 + hx, 44 + b, 16, 19, hair, bias=0.1)
    for pts in ([(40, 44), (52, 44), (44, 68)], [(48, 46), (60, 46), (56, 70)]):
        lock(c, hair, sh(pts, hx), b, bias=0.15)
    if st == "spiky":
        for pts in ([(40, 30), (50, 20), (20, 16)], [(44, 20), (58, 12), (38, 0)], [(56, 14), (70, 12), (66, -2)], [(68, 14), (80, 18), (88, 4)]):
            lock(c, hair, sh(pts, hx), b)
    for pts in ([(66, 20), (80, 20), (86, 46)], [(76, 20), (90, 26), (92, 42)], [(58, 20), (70, 20), (72, 40)]):
        lock(c, hair, sh(pts, hx), b)
    lock(c, hair, sh([(55, 34), (64, 34), (65, 58), (59, 66), (55, 54)], hx), b)
    angel_ring(c, hair, 62 + hx, 25, b, 40 + hx, 80 + hx)
    if st == "ponytail":
        poly(c, sh([(50, 12), (40, 6), (42, 18)], hx, b), ("r2", "r1", "r0")); ell(c, 49 + hx, 15 + b, 3, 3, ("r1", "r0", "r0"))
    if st == "long":
        for dx, dy in ((0, -3), (3, 0), (0, 3), (-3, 0)): ell(c, 72 + hx + dx, 22 + dy + b, 2.5, 2.5, ("wh", "m2", "m1"))
    if st == "pigtails": ell(c, 46 + hx, 32 + b, 4, 4, ("m2", "m1", "m0"))
    if st == "bun": ell(c, 50 + hx, 12 + b, 11, 9, hair); flat(c, 44 + hx, 2 + b, 46 + hx, 16 + b, "r1")


def headwear(c, cfg, b, view, hx=0):
    ex = cfg.get("extra")
    if ex == "helmet":
        cx = 64 if view != "side" else 63 + hx
        ell(c, cx, 28 + b, 31, 22, ("s3", "s2", "s1"), cut=30 + b)
        flat(c, cx - 31, 27 + b, cx + 31, 31 + b, "au0"); flat(c, cx - 31, 27 + b, cx + 31, 27 + b, "au")
        ell(c, cx - 10, 16 + b, 7, 3, ("wh", "s3", "s3"), edge=False)
        if view == "front": poly(c, sh([(60, 6), (68, 6), (64, -4)], 0, b), ("r2", "r1", "r0"))
    if ex == "hat":
        cx = 64 if view != "side" else 66 + hx
        ell(c, cx, 30 + b, 42, 8, ("au2", "au", "au0"))
        ell(c, cx - (0 if view != "side" else 2), 20 + b, 22, 15, ("au2", "au", "au0"), cut=28 + b)
        flat(c, cx - 22, 24 + b, cx + 21, 27 + b, "r1"); flat(c, cx - 22, 27 + b, cx + 21, 27 + b, "r0")
        for x in range(cx - 40, cx + 41, 5): c.px(x, 31 + b, "au0")


# ---------------------------------------------------------------- cabeça completa
def head(c, cfg, b, view, hx=0, eyes="open"):
    ex = cfg.get("extra")
    if view == "back":
        flat(c, 60, 56 + b, 67, 66 + b, "sk0")
        hair_back_view(c, cfg, b); headwear(c, cfg, b, "back")
        return
    if not (view == "front" and cfg["style"] == "long"):  # cabelo longo de frente já foi desenhado atrás do corpo
        hair_back_layer(c, cfg, b, view)
    if view == "front":
        rect(c, 60, 56 + b, 67, 66 + b, ("sk", "sk0", "sk0"))
        for x in (40, 88): ell(c, x, 47 + b, 3.2, 5, SKIN)
        face_front(c, b)
        bald = ex == "beard"
        if eyes == "open" and not bald:
            anime_eye(c, 47, 40 + b, cfg["eye"], "left"); anime_eye(c, 72, 40 + b, cfg["eye"], "right")
            flat(c, 48, 35 + b, 55, 35 + b, cfg["hair"][2]); flat(c, 73, 35 + b, 80, 35 + b, cfg["hair"][2])
        elif eyes == "hurt":
            hurt_eye(c, 50, 41 + b); hurt_eye(c, 74, 41 + b)
        else:
            closed_eye(c, 47, 40 + b); closed_eye(c, 72, 40 + b)
        c.px(65, 53 + b, "sk0")
        mouth(c, "ouch" if eyes == "hurt" else cfg.get("mouth", "smile"), 62, 57 + b)
        blush(c, 45, 53 + b); blush(c, 75, 53 + b)
        if bald:
            ell(c, 64, 30 + b, 25, 18, ("sk2", "sk", "sk0"), cut=34 + b)
            for x0 in (36, 80): ell(c, x0 + 6, 42 + b, 8, 11, cfg["hair"])
            for m in (False, True): poly(c, sh([(44, 36), (58, 34), (58, 40), (46, 42)], mirror=m, dy=b), WHITE)
            poly(c, sh([(44, 54), (84, 54), (80, 76), (70, 92), (64, 98), (58, 92), (48, 76)], 0, b), WHITE, axis="y")
            for m in (False, True): poly(c, sh([(50, 54), (64, 52), (64, 58), (52, 60)], mirror=m, dy=b), ("s3", "s2", "s2"))
            flat(c, 61, 58 + b, 66, 59 + b, "s2")
        else:
            hair_front(c, cfg, b)
        headwear(c, cfg, b, "front")
    else:  # lateral, olhando para a direita
        rect(c, 62 + hx, 56 + b, 70 + hx, 66 + b, ("sk", "sk0", "sk0"))
        face_side(c, b, hx)
        ell(c, 59 + hx, 48 + b, 3.2, 5, SKIN)
        if ex == "beard":
            closed_eye(c, 76 + hx, 40 + b, w=6)
            poly(c, sh([(62, 50), (86, 52), (84, 70), (74, 90), (66, 84), (62, 66)], hx, b), WHITE, axis="y")
            ell(c, 64 + hx, 30 + b, 24, 18, ("sk2", "sk", "sk0"), cut=34 + b); ell(c, 54 + hx, 42 + b, 10, 12, cfg["hair"])
            poly(c, sh([(74, 34), (86, 34), (86, 40), (76, 42)], hx, b), WHITE)
        else:
            if eyes == "open": eye_side(c, 77 + hx, 40 + b, cfg["eye"]); flat(c, 77 + hx, 35 + b, 83 + hx, 35 + b, cfg["hair"][2])
            elif eyes == "hurt": hurt_eye(c, 77 + hx, 41 + b)
            else: closed_eye(c, 76 + hx, 40 + b, w=6)
            mouth(c, "ouch" if eyes == "hurt" else "flat", 81 + hx, 56 + b)
            blush(c, 74 + hx, 53 + b)
            hair_side(c, cfg, b, hx)
        headwear(c, cfg, b, "side", hx)


# ---------------------------------------------------------------- corpo e roupas
def legs_front(c, cfg, step):
    for i, lx in enumerate((55, 66)):
        lifted = (step == 1 and i == 0) or (step == 2 and i == 1)
        bot = 116 - (3 if lifted else 0)
        rect(c, lx, 92, lx + 6, bot - 10, cfg.get("legs", PANTS))
        rect(c, lx - 1, bot - 11, lx + 7, bot, BOOTS, axis="y")
        flat(c, lx - 1, bot - 11, lx + 7, bot - 10, "d2"); c.px(lx + 2, bot - 6, "d2")


def arms_front(c, cfg, b, step):
    sl = cfg["sleeve"]; gl = cfg.get("gloves", GLOVES)
    sw = {0: (0, 0), 1: (-3, 3), 2: (3, -3)}[step]
    for ax, dy, bias in ((46, sw[0], -0.15), (77, sw[1], 0.2)):
        rect(c, ax, 66 + b + dy, ax + 5, 80 + b + dy, sl, bias=bias)
        flat(c, ax, 79 + b + dy, ax + 5, 80 + b + dy, sl[0])
        rect(c, ax, 81 + b + dy, ax + 5, 88 + b + dy, gl, bias=bias)
        ell(c, ax + 2.5, 90 + b + dy, 3.6, 3.2, gl, bias=bias)


TORSO_F = [(52, 65), (76, 65), (77, 84), (74, 92), (54, 92), (51, 84)]
TORSO_S = [(56, 65), (73, 65), (75, 84), (73, 92), (57, 92), (55, 84)]


def outfit_front(c, cfg, b, back):
    o = cfg["outfit"]; main = cfg["coat"]
    if o in ("robe", "dress"):
        bot = 110 if o == "robe" else 100
        poly(c, sh([(52, 65), (76, 65), (78, 84), (84, bot), (44, bot), (50, 84)], 0, b), main)
        for fx in (54, 64, 74): flat(c, fx, 88 + b, fx, bot - 1 + b, main[2])
        flat(c, 45, bot - 2 + b, 83, bot - 1 + b, cfg.get("trim", "au"))
    else:
        poly(c, sh(TORSO_F, 0, b), main)
    if o == "jacket":
        if not back:
            poly(c, sh([(60, 65), (68, 65), (67, 84), (61, 84)], 0, b), WHITE)
            for m in (False, True): poly(c, sh([(55, 64), (62, 64), (61, 74)], mirror=m, dy=b), ("r2", "r2", "r1"))
        poly(c, sh([(51, 84), (77, 84), (82, 99), (46, 99)], 0, b), main)
        for x0, x1 in ((54, 51), (64, 64), (73, 77)): flat(c, x0, 88 + b, x0, 98 + b, main[2])
    if o == "tunic":
        poly(c, sh([(51, 84), (77, 84), (79, 96), (49, 96)], 0, b), main)
        flat(c, 64, 86 + b, 64, 96 + b, main[2])
        if not back:
            flat(c, 61, 66 + b, 66, 68 + b, "sk0")
    if o in ("jacket", "tunic", "dress"):
        y = (84 if o != "dress" else 80) + b
        flat(c, 51, y, 77, y + 2, "d0")
        for x in range(52, 77, 3): c.px(x, y + 1, "d1")
        if not back:
            rect(c, 61, y - 1, 67, y + 3, ("au2", "au", "au0")); c.px(62, y, "wh")
    if cfg.get("capelet"):
        poly(c, sh([(49, 63), (79, 63), (82, 75), (46, 75)], 0, b), WHITE, axis="y")
        flat(c, 46, 74 + b, 82, 75 + b, "au")
        if not back: ell(c, 64, 66 + b, 3, 3, ("au2", "au", "au0"))
    if cfg.get("scarf"):
        poly(c, sh([(53, 60), (75, 60), (76, 68), (52, 68)], 0, b), cfg["scarf"], axis="y")
        poly(c, sh([(70, 66), (77, 66), (80, 84), (73, 86)], 0, b), cfg["scarf"])
    if cfg.get("pauldron"):
        ell(c, 50, 67 + b, 6, 4.5, ("s3", "s2", "s1")); flat(c, 45, 69 + b, 55, 69 + b, "s1")
    if cfg.get("apron") and not back:
        poly(c, sh([(55, 70), (73, 70), (75, 102), (53, 102)], 0, b), WHITE, axis="y")
        flat(c, 52, 76 + b, 76, 77 + b, "s2")
    if cfg.get("plate") and not back:
        poly(c, sh([(54, 66), (74, 66), (73, 82), (64, 86), (55, 82)], 0, b), ("s3", "s2", "s1"))
        ell(c, 59, 71 + b, 3, 2, ("wh", "s3", "s3"), edge=False)


def outfit_side(c, cfg, b, lean=0):
    o = cfg["outfit"]; main = cfg["coat"]; L = lean
    if o in ("robe", "dress"):
        bot = 110 if o == "robe" else 100
        poly(c, sh([(56, 65), (73, 65), (76, 84), (80, bot), (50, bot), (54, 84)], L, b), main)
        flat(c, 51 + L, bot - 2 + b, 79 + L, bot - 1 + b, cfg.get("trim", "au"))
    else:
        poly(c, sh(TORSO_S, L, b), main, bias=-0.1)
    if o == "jacket":
        poly(c, sh([(55, 84), (74, 84), (79, 99), (51, 99)], L, b), main)
        poly(c, sh([(69, 65), (73, 65), (74, 84), (70, 84)], L, b), WHITE)
    if o == "tunic":
        poly(c, sh([(55, 84), (75, 84), (77, 96), (53, 96)], L, b), main)
    if o in ("jacket", "tunic", "dress"):
        y = (84 if o != "dress" else 80) + b
        flat(c, 55 + L, y, 74 + L, y + 2, "d0")
        rect(c, 70 + L, y - 1, 74 + L, y + 3, ("au2", "au", "au0"))
    if cfg.get("capelet"):
        poly(c, sh([(53, 63), (75, 63), (79, 75), (51, 75)], L, b), WHITE, axis="y"); flat(c, 51 + L, 74 + b, 79 + L, 75 + b, "au")
    if cfg.get("scarf"):
        poly(c, sh([(57, 60), (74, 60), (75, 68), (56, 68)], L, b), cfg["scarf"], axis="y")
        poly(c, sh([(58, 64), (52, 64), (36, 76), (42, 80)], L, b), cfg["scarf"])
    if cfg.get("apron"): poly(c, sh([(64, 70), (75, 70), (78, 102), (66, 102)], L, b), WHITE, axis="y")
    if cfg.get("plate"): poly(c, sh([(60, 66), (74, 66), (75, 84), (62, 84)], L, b), ("s3", "s2", "s1"))
    if cfg.get("pauldron"): ell(c, 63 + L, 67 + b, 5.5, 4.5, ("s3", "s2", "s1"))


def legs_side(c, cfg, step):
    legs = cfg.get("legs", PANTS); dark = ("p0", "p0", "pd")
    if step == 0:
        rect(c, 60, 92, 67, 104, legs); rect(c, 58, 104, 72, 116, BOOTS, axis="y"); flat(c, 58, 104, 70, 104, "d2")
        return
    fc, bc = (legs, dark) if step == 1 else (dark, legs)
    rect(c, 50, 92, 56, 102, bc); rect(c, 46, 103, 58, 114, BOOTS, axis="y")
    rect(c, 70, 92, 76, 102, fc); rect(c, 70, 103, 84, 114, BOOTS, axis="y"); flat(c, 70, 103, 82, 103, "d2")


def arm_side(c, cfg, b, x, bias=0.1):
    sl = cfg["sleeve"]; gl = cfg.get("gloves", GLOVES)
    rect(c, x, 66 + b, x + 5, 80 + b, sl, bias=bias); rect(c, x, 81 + b, x + 5, 88 + b, gl, bias=bias)
    ell(c, x + 2.5, 90 + b, 3.6, 3.2, gl, bias=bias)


# ---------------------------------------------------------------- quadros
def front(cfg, step, back=False):
    c = Canvas(128, 128); b = -2 if step else 0
    if not back and cfg["style"] == "long": hair_back_layer(c, cfg, b, "front")
    legs_front(c, cfg, step)
    outfit_front(c, cfg, b, back)
    arms_front(c, cfg, b, step)
    head(c, cfg, b, "back" if back else "front")
    finish(c); c.shadow_ellipse(64, 118, 22, 5)
    return c


def side(cfg, step):
    c = Canvas(128, 128); b = -2 if step else 0
    legs_side(c, cfg, step)
    outfit_side(c, cfg, b)
    head(c, cfg, b, "side")
    arm_side(c, cfg, b, {0: 61, 1: 56, 2: 66}[step])
    finish(c); c.shadow_ellipse(64, 118, 22, 5)
    return c


def pose_attack(cfg):
    c = Canvas(128, 128); sl = cfg["sleeve"]; gl = cfg.get("gloves", GLOVES)
    legs_side(c, cfg, 1)
    rect(c, 48, 68, 53, 80, sl, bias=0.3); rect(c, 48, 81, 53, 86, gl)
    outfit_side(c, cfg, 0, lean=2)
    head(c, cfg, 0, "side", hx=4)
    rect(c, 74, 67, 88, 72, sl, axis="y"); rect(c, 89, 66, 94, 73, gl, axis="y")
    rect(c, 95, 60, 98, 79, ("au2", "au", "au0")); flat(c, 93, 60, 100, 61, "au")
    for i in range(27):
        x, y = 99 + i, 66 - i
        c.px(x, y - 1, "wh"); c.px(x, y, "s3"); c.px(x, y + 1, "s3"); c.px(x, y + 2, "s2"); c.px(x + 1, y + 2, "s1")
    star(c, 124, 40, "w3", 3)
    finish(c); c.shadow_ellipse(64, 118, 25, 5)
    return c


def pose_cast(cfg):
    c = Canvas(128, 128); sl = cfg["sleeve"]; gl = cfg.get("gloves", GLOVES)
    legs_side(c, cfg, 0)
    rect(c, 56, 46, 61, 64, sl, bias=0.3); ell(c, 58.5, 41, 4, 5, gl)
    outfit_side(c, cfg, 0)
    head(c, cfg, 0, "side", eyes="closed")
    rect(c, 74, 62, 84, 68, sl); rect(c, 88, 48, 93, 63, sl); ell(c, 91, 43, 4.5, 5, gl)
    for x, y, col, r in [(98, 26, "wh", 3), (90, 22, "w3", 2), (106, 34, "w3", 2), (108, 20, "au", 2), (56, 24, "au", 2), (96, 12, "w3", 3), (114, 30, "wh", 1)]:
        star(c, x, y, col, r)
    finish(c); c.shadow_ellipse(64, 118, 22, 5)
    return c


def pose_hurt(cfg):
    c = Canvas(128, 128); sl = cfg["sleeve"]; gl = cfg.get("gloves", GLOVES)
    legs_side(c, cfg, 0)
    rect(c, 44, 60, 49, 72, sl, bias=0.3); ell(c, 45, 56, 4, 4, gl)
    outfit_side(c, cfg, 2, lean=-4)
    head(c, cfg, 2, "side", hx=-8, eyes="hurt")
    rect(c, 70, 66, 75, 76, sl); rect(c, 74, 76, 79, 81, gl)
    for x, y in [(92, 22), (96, 30), (88, 34)]: star(c, x, y, "wh", 2)
    finish(c); c.shadow_ellipse(64, 118, 22, 5)
    return c


def pose_ko(cfg):
    c = Canvas(128, 128); main = cfg["coat"]; hair = cfg["hair"]
    rect(c, 10, 100, 24, 114, BOOTS); rect(c, 24, 101, 50, 112, cfg.get("legs", PANTS), axis="y")
    poly(c, [(48, 96), (84, 94), (86, 114), (46, 114)], main, axis="y")
    flat(c, 60, 95, 62, 114, "d0"); rect(c, 59, 101, 63, 105, ("au2", "au", "au0"))
    rect(c, 60, 114, 82, 118, cfg.get("gloves", GLOVES), axis="y")
    if cfg["style"] in ("long", "pigtails", "ponytail"): poly(c, [(96, 86), (124, 90), (124, 116), (98, 116)], hair, axis="y")
    ell(c, 100, 104, 16, 15, SKIN)
    ell(c, 108, 102, 15, 16, hair, bias=-0.05)
    for pts in ([(94, 90), (104, 88), (90, 100)], [(94, 102), (104, 104), (88, 112)]): poly(c, pts, hair, hl=hair[0])
    for y in (98, 108): flat(c, 88, y, 92, y, "ol")
    if cfg.get("extra") == "hat": ell(c, 118, 98, 7, 22, ("au2", "au", "au0"))
    if cfg.get("extra") == "helmet": ell(c, 112, 102, 13, 18, ("s3", "s2", "s1"))
    finish(c); c.shadow_ellipse(66, 119, 48, 5)
    return c


# ---------------------------------------------------------------- elenco
CHARS = [
    dict(hair=("h2", "h1", "h0"), eye=("w3", "w2", "w0"), style="ponytail", outfit="jacket",
         coat=("r2", "r1", "r0"), sleeve=("r2", "r1", "r0"), mouth="smile"),
    dict(hair=("k2", "k1", "k0"), eye=("au2", "au0", "d0"), style="spiky", outfit="tunic",
         coat=("t2", "t1", "t0"), sleeve=("t2", "t1", "t0"), scarf=("au2", "au", "au0"), pauldron=True, mouth="flat"),
    dict(hair=("au2", "au", "au0"), eye=("g3", "g2", "g0"), style="long", outfit="dress",
         coat=("g3", "g2", "g1"), sleeve=("g3", "g2", "g1"), capelet=True, gloves=WHITE, mouth="open"),
]
NPCS = [
    dict(hair=("k2", "k1", "k0"), eye=("s3", "s1", "s0"), style="short", extra="helmet", outfit="tunic",
         coat=("s2", "s1", "s0"), sleeve=("s2", "s1", "s0"), plate=True, mouth="flat"),
    dict(hair=("wh", "s3", "s2"), eye=("d1", "d0", "ol"), style="short", extra="beard", outfit="robe",
         coat=("v2", "v1", "v0"), sleeve=("v2", "v1", "v0"), gloves=SKIN, trim="wh"),
    dict(hair=("o2", "o1", "o0"), eye=("g3", "g2", "g0"), style="pigtails", outfit="dress",
         coat=("m2", "m1", "m0"), sleeve=("m2", "m1", "m0"), gloves=SKIN, trim="wh", mouth="open"),
    dict(hair=("h2", "h1", "h0"), eye=("d2", "d1", "d0"), style="short", extra="hat", outfit="tunic",
         coat=("d2", "d1", "d0"), sleeve=SKIN, gloves=SKIN, mouth="smile"),
    dict(hair=("k2", "k1", "k0"), eye=("v2", "v1", "v0"), style="bun", outfit="tunic",
         coat=("au2", "au", "au0"), sleeve=("au2", "au", "au0"), gloves=SKIN, apron=True, mouth="smile"),
]


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
    print("ok -> herois_128.png, npcs_128.png, slimes_128.png (estilo anime)")


if __name__ == "__main__":
    main()
