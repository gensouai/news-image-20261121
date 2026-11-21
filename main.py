#!/usr/bin/env python3
"""Sum up 21 November 2026's world news in one image.

A pure-stdlib Python program that draws a newspaper front page for
Saturday 21 November 2026 and writes it to /output/entry.png
(falling back to ./output/entry.png). No network, fully deterministic.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 241, 226)
PAPER_DARK = (238, 229, 205)
INK = (26, 24, 22)
INK_SOFT = (74, 68, 60)
RED = (178, 34, 34)
BLUE = (30, 74, 140)
GREEN = (24, 92, 62)
GOLD = (212, 160, 32)
CHALK = (238, 244, 238)
BOARD = (26, 66, 50)
SKY = (168, 205, 232)
GREY = (120, 116, 110)
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def frame(self, x, y, w, h, c, t=2):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        r = t // 2
        while True:
            for yy in range(y - r, y - r + t):
                for xx in range(x - r, x - r + t):
                    self.set(xx, yy, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, rad, c):
        for yy in range(cy - rad, cy + rad + 1):
            for xx in range(cx - rad, cx + rad + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= rad * rad:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, rad, c, t=2):
        for yy in range(cy - rad - t, cy + rad + t + 1):
            for xx in range(cx - rad - t, cx + rad + t + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (rad - t) ** 2 < d2 <= rad * rad:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            nodes = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    nodes.append(x0 + (yy - y0) * (x1 - x0) // (y1 - y0))
            nodes.sort()
            for i in range(0, len(nodes) - 1, 2):
                for xx in range(nodes[i], nodes[i + 1] + 1):
                    self.set(xx, yy, c)


def save_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- font
# Hand-drawn 5x7 bitmap font. Each glyph is 7 rows of 5 pixels.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": (".##..", ".##..", "..#..", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#.##", "#..##"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "\u2022": (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
}


# ---------------------------------------------------------------- text
def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color):
    cx = x
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == "#":
                    cv.rect(cx + col * scale, y + row * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def draw_centered(cv, cx, y, s, scale, color):
    return draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def draw_right(cv, rx, y, s, scale, color):
    return draw_text(cv, rx - text_w(s, scale), y, s, scale, color)


def wrap(s, max_chars):
    lines = []
    cur = ""
    for word in s.split():
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, s, scale, color, max_chars, leading):
    for ln in wrap(s, max_chars):
        draw_text(cv, x, y, ln, scale, color)
        y += 7 * scale + leading
    return y


# ---------------------------------------------------------------- layout
MARGIN = 28
CW = W - 2 * MARGIN  # 968 content width


def masthead(cv):
    cv.rect(MARGIN, 26, CW, 3, INK)
    draw_centered(cv, W // 2, 44, "THE DAILY WORLD", 10, INK)
    cv.rect(MARGIN, 128, CW, 2, INK)
    draw_text(cv, MARGIN, 140, "SATURDAY, 21 NOVEMBER 2026", 2, INK)
    draw_centered(cv, W // 2, 140, "ONE IMAGE, ONE DAY", 2, INK_SOFT)
    draw_right(cv, W - MARGIN, 140, "LATE EDITION", 2, INK)
    cv.rect(MARGIN, 162, CW, 5, INK)


def panel(cv, x, y, w, h):
    cv.rect(x, y, w, h, PAPER_DARK)
    cv.frame(x, y, w, h, INK, 2)


def story_lead(cv):
    # Lead story: Riemann hypothesis proof (panel 28,182,968,288)
    draw_text(cv, 44, 196, "SCIENCE BREAKTHROUGH", 2, RED)
    cv.rect(44, 214, 180, 3, RED)
    draw_text(cv, 44, 226, "AI PROVES MATH'S OLDEST RIDDLE", 5, INK)
    draw_block(cv, 44, 292,
               "ANTHROPIC RESEARCHER LEVENT ALPOGE, WORKING WITH THE AI "
               "CLAUDE, ANNOUNCES A PROOF OF THE RIEMANN HYPOTHESIS, "
               "MATH'S FAMOUS UNSOLVED PROBLEM SINCE 1859. INDEPENDENT "
               "EXPERTS COMPILE THE COMPUTER-CHECKED PROOF AND CALL IT "
               "ALMOST CERTAINLY TRUE.",
               2, INK, 43, 6)
    # chalkboard scene
    cv.rect(592, 278, 392, 180, (122, 84, 40))
    cv.rect(600, 286, 376, 164, BOARD)
    draw_text(cv, 616, 298, "PRIMES:", 2, CHALK)
    draw_text(cv, 616, 320, "2 3 5 7 11 13", 3, CHALK)
    draw_text(cv, 616, 350, "17 19 23 29", 3, CHALK)
    draw_text(cv, 616, 384, "UNSOLVED SINCE 1859", 2, CHALK)
    draw_text(cv, 616, 410, "167 YEARS", 2, CHALK)
    cv.line(872, 336, 908, 378, CHALK, 9)
    cv.line(908, 378, 962, 302, CHALK, 9)
    draw_text(cv, 836, 402, "PROVED!", 3, CHALK)


def story_markets(cv):
    # Markets rout (panel 28,486,476,252)
    cv.rect(44, 500, 444, 96, (16, 20, 38))
    pts = [(60, 516), (130, 528), (190, 522), (250, 545),
           (310, 540), (365, 566), (408, 578)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 4)
    cv.line(408, 578, 392, 574, RED, 4)
    cv.line(408, 578, 404, 562, RED, 4)
    cv.circle(452, 540, 19, GOLD)
    cv.ring(452, 540, 19, (150, 110, 20), 2)
    draw_text(cv, 445, 530, "B", 3, INK)
    draw_text(cv, 56, 570, "-3.7%", 2, (255, 120, 120))
    draw_text(cv, 44, 606, "MARKETS IN TURMOIL", 2, RED)
    draw_text(cv, 44, 624, "AI SELLOFF SINKS STOCKS", 3, INK)
    draw_block(cv, 44, 658,
               "S&P 500 FALLS 3.7% INTO CORRECTION AS NVIDIA DIVES 14%. "
               "BITCOIN BREAKS BELOW $60,000, HITTING A TWO-YEAR LOW "
               "NEAR $55,800.",
               2, INK, 37, 5)


def story_cop31(cv):
    # COP31 overtime (panel 520,486,476,252)
    cv.rect(536, 500, 444, 96, SKY)
    cv.circle(922, 526, 16, GOLD)
    cv.rect(536, 584, 444, 12, (90, 130, 80))
    cv.rect(560, 548, 130, 40, (105, 102, 98))
    cv.rect(578, 522, 18, 30, (80, 78, 74))
    cv.rect(614, 518, 18, 34, (80, 78, 74))
    cv.circle(584, 516, 7, (200, 200, 200))
    cv.circle(598, 511, 8, (210, 210, 210))
    cv.circle(620, 512, 8, (200, 200, 200))
    cv.circle(638, 510, 8, (215, 215, 215))
    cv.rect(756, 538, 128, 36, WHITE)
    cv.frame(756, 538, 128, 36, INK, 2)
    draw_text(cv, 774, 545, "COP31", 3, INK)
    draw_text(cv, 536, 606, "CLIMATE SUMMIT", 2, RED)
    draw_block(cv, 536, 624, "CLIMATE TALKS STUCK IN OVERTIME", 3, INK, 19, 4)
    draw_block(cv, 536, 682,
               "NEARLY 200 NATIONS IN ANTALYA MISS THE DEADLINE, "
               "FIGHTING OVER FOSSIL FUELS CUT FROM THE DRAFT DEAL.",
               2, INK, 37, 5)


def story_cancer(cv):
    # Pancreatic cancer pill (panel 28,754,476,196)
    cv.rect(44, 766, 444, 56, (226, 233, 238))
    # tumour circles shrinking left to right
    cv.circle(84, 794, 16, (150, 60, 60))
    cv.circle(128, 794, 11, (170, 80, 80))
    cv.circle(162, 794, 7, (190, 110, 110))
    cv.line(196, 794, 232, 794, INK, 3)
    cv.line(232, 794, 222, 786, INK, 3)
    cv.line(232, 794, 222, 802, INK, 3)
    # capsule pill
    cv.rect(252, 778, 118, 32, WHITE)
    cv.rect(252, 778, 59, 32, RED)
    cv.circle(252, 794, 16, RED)
    cv.circle(370, 794, 16, WHITE)
    cv.ring(370, 794, 16, INK, 2)
    cv.line(252, 778, 370, 778, INK, 2)
    cv.line(252, 810, 370, 810, INK, 2)
    # medical cross
    cv.rect(424, 776, 10, 36, GREEN)
    cv.rect(411, 789, 36, 10, GREEN)
    draw_block(cv, 44, 832, "PILL MAKES CANCER TUMOURS VANISH", 3, INK, 18, 4)
    draw_block(cv, 44, 890,
               "DAILY PILL DARAXONRASIB WITH CHEMO ERASED TUMOURS IN "
               "1 IN 12 PATIENTS WITH ADVANCED PANCREATIC CANCER.",
               2, INK, 37, 5)


def story_genz(cv):
    # Gen Z protests (panel 520,754,476,196)
    cv.rect(536, 766, 444, 56, (250, 226, 190))
    # placards
    cv.rect(700, 800, 4, 22, INK)
    cv.rect(664, 770, 76, 30, WHITE)
    cv.frame(664, 770, 76, 30, INK, 2)
    draw_text(cv, 672, 776, "NO CUTS", 1, INK)
    draw_text(cv, 676, 786, "TO SCHOOLS", 1, INK)
    cv.rect(884, 800, 4, 22, INK)
    cv.rect(848, 770, 76, 30, WHITE)
    cv.frame(848, 770, 76, 30, INK, 2)
    draw_text(cv, 862, 776, "GEN Z", 1, INK)
    draw_text(cv, 858, 786, "STRIKE", 1, INK)
    # crowd: heads and shoulders
    tones = [(198, 150, 110), (140, 95, 60), (232, 190, 150),
             (110, 75, 45), (205, 160, 120), (150, 105, 70)]
    for i, tone in enumerate(tones):
        cx = 566 + i * 68
        cv.circle(cx, 800, 10, tone)
        cv.rect(cx - 13, 810, 26, 12, (60 + i * 30 % 120, 70, 110))
    draw_block(cv, 536, 832, "GEN Z FLOODS EUROPE'S STREETS", 3, INK, 18, 4)
    draw_block(cv, 536, 890,
               "YOUTH STRIKE IN 25+ COUNTRIES OVER LIVING COSTS, "
               "SCHOOLS AND WAR SPENDING. 100 CITIES MARCH IN ITALY.",
               2, INK, 37, 5)


def build():
    cv = Canvas(W, H, PAPER)
    masthead(cv)
    # panel frames (scenes and text are added by the story functions)
    panel(cv, MARGIN, 182, CW, 288)                    # lead story
    panel(cv, MARGIN, 486, 476, 252)                   # markets
    panel(cv, 520, 486, 476, 252)                      # COP31
    panel(cv, MARGIN, 754, 476, 196)                   # cancer pill
    panel(cv, 520, 754, 476, 196)                      # gen z
    story_lead(cv)
    story_markets(cv)
    story_cop31(cv)
    story_cancer(cv)
    story_genz(cv)
    # footer
    cv.rect(MARGIN, 962, CW, 3, INK)
    draw_centered(cv, W // 2, 974,
                  "ALSO TODAY: FBI + USDA DATABASES HACKED \u2022 TRUMP FIRES CYBER CHIEF",
                  2, INK)
    return cv


def main():
    cv = build()
    out = "/output/entry.png"
    try:
        os.makedirs("/output", exist_ok=True)
    except OSError:
        out = os.path.join(".", "output", "entry.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
    save_png(cv, out)


if __name__ == "__main__":
    main()
