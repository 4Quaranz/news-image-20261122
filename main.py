#!/usr/bin/env python3
"""Draw a newspaper front page summing up 22 November 2026 world news.

Pure Python standard library only. Builds a 1024x1024 pixel buffer,
draws shapes and text with a hand-written 5x7 bitmap font, and encodes
the PNG by hand with zlib and struct. Deterministic: no chance
elements, no clock, no network, no files read.
"""
import binascii
import math
import os
import struct
import zlib

W = 1024
H = 1024
PAPER = (247, 243, 232)
INK = (18, 18, 18)
RED = (185, 28, 28)
DARK = (70, 70, 70)
WHITE = (255, 255, 255)
BLUE = (30, 64, 175)
LIGHT = (232, 226, 210)
GOLD = (180, 130, 30)

# 5x7 bitmap font. Each glyph is 7 rows of 5 characters, '#' = on.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    "-": ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    "\u2014": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
}

buf = bytearray(W * H * 3)
for _i in range(W * H):
    buf[_i * 3] = PAPER[0]
    buf[_i * 3 + 1] = PAPER[1]
    buf[_i * 3 + 2] = PAPER[2]


def px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        _o = (y * W + x) * 3
        buf[_o] = color[0]
        buf[_o + 1] = color[1]
        buf[_o + 2] = color[2]


def fill_rect(x, y, w, h, color):
    for _yy in range(y, y + h):
        for _xx in range(x, x + w):
            px(_xx, _yy, color)


def rect_outline(x, y, w, h, color, thick=2):
    fill_rect(x, y, w, thick, color)
    fill_rect(x, y + h - thick, w, thick, color)
    fill_rect(x, y, thick, h, color)
    fill_rect(x + w - thick, y, thick, h, color)


