#!/usr/bin/env python3
"""Ocelote Apariencia - elegir tema y modo (ligero/bonito)."""
import subprocess

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

TEMAS = [
    ("aurora",  "Aurora",  "#7C4DDB", "#3F2A99"),
    ("aqua",    "Aqua",    "#2E9BEF", "#124A9C"),
    ("grafito", "Grafito", "#8A8F9C", "#2E3038"),
    ("jade",    "Jade",    "#2EBD8A", "#0E5A52"),
]


class Ventana(Gtk.Window):
    def __init__(self):
        super().__init__(title="Apariencia")
        self.set_icon_name("ocelote-apariencia")
        self.set_border_width(14)
        self.set_default_size(520, 260)
        self.connect("destroy", Gtk.main_quit)
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(caja)
        caja.pack_start(Gtk.Label(label="Elige un tema (cambia iconos, fondo y barra superior):", xalign=0),
                        False, False, 0)
        fila = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        caja.pack_start(fila, False, False, 0)
        for clave, nombre, c1, c2 in TEMAS:
            b = Gtk.Button(label=nombre)
            b.set_size_request(110, 80)
            prov = Gtk.CssProvider()
            prov.load_from_data((
                "button { background-image: linear-gradient(to bottom, %s, %s); color: white; "
                "font-weight: bold; border-radius: 12px; }" % (c1, c2)).encode())
            b.get_style_context().add_provider(prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            b.connect("clicked", self.aplicar, clave)
            fila.pack_start(b, True, True, 0)
        caja.pack_start(Gtk.Separator(), False, False, 4)
        caja.pack_start(Gtk.Label(label="Rendimiento:", xalign=0), False, False, 0)
        fila2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        caja.pack_start(fila2, False, False, 0)
        for etiqueta, cmd in (("Modo ligero (menos CPU)", "ocelote-modo-ligero"),
                              ("Modo bonito (efectos completos)", "ocelote-modo-bonito")):
            b = Gtk.Button(label=etiqueta)
            b.connect("clicked", lambda _b, c=cmd: subprocess.Popen([c]))
            fila2.pack_start(b, True, True, 0)
        self.estado = Gtk.Label(label="", xalign=0)
        caja.pack_start(self.estado, False, False, 0)
        self.show_all()

    def aplicar(self, _btn, clave):
        self.estado.set_text("Aplicando tema %s..." % clave)
        subprocess.Popen(["ocelote-tema", clave])
        self.estado.set_text("Tema %s aplicado." % clave)


if __name__ == "__main__":
    Ventana()
    Gtk.main()
