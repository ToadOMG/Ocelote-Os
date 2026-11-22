#!/usr/bin/env python3
"""Juegos de Ocelote OS: culebrita, minas y pong (GTK 3 + cairo).
Uso: juegos.py culebrita|minas|pong"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402
import cairo  # noqa: E402

from core import Culebrita, Minas, Pong  # noqa: E402

CSS = b"""
.celda { min-width: 26px; min-height: 26px; padding: 0; }
.abierta { background-image: none; background-color: #e6e6e6; }
.explotada { background-image: none; background-color: #ff6b6b; }
"""


def aplicar_css():
    prov = Gtk.CssProvider()
    prov.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def texto(cr, s, x, y, tam=18, rgb=(1, 1, 1)):
    cr.set_source_rgb(*rgb)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(tam)
    cr.move_to(x, y)
    cr.show_text(s)


# ====================================================================== Culebrita
class VentanaCulebrita(Gtk.Window):
    CELDA = 20

    def __init__(self):
        super().__init__(title="Culebrita")
        self.set_icon_name("ocelote-culebrita")
        self.set_resizable(False)
        self.juego = Culebrita()
        self.pausa = False
        self.area = Gtk.DrawingArea()
        self.area.set_size_request(self.juego.w * self.CELDA, self.juego.h * self.CELDA)
        self.add(self.area)
        self.area.connect("draw", self.dibujar)
        self.connect("key-press-event", self.tecla)
        self.connect("destroy", Gtk.main_quit)
        GLib.timeout_add(110, self.tick)
        self.show_all()

    def tick(self):
        if not self.pausa:
            self.juego.paso()
        self.area.queue_draw()
        return True

    def tecla(self, w, e):
        k = (Gdk.keyval_name(e.keyval) or "").lower()
        mapa = {"up": (0, -1), "w": (0, -1), "down": (0, 1), "s": (0, 1),
                "left": (-1, 0), "a": (-1, 0), "right": (1, 0), "d": (1, 0)}
        if k in mapa:
            self.juego.girar(mapa[k])
        elif k == "p":
            self.pausa = not self.pausa
        elif k in ("return", "space") and not self.juego.vivo:
            self.juego.reset()
        elif k == "escape":
            Gtk.main_quit()
        return True

    def dibujar(self, w, cr):
        c = self.CELDA
        g = self.juego
        cr.set_source_rgb(0.10, 0.22, 0.14)
        cr.paint()
        if g.comida:
            cr.set_source_rgb(0.9, 0.2, 0.2)
            cr.arc(g.comida[0] * c + c / 2, g.comida[1] * c + c / 2, c * 0.38, 0, 2 * math.pi)
            cr.fill()
        for i, (x, y) in enumerate(g.cuerpo):
            cr.set_source_rgb(*((0.55, 0.95, 0.45) if i == 0 else (0.35, 0.78, 0.35)))
            cr.rectangle(x * c + 1, y * c + 1, c - 2, c - 2)
            cr.fill()
        texto(cr, "Puntos: %d" % g.puntos, 8, 20, 15)
        if self.pausa:
            texto(cr, "PAUSA (P)", g.w * c / 2 - 50, g.h * c / 2, 22)
        if not g.vivo:
            msg = "¡Ganaste!" if g.ganado else "Fin del juego"
            texto(cr, msg, g.w * c / 2 - 70, g.h * c / 2 - 10, 28, (1, 0.9, 0.3))
            texto(cr, "Enter para reiniciar", g.w * c / 2 - 85, g.h * c / 2 + 22, 16)
        return False


# ====================================================================== Minas
class VentanaMinas(Gtk.Window):
    NIVELES = (("Principiante 9x9", 9, 9, 10), ("Intermedio 16x16", 16, 16, 40))
    COLORES = {1: "#1e88e5", 2: "#2e7d32", 3: "#e53935", 4: "#3949ab", 5: "#8e24aa", 6: "#00838f", 7: "#000000", 8: "#616161"}

    def __init__(self):
        super().__init__(title="Minas")
        self.set_icon_name("ocelote-minas")
        self.set_resizable(False)
        self.connect("destroy", Gtk.main_quit)
        self.caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.caja.set_border_width(8)
        self.add(self.caja)
        barra = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.combo = Gtk.ComboBoxText()
        for nombre, *_ in self.NIVELES:
            self.combo.append_text(nombre)
        self.combo.set_active(0)
        self.combo.connect("changed", lambda _c: self.nuevo())
        barra.pack_start(self.combo, False, False, 0)
        b = Gtk.Button(label="Nuevo juego")
        b.connect("clicked", lambda _b: self.nuevo())
        barra.pack_start(b, False, False, 0)
        self.info = Gtk.Label(label="")
        barra.pack_end(self.info, False, False, 0)
        self.caja.pack_start(barra, False, False, 0)
        self.grid = None
        self.botones = {}
        self.nuevo()

    def nuevo(self):
        _, w, h, n = self.NIVELES[self.combo.get_active()]
        self.juego = Minas(w, h, n)
        if self.grid is not None:
            self.caja.remove(self.grid)
        self.grid = Gtk.Grid(column_spacing=1, row_spacing=1)
        self.botones = {}
        for x in range(w):
            for y in range(h):
                b = Gtk.Button(label=" ")
                b.get_style_context().add_class("celda")
                b.connect("button-press-event", self.clic, x, y)
                self.grid.attach(b, x, y, 1, 1)
                self.botones[(x, y)] = b
        self.caja.pack_start(self.grid, False, False, 0)
        self.refrescar()
        self.show_all()

    def clic(self, widget, evento, x, y):
        if evento.button == 1:
            self.juego.abrir(x, y)
        elif evento.button == 3:
            self.juego.bandera(x, y)
        self.refrescar()
        return True

    def refrescar(self):
        j = self.juego
        for (x, y), b in self.botones.items():
            lbl = b.get_child()
            ctx = b.get_style_context()
            ctx.remove_class("abierta")
            ctx.remove_class("explotada")
            if (x, y) in j.abiertas:
                ctx.add_class("abierta")
                n = j.cuenta(x, y)
                lbl.set_markup('<b><span foreground="%s">%s</span></b>' % (self.COLORES.get(n, "#000"), n if n else " "))
            elif j.estado == "perdido" and (x, y) in j.minas:
                ctx.add_class("explotada")
                lbl.set_markup("<b>*</b>")
            elif (x, y) in j.banderas:
                lbl.set_markup('<b><span foreground="#d81b60">F</span></b>')
            else:
                lbl.set_text(" ")
        if j.estado == "ganado":
            self.info.set_text("¡Ganaste!")
        elif j.estado == "perdido":
            self.info.set_text("¡Boom! Perdiste")
        else:
            self.info.set_text("Minas: %d   (clic derecho = bandera)" % j.minas_restantes())


# ====================================================================== Pong
class VentanaPong(Gtk.Window):
    def __init__(self):
        super().__init__(title="Pong")
        self.set_icon_name("ocelote-pong")
        self.set_resizable(False)
        self.juego = Pong()
        self.pausa = False
        self.area = Gtk.DrawingArea()
        self.area.set_size_request(Pong.W, Pong.H)
        self.area.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.add(self.area)
        self.area.connect("draw", self.dibujar)
        self.area.connect("motion-notify-event", lambda w, e: (self.juego.mover_jugador(e.y), True)[1])
        self.connect("key-press-event", self.tecla)
        self.connect("destroy", Gtk.main_quit)
        GLib.timeout_add(25, self.tick)
        self.show_all()

    def tick(self):
        if not self.pausa:
            self.juego.paso(0.025)
        self.area.queue_draw()
        return True

    def tecla(self, w, e):
        k = (Gdk.keyval_name(e.keyval) or "").lower()
        if k in ("up", "w"):
            self.juego.mover_jugador(self.juego.jy - 30)
        elif k in ("down", "s"):
            self.juego.mover_jugador(self.juego.jy + 30)
        elif k == "p":
            self.pausa = not self.pausa
        elif k in ("return", "space") and self.juego.fin:
            self.juego = Pong()
        elif k == "escape":
            Gtk.main_quit()
        return True

    def dibujar(self, w, cr):
        j = self.juego
        cr.set_source_rgb(0.05, 0.05, 0.12)
        cr.paint()
        cr.set_source_rgba(1, 1, 1, 0.25)
        cr.set_line_width(3)
        cr.set_dash([10, 10])
        cr.move_to(j.W / 2, 0)
        cr.line_to(j.W / 2, j.H)
        cr.stroke()
        cr.set_dash([])
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(20, j.jy - j.PH / 2, j.PW, j.PH)
        cr.rectangle(j.W - 20 - j.PW, j.cy - j.PH / 2, j.PW, j.PH)
        cr.fill()
        cr.set_source_rgb(1, 0.57, 0)
        cr.arc(j.bx, j.by, j.R, 0, 2 * math.pi)
        cr.fill()
        texto(cr, str(j.p1), j.W / 2 - 60, 50, 36)
        texto(cr, str(j.p2), j.W / 2 + 36, 50, 36)
        if j.fin:
            texto(cr, "¡Ganaste!" if j.p1 > j.p2 else "Perdiste", j.W / 2 - 70, j.H / 2, 32, (1, 0.9, 0.3))
            texto(cr, "Enter para jugar otra vez", j.W / 2 - 110, j.H / 2 + 32, 16)
        return False


JUEGOS = {"culebrita": VentanaCulebrita, "minas": VentanaMinas, "pong": VentanaPong}


def main():
    nombre = sys.argv[1] if len(sys.argv) > 1 else "culebrita"
    if nombre not in JUEGOS:
        print("Juegos disponibles:", ", ".join(JUEGOS))
        return 1
    aplicar_css()
    JUEGOS[nombre]()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