def line(x0, y0, x1, y1, color):
    _dx = abs(x1 - x0)
    _dy = -abs(y1 - y0)
    _sx = 1 if x0 < x1 else -1
    _sy = 1 if y0 < y1 else -1
    _err = _dx + _dy
    while True:
        px(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        _e2 = 2 * _err
        if _e2 >= _dy:
            _err += _dy
            x0 += _sx
        if _e2 <= _dx:
            _err += _dx
            y0 += _sy


def circle(cx, cy, r, color, filled=False):
    if filled:
        for _dy in range(-r, r + 1):
            _dx = int(math.sqrt(max(0, r * r - _dy * _dy)))
            for _xx in range(cx - _dx, cx + _dx + 1):
                px(_xx, cy + _dy, color)
    else:
        for _a in range(360):
            _rad = math.radians(_a)
            px(cx + int(r * math.cos(_rad)), cy + int(r * math.sin(_rad)), color)


def fill_polygon(points, color):
    _ys = [p[1] for p in points]
    for _y in range(min(_ys), max(_ys) + 1):
        _xs = []
        for _i in range(len(points)):
            _x1, _y1 = points[_i]
            _x2, _y2 = points[(_i + 1) % len(points)]
            if (_y1 <= _y < _y2) or (_y2 <= _y < _y1):
                _xs.append(_x1 + (_y - _y1) * (_x2 - _x1) / (_y2 - _y1))
        _xs.sort()
        for _k in range(0, len(_xs) - 1, 2):
            for _xx in range(int(_xs[_k]), int(_xs[_k + 1]) + 1):
                px(_xx, _y, color)


def star_points(cx, cy, r_out, r_in):
    _pts = []
    for _i in range(10):
        _r = r_out if _i % 2 == 0 else r_in
        _ang = math.radians(-90 + _i * 36)
        _pts.append((cx + int(_r * math.cos(_ang)), cy + int(_r * math.sin(_ang))))
    return _pts


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(x, y, text, scale, color):
    text = text.upper()
    _cx = x
    for _ch in text:
        _glyph = FONT.get(_ch, FONT[" "])
        for _row in range(7):
            for _col in range(5):
                if _glyph[_row][_col] == "1":
                    fill_rect(_cx + _col * scale, y + _row * scale, scale, scale, color)
        _cx += 6 * scale
    return _cx


def draw_text_center(x, y, w, text, scale, color):
    _tw = text_width(text, scale)
    draw_text(x + (w - _tw) // 2, y, text, scale, color)


def wrap(text, max_w, scale):
    _words = text.split(" ")
    _lines = []
    _cur = ""
    for _wd in _words:
        _try = (_cur + " " + _wd).strip()
        if text_width(_try, scale) <= max_w:
            _cur = _try
        else:
            if _cur:
                _lines.append(_cur)
            _cur = _wd
    if _cur:
        _lines.append(_cur)
    return _lines


def pictogram(kind, x, y, w, h):
    _cx = x + w // 2
    _cy = y + h // 2
    if kind == "gulf":
        fill_rect(x + 10, y + h - 26, w - 20, 3, BLUE)
        fill_rect(x + 10, y + h - 16, w - 20, 3, BLUE)
        _hull = [(x + 30, _cy + 10), (x + w - 30, _cy + 10),
                 (x + w - 55, _cy + 34), (x + 55, _cy + 34)]
        fill_polygon(_hull, INK)
        line(_cx - 10, _cy + 10, _cx - 10, _cy - 26, INK)
        line(_cx - 10, _cy - 26, _cx + 26, _cy - 12, RED)
        fill_polygon(star_points(x + w - 52, y + 26, 22, 9), RED)
        circle(x + w - 52, y + 26, 5, GOLD, filled=True)
    elif kind == "ukraine":
        _map = [(x + 30, y + 18), (x + w - 60, y + 10), (x + w - 24, y + 34),
                (x + w - 40, y + h - 18), (x + 70, y + h - 10), (x + 22, y + 52)]
        fill_polygon(_map, LIGHT)
        for _i in range(len(_map)):
            _a = _map[_i]
            _b = _map[(_i + 1) % len(_map)]
            line(_a[0], _a[1], _b[0], _b[1], INK)
        for _dx, _dy in [(-40, -8), (-10, 6), (18, -14), (40, 10)]:
            circle(_cx + _dx, _cy + _dy, 4, RED, filled=True)
        fill_polygon(star_points(_cx + 52, y + 22, 16, 7), RED)
    elif kind == "shenzhen":
        circle(_cx, _cy + 6, 42, INK)
        circle(_cx, _cy + 6, 38, LIGHT, filled=True)
        for _dx, _col in [(-52, RED), (0, BLUE), (52, GOLD)]:
            fill_rect(_cx + _dx - 12, y + 2, 24, 16, _col)
            line(_cx + _dx, y + 18, _cx + _dx, y + 30, INK)
        for _dx in [-52, 0, 52]:
            circle(_cx + _dx, _cy + 6, 9, INK, filled=True)
    elif kind == "mexico":
        fill_polygon(star_points(_cx - 34, _cy, 34, 14), GOLD)
        circle(_cx - 34, _cy, 10, RED, filled=True)
        circle(_cx + 34, _cy - 6, 13, INK)
        circle(_cx + 34, _cy - 6, 8, PAPER, filled=True)
        circle(_cx + 44, _cy + 16, 13, INK)
        circle(_cx + 44, _cy + 16, 8, PAPER, filled=True)
        line(_cx + 34, _cy - 6, _cx + 44, _cy + 16, INK)
    elif kind == "brazil":
        fill_rect(x + 24, y + 8, w - 48, h - 16, WHITE)
        rect_outline(x + 24, y + 8, w - 48, h - 16, INK, 3)
        fill_rect(_cx - 10, _cy - 26, 20, 52, RED)
        fill_rect(_cx - 26, _cy - 10, 52, 20, RED)
        fill_rect(x + 24, y + h - 22, w - 48, 4, RED)


def panel(x, y, w, h, kicker, headline, head_scale, summary, kind, date_tag):
    fill_rect(x, y, w, h, WHITE)
    rect_outline(x, y, w, h, INK, 3)
    fill_rect(x, y, w, 30, RED)
    draw_text(x + 12, y + 8, kicker, 2, WHITE)
    fill_rect(x + w - 112, y + 3, 100, 24, WHITE)
    draw_text_center(x + w - 112, y + 9, 100, date_tag, 2, RED)
    _lines = wrap(headline, w - 24, head_scale)
    _hy = y + 42
    for _ln in _lines:
        draw_text(x + 12, _hy, _ln, head_scale, INK)
        _hy += 7 * head_scale + 6
    _pic_y = _hy + 4
    _pic_h = 92 if w > 400 else 78
    pictogram(kind, x + 12, _pic_y, w - 24, _pic_h)
    _sy = _pic_y + _pic_h + 8
    for _ln in wrap(summary, w - 24, 2):
        draw_text(x + 12, _sy, _ln, 2, DARK)
        _sy += 18


def draw_page():
    draw_text_center(0, 28, W, "THE WORLD TODAY", 8, INK)
    fill_rect(24, 98, W - 48, 3, INK)
    draw_text_center(0, 110, W, "22 NOVEMBER 2026", 3, RED)
    draw_text_center(0, 136, W, "SUNDAY - WORLD NEWS IN ONE IMAGE", 2, DARK)
    fill_rect(24, 158, W - 48, 4, INK)
    panel(24, 172, 488, 296, "GULF ON EDGE",
          "IRAN DOWNS 2 US DRONES. TANKERS HIT OFF OMAN", 3,
          "Strait of Hormuz: tankers struck off Khasab, 21 Nov. ADNOC ship hit 17 Nov, 1 crew missing.",
          "gulf", "21 NOV")
    panel(528, 172, 472, 296, "UKRAINE UNDER FIRE",
          "400+ DRONES, 110+ MISSILES", 4,
          "Russia's biggest barrage hits Kyiv and Lviv. 2 missiles and a drone fall in Poland, 20 Nov.",
          "ukraine", "20 NOV")
    panel(24, 484, 314, 296, "SHENZHEN SUMMIT",
          "TRUMP - XI - PUTIN MEET", 3,
          "First trilateral summit at APEC. Joint line: nuclear war cannot be won, 19 Nov.",
          "shenzhen", "19 NOV")
    panel(354, 484, 314, 296, "MEXICO",
          "EL CHAPO ISIDRO CAPTURED", 3,
          "FBI most-wanted cartel boss seized in Guasave, Sinaloa. 11 dead, 20 Nov.",
          "mexico", "20 NOV")
    panel(684, 484, 316, 296, "BRAZIL",
          "BOLSONARO IN ICU", 3,
          "Ex-president in intensive care in Brasilia with abdominal obstruction. Stable, 21 Nov.",
          "brazil", "21 NOV")
    fill_rect(24, 796, 488, 104, WHITE)
    rect_outline(24, 796, 488, 104, INK, 3)
    draw_text(36, 808, "COP31 DEADLOCK", 3, RED)
    for _i, _ln in enumerate(wrap("Fossil-fuel wording dropped from draft deal, talks drag on, Antalya.", 488 - 24, 2)):
        draw_text(36, 838 + _i * 18, _ln, 2, DARK)
    fill_rect(528, 796, 472, 104, WHITE)
    rect_outline(528, 796, 472, 104, INK, 3)
    draw_text(540, 808, "PERU M6.9 QUAKE", 3, RED)
    for _i, _ln in enumerate(wrap("Andes, Junin, felt in Lima. No damage reported, 20 Nov.", 472 - 24, 2)):
        draw_text(540, 838 + _i * 18, _ln, 2, DARK)
    fill_rect(24, 912, W - 48, 2, INK)
    draw_text_center(0, 926, W, "SOURCES: REUTERS, BBC, AP, CNN, USGS - 22 NOV 2026", 2, DARK)


def chunk(kind, data):
    _out = struct.pack(">I", len(data)) + kind + data
    _out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return _out


def encode_png():
    _raw = bytearray()
    for _y in range(H):
        _raw.append(0)
        _raw.extend(buf[_y * W * 3:(_y + 1) * W * 3])
    _ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    _png = b"\x89PNG\r\n\x1a\n"
    _png += chunk(b"IHDR", _ihdr)
    _png += chunk(b"IDAT", zlib.compress(bytes(_raw), 9))
    _png += chunk(b"IEND", b"")
    return _png


def main():
    draw_page()
    _out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(_out_dir, exist_ok=True)
    with open(os.path.join(_out_dir, "entry.png"), "wb") as _f:
        _f.write(encode_png())


if __name__ == "__main__":
    main()
