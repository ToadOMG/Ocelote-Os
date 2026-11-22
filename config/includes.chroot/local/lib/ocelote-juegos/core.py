"""Logica de los juegos de Ocelote OS (sin GTK, se puede probar sola)."""
import random


# ------------------------------------------------------------------ Culebrita
class Culebrita:
    def __init__(self, w=24, h=16, rng=None):
        self.w, self.h = w, h
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        cx, cy = self.w // 2, self.h // 2
        self.cuerpo = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]  # la cabeza va primero
        self.dir = (1, 0)
        self.sig = (1, 0)
        self.puntos = 0
        self.vivo = True
        self.ganado = False
        self.comida = None
        self._nueva_comida()

    def girar(self, d):
        if (d[0] + self.dir[0], d[1] + self.dir[1]) != (0, 0):  # no se puede dar media vuelta
            self.sig = d

    def _nueva_comida(self):
        libres = [(x, y) for x in range(self.w) for y in range(self.h) if (x, y) not in self.cuerpo]
        if not libres:
            self.comida = None
            self.vivo = False
            self.ganado = True
            return
        self.comida = self.rng.choice(libres)

    def paso(self):
        if not self.vivo:
            return
        self.dir = self.sig
        nx, ny = self.cuerpo[0][0] + self.dir[0], self.cuerpo[0][1] + self.dir[1]
        come = (nx, ny) == self.comida
        ocupado = self.cuerpo if come else self.cuerpo[:-1]
        if not (0 <= nx < self.w and 0 <= ny < self.h) or (nx, ny) in ocupado:
            self.vivo = False
            return
        self.cuerpo.insert(0, (nx, ny))
        if come:
            self.puntos += 10
            self._nueva_comida()
        else:
            self.cuerpo.pop()


# ------------------------------------------------------------------ Buscaminas
class Minas:
    def __init__(self, w=9, h=9, minas=10, rng=None):
        self.w, self.h, self.n = w, h, minas
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        self.minas = set()
        self.abiertas = set()
        self.banderas = set()
        self.estado = "jugando"  # jugando | ganado | perdido
        self.colocadas = False

    def vecinos(self, x, y):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if (dx or dy) and 0 <= x + dx < self.w and 0 <= y + dy < self.h:
                    yield (x + dx, y + dy)

    def cuenta(self, x, y):
        return sum(1 for v in self.vecinos(x, y) if v in self.minas)

    def _colocar(self, x0, y0):
        prohibidas = {(x0, y0), *self.vecinos(x0, y0)}  # el primer clic nunca es mina
        celdas = [(x, y) for x in range(self.w) for y in range(self.h) if (x, y) not in prohibidas]
        self.minas = set(self.rng.sample(celdas, min(self.n, len(celdas))))
        self.colocadas = True

    def bandera(self, x, y):
        if self.estado != "jugando" or (x, y) in self.abiertas:
            return
        self.banderas.symmetric_difference_update({(x, y)})

    def abrir(self, x, y):
        if self.estado != "jugando" or (x, y) in self.banderas or (x, y) in self.abiertas:
            return
        if not self.colocadas:
            self._colocar(x, y)
        if (x, y) in self.minas:
            self.estado = "perdido"
            return
        pila = [(x, y)]
        while pila:
            cx, cy = pila.pop()
            if (cx, cy) in self.abiertas or (cx, cy) in self.banderas:
                continue
            self.abiertas.add((cx, cy))
            if self.cuenta(cx, cy) == 0:
                pila.extend(self.vecinos(cx, cy))
        if len(self.abiertas) == self.w * self.h - len(self.minas):
            self.estado = "ganado"

    def minas_restantes(self):
        return self.n - len(self.banderas)


# ------------------------------------------------------------------ Pong
class Pong:
    W, H = 640, 400
    PW, PH, R = 12, 76, 8
    META = 7

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.p1 = self.p2 = 0
        self.jy = self.H / 2          # centro de la paleta del jugador (izquierda)
        self.cy = self.H / 2          # centro de la paleta de la computadora (derecha)
        self.fin = False
        self._saque(1)

    def _saque(self, direccion):
        self.bx, self.by = self.W / 2, self.H / 2
        self.vx = 280.0 * direccion
        self.vy = self.rng.choice((-1, 1)) * self.rng.uniform(60, 170)

    def mover_jugador(self, y):
        self.jy = max(self.PH / 2, min(self.H - self.PH / 2, y))

    def paso(self, dt):
        if self.fin:
            return
        # computadora: sigue la bola con velocidad limitada (se le puede ganar)
        objetivo = self.by
        mov = max(-230 * dt, min(230 * dt, objetivo - self.cy))
        self.cy = max(self.PH / 2, min(self.H - self.PH / 2, self.cy + mov))
        self.bx += self.vx * dt
        self.by += self.vy * dt
        if self.by < self.R:
            self.by, self.vy = self.R, abs(self.vy)
        elif self.by > self.H - self.R:
            self.by, self.vy = self.H - self.R, -abs(self.vy)
        # paleta jugador (x ~ 20) y computadora (x ~ W-20)
        if self.vx < 0 and self.bx - self.R <= 20 + self.PW and abs(self.by - self.jy) <= self.PH / 2 + self.R and self.bx > 10:
            self._rebote(self.jy, 1)
        elif self.vx > 0 and self.bx + self.R >= self.W - 20 - self.PW and abs(self.by - self.cy) <= self.PH / 2 + self.R and self.bx < self.W - 10:
            self._rebote(self.cy, -1)
        if self.bx < -self.R:
            self.p2 += 1
            self._saque(1)
        elif self.bx > self.W + self.R:
            self.p1 += 1
            self._saque(-1)
        if self.p1 >= self.META or self.p2 >= self.META:
            self.fin = True

    def _rebote(self, centro, signo):
        rel = max(-1.0, min(1.0, (self.by - centro) / (self.PH / 2)))
        vel = min(560.0, abs(self.vx) * 1.06)
        self.vx = signo * vel
        self.vy = rel * 260.0
