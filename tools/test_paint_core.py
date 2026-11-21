import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config", "includes.chroot", "usr", "local", "lib", "ocelote-paint"))
from core import flood_fill, History

def make(w, h, stride_extra=0):
    stride = w * 4 + stride_extra
    buf = bytearray(b"\xff" * (stride * h))  # blanco opaco
    return buf, stride

def px(buf, stride, x, y):
    o = y * stride + x * 4
    return tuple(buf[o:o + 4])

# 1) relleno de area completa
buf, st = make(10, 8)
n = flood_fill(buf, 10, 8, st, 3, 3, (255, 0, 0, 255))
assert n == 80, n
assert px(buf, st, 0, 0) == (0, 0, 255, 255) and px(buf, st, 9, 7) == (0, 0, 255, 255)  # BGRA

# 2) respeta barreras (muro negro vertical en x=5)
buf, st = make(10, 8, stride_extra=8)
for y in range(8):
    o = y * st + 5 * 4; buf[o:o + 4] = bytes((0, 0, 0, 255))
n = flood_fill(buf, 10, 8, st, 1, 1, (0, 255, 0, 255))
assert n == 5 * 8, n
assert px(buf, st, 7, 3) == (255, 255, 255, 255)       # el otro lado intacto
assert px(buf, st, 5, 3) == (0, 0, 0, 255)             # el muro intacto

# 3) forma en U (el relleno debe rodear)
buf, st = make(9, 9)
for i in range(9):
    for (x, y) in ((i, 0), (i, 8), (0, i), (8, i)):
        o = y * st + x * 4; buf[o:o + 4] = bytes((0, 0, 0, 255))
for x in range(2, 7):
    o = 4 * st + x * 4; buf[o:o + 4] = bytes((0, 0, 0, 255))
n = flood_fill(buf, 9, 9, st, 1, 1, (0, 0, 255, 255))
assert n == 7 * 7 - 5, n

# 4) mismo color = no hace nada; fuera de rango = 0
buf, st = make(4, 4)
assert flood_fill(buf, 4, 4, st, 1, 1, (255, 255, 255, 255)) == 0
assert flood_fill(buf, 4, 4, st, 9, 9, (1, 2, 3, 255)) == 0
assert flood_fill(buf, 4, 4, st, -1, 0, (1, 2, 3, 255)) == 0

# 5) historial
h = History(max_bytes=100)
h.push((1, 1, b"a" * 40)); h.push((1, 1, b"b" * 40))
assert h.can_undo() and not h.can_redo()
s = h.undo((1, 1, b"c" * 40)); assert s[2] == b"b" * 40
assert h.can_redo()
s = h.redo((1, 1, b"b" * 40)); assert s[2] == b"c" * 40
h.push((1, 1, b"d" * 40)); assert not h.can_redo()      # un cambio nuevo borra rehacer
h.push((1, 1, b"e" * 40)); h.push((1, 1, b"f" * 40))     # supera el limite: descarta los mas viejos
assert sum(len(s[2]) for s in h.undo_stack) <= 100 + 40
assert h.undo_stack[-1][2] == b"f" * 40
h.clear(); assert not h.can_undo()

# 6) rendimiento: 900x600 en blanco
import time
buf, st = make(900, 600)
t = time.time(); n = flood_fill(buf, 900, 600, st, 10, 10, (254, 145, 0, 255)); dt = time.time() - t
assert n == 900 * 600
print("OK todas las pruebas | relleno 900x600: %.2fs" % dt)
