import os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config", "includes.chroot", "usr", "local", "lib", "ocelote-juegos"))
from core import Culebrita, Minas, Pong

# ---- Culebrita
g = Culebrita(10, 6, rng=random.Random(1))
assert len(g.cuerpo) == 3 and g.vivo
cabeza0 = g.cuerpo[0]
g.girar((-1, 0)); g.paso()                      # intentar ir hacia atras: se ignora
assert g.cuerpo[0] == (cabeza0[0] + 1, cabeza0[1])
g.comida = (g.cuerpo[0][0] + 1, g.cuerpo[0][1])  # comida justo delante
n = len(g.cuerpo); g.paso()
assert len(g.cuerpo) == n + 1 and g.puntos == 10 and g.comida not in g.cuerpo
g2 = Culebrita(5, 5, rng=random.Random(2))       # chocar con la pared
for _ in range(10): g2.paso()
assert not g2.vivo
g3 = Culebrita(8, 8, rng=random.Random(3))                # se muerde la cola/cuerpo
g3.cuerpo = [(3, 3), (3, 4), (4, 4), (4, 3), (5, 3)]       # cabeza en (3,3), mirando hacia arriba
g3.dir = g3.sig = (0, -1); g3.comida = (0, 0)
g3.girar((1, 0)); g3.paso()                                  # avanza a (4,3): es parte del cuerpo
assert not g3.vivo

# ---- Buscaminas
m = Minas(9, 9, 10, rng=random.Random(5))
m.abrir(4, 4)
assert m.estado == "jugando" and (4, 4) in m.abiertas and len(m.minas) == 10
assert (4, 4) not in m.minas and not any(v in m.minas for v in m.vecinos(4, 4))   # primer clic seguro
libre = next((x, y) for x in range(9) for y in range(9) if (x, y) not in m.abiertas)
m.bandera(*libre); assert libre in m.banderas and m.minas_restantes() == 9
m.abrir(*libre); assert libre not in m.abiertas          # con bandera no se abre
m.bandera(*libre); assert not m.banderas
# perder
mina = next(iter(m.minas)); m.abrir(*mina); assert m.estado == "perdido"
# ganar abriendo todo lo seguro
m2 = Minas(6, 6, 5, rng=random.Random(6)); m2.abrir(0, 0)
for x in range(6):
    for y in range(6):
        if (x, y) not in m2.minas: m2.abrir(x, y)
assert m2.estado == "ganado"
m2.reset(); assert m2.estado == "jugando" and not m2.minas

# ---- Pong
p = Pong(rng=random.Random(7))
for _ in range(2000): p.paso(1 / 60)
assert p.p1 + p.p2 > 0 or p.fin                     # alguien anota
p = Pong(rng=random.Random(8)); p.mover_jugador(9999); assert p.jy == p.H - p.PH / 2
# la bola rebota arriba/abajo y nunca sale del campo vertical
p = Pong(rng=random.Random(9))
for _ in range(1200):
    p.paso(1 / 60); assert 0 <= p.by <= p.H
# el jugador puede devolver la bola si sigue su posicion
p = Pong(rng=random.Random(10)); devueltas = 0
for _ in range(6000):
    p.mover_jugador(p.by); vx0 = p.vx; p.paso(1 / 60)
    if vx0 < 0 and p.vx > 0: devueltas += 1
    if p.fin: break
assert devueltas >= 3, devueltas
print("OK todas las pruebas de juegos")
