#!/usr/bin/env python3
"""Ocelote Escudo 0.1 - antivirus basico con interfaz clasica (GTK 3)."""
import os
import shutil
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango  # noqa: E402
import cairo  # noqa: E402

import engine  # noqa: E402

SONIDO = "/usr/share/ocelote/sonidos/virus-detectado.mp3"
RESP_MOVER, RESP_ELIMINAR, RESP_IGNORAR = 1, 2, 3
AUTOSTART = os.path.join(os.path.expanduser("~"), ".config", "autostart", "ocelote-escudo-vigia.desktop")
AUTOSTART_TXT = ("[Desktop Entry]\nType=Application\nName=Ocelote Escudo (vigía)\n"
                 "Exec=ocelote-escudo-vigia\nX-GNOME-Autostart-enabled=true\n")

CSS = b"""
.escudo-lateral { background-image: linear-gradient(to bottom, #3b3b3b, #1b1b1b); }
.escudo-item { background-image: none; background-color: transparent; color: #dddddd;
               border: none; border-radius: 0; padding: 12px 16px; box-shadow: none; }
.escudo-item:checked { background-color: #FE9100; color: #ffffff; }
.escudo-titulo { font-size: 30px; font-weight: bold; color: #2e9e4f; }
.escudo-aviso { font-size: 30px; font-weight: bold; color: #e07800; }
.alerta { background-color: #dcdcdc; }
.alerta label { color: #111111; }
"""


def reproducir_alerta():
    for cmd in (["mpg123", "-q", SONIDO], ["paplay", SONIDO], ["pw-play", SONIDO]):
        if shutil.which(cmd[0]) and os.path.exists(SONIDO):
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                continue
            return


def aplicar_estilos():
    prov = Gtk.CssProvider()
    prov.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def mensaje(parent, texto):
    d = Gtk.MessageDialog(transient_for=parent, modal=True, message_type=Gtk.MessageType.INFO,
                          buttons=Gtk.ButtonsType.OK, text=texto)
    d.run()
    d.destroy()


def aplicar_accion(h, resp):
    """Devuelve None si todo bien o un texto de error."""
    try:
        if resp == RESP_MOVER:
            engine.mover_al_cofre(h.ruta, h.nombre)
        elif resp == RESP_ELIMINAR:
            engine.eliminar_archivo(h.ruta)
    except OSError as e:
        return str(e)
    return None


class AlertaVirus(Gtk.Dialog):
    """Ventana de alerta con el estilo clasico de los antivirus de 2008."""

    def __init__(self, parent, h, simulacion=False):
        super().__init__(title="Ocelote Escudo - Advertencia" + (" (simulación)" if simulacion else ""),
                         transient_for=parent, modal=parent is not None)
        self.h = h
        self.set_resizable(False)
        self.set_keep_above(True)
        self.get_style_context().add_class("alerta")
        caja = self.get_content_area()
        caja.set_border_width(14)
        caja.set_spacing(10)

        if h.tipo.startswith("Archivo de prueba"):
            titulo = "¡Se encontró el archivo de prueba EICAR!"
        elif h.tipo == "Heurística":
            titulo = "¡Se encontró un archivo sospechoso!"
        else:
            titulo = "¡Se encontró un virus!"

        cab = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        icono = Gtk.DrawingArea()
        icono.set_size_request(84, 84)
        icono.connect("draw", self.dibujar_icono)
        cab.pack_start(icono, False, False, 0)
        textos = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        t = Gtk.Label(xalign=0)
        t.set_markup('<span size="xx-large" weight="bold">%s</span>' % GLib.markup_escape_text(titulo))
        textos.pack_start(t, False, False, 0)
        d = Gtk.Label(xalign=0, wrap=True)
        d.set_max_width_chars(60)
        d.set_text("No hay motivo para entrar en pánico. Siga los consejos que aparecen aquí. "
                   "Si su equipo forma parte de una red, desconecte el cable de red para evitar que "
                   "la infección se propague.")
        textos.pack_start(d, False, False, 0)
        cab.pack_start(textos, True, True, 0)
        caja.pack_start(cab, False, False, 0)

        grid = Gtk.Grid(column_spacing=16, row_spacing=4)
        filas = (("Nombre del archivo:", h.ruta), ("Nombre de la amenaza:", h.nombre),
                 ("Tipo de amenaza:", h.tipo), ("Firmas:", engine.VERSION_FIRMAS))
        for i, (a, b) in enumerate(filas):
            grid.attach(Gtk.Label(label=a, xalign=0), 0, i, 1, 1)
            v = Gtk.Label(label=b, xalign=0, selectable=True)
            v.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
            v.set_max_width_chars(52)
            grid.attach(v, 1, i, 1, 1)
        caja.pack_start(grid, False, False, 0)

        marco = Gtk.Frame(label=" Acciones disponibles ")
        interior = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        interior.set_border_width(10)
        marco.add(interior)
        fila = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for texto, resp in (("Mover al cofre", RESP_MOVER), ("Eliminar", RESP_ELIMINAR), ("Ignorar", RESP_IGNORAR)):
            b = Gtk.Button(label=texto)
            b.set_sensitive(not simulacion or resp == RESP_IGNORAR)
            b.connect("clicked", lambda _b, r=resp: self.response(r))
            fila.pack_start(b, True, True, 0)
        interior.pack_start(fila, False, False, 0)
        rec = Gtk.Label(xalign=0)
        rec.set_markup("<b>Acción recomendada: Mover al cofre</b>" if not simulacion
                       else "<b>Simulación: no hay ningún archivo real.</b>")
        interior.pack_start(rec, False, False, 0)
        caja.pack_start(marco, False, False, 0)
        self.show_all()
        reproducir_alerta()

    def dibujar_icono(self, widget, cr):
        cr.move_to(42, 6)
        cr.line_to(80, 76)
        cr.line_to(4, 76)
        cr.close_path()
        cr.set_source_rgb(0.86, 0.12, 0.12)
        cr.fill_preserve()
        cr.set_source_rgb(0.45, 0.0, 0.0)
        cr.set_line_width(3)
        cr.stroke()
        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(8)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(42, 30)
        cr.line_to(42, 52)
        cr.stroke()
        cr.arc(42, 64, 4.5, 0, 6.2832)
        cr.fill()
        return False


class Escudo(Gtk.Window):
    def __init__(self):
        super().__init__(title="Ocelote Escudo")
        self.set_icon_name("ocelote-escudo")
        self.set_default_size(780, 520)
        self.connect("destroy", self.salir)
        self.firmas = engine.cargar_firmas()
        self.cancelar = False
        self.escaneando = False
        self.hallazgos = []
        self.cfg = engine.leer_config()

        raiz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(raiz)
        lateral = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        lateral.get_style_context().add_class("escudo-lateral")
        lateral.set_size_request(200, -1)
        raiz.pack_start(lateral, False, False, 0)
        marca = Gtk.Label()
        marca.set_markup('<span foreground="#ffffff" size="x-large" weight="bold">Ocelote</span>'
                         '<span foreground="#FE9100" size="x-large"> Escudo</span>')
        marca.set_margin_top(16)
        marca.set_margin_bottom(16)
        lateral.pack_start(marca, False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)
        raiz.pack_start(self.stack, True, True, 0)

        primero = None
        for nombre, etiqueta in (("resumen", "Resumen"), ("analizar", "Analizar equipo"),
                                 ("escudo", "Escudo en tiempo real"), ("cofre", "Mantenimiento (cofre)")):
            if primero is None:
                b = Gtk.RadioButton.new_with_label(None, etiqueta)
                primero = b
            else:
                b = Gtk.RadioButton.new_with_label_from_widget(primero, etiqueta)
            b.set_mode(False)
            b.get_style_context().add_class("escudo-item")
            b.connect("toggled", self.cambiar_pagina, nombre)
            lateral.pack_start(b, False, False, 0)

        self.stack.add_named(self.pagina_resumen(), "resumen")
        self.stack.add_named(self.pagina_analizar(), "analizar")
        self.stack.add_named(self.pagina_escudo(), "escudo")
        self.stack.add_named(self.pagina_cofre(), "cofre")
        self.actualizar_resumen()
        self.show_all()

    def salir(self, *_):
        self.cancelar = True
        Gtk.main_quit()

    def cambiar_pagina(self, btn, nombre):
        if btn.get_active():
            self.stack.set_visible_child_name(nombre)
            if nombre == "cofre":
                self.refrescar_cofre()
            if nombre == "resumen":
                self.actualizar_resumen()

    # ------------------------------------------------------------ resumen
    def pagina_resumen(self):
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        caja.set_border_width(20)
        cab = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        self.icono_estado = Gtk.DrawingArea()
        self.icono_estado.set_size_request(96, 96)
        self.icono_estado.connect("draw", self.dibujar_estado)
        cab.pack_start(self.icono_estado, False, False, 0)
        textos = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.lbl_estado = Gtk.Label(xalign=0)
        self.lbl_sub = Gtk.Label(xalign=0)
        textos.pack_start(self.lbl_estado, False, False, 0)
        textos.pack_start(self.lbl_sub, False, False, 0)
        cab.pack_start(textos, True, True, 0)
        caja.pack_start(cab, False, False, 0)
        grid = Gtk.Grid(column_spacing=30, row_spacing=10)
        self.val_escudo = Gtk.Label(xalign=0)
        self.val_ultimo = Gtk.Label(xalign=0)
        filas = (("Escudo en tiempo real:", self.val_escudo),
                 ("Firmas de virus:", Gtk.Label(label=engine.VERSION_FIRMAS, xalign=0)),
                 ("Último análisis:", self.val_ultimo),
                 ("Versión del programa:", Gtk.Label(label=engine.VERSION_PROGRAMA, xalign=0)))
        for i, (a, w) in enumerate(filas):
            grid.attach(Gtk.Label(label=a, xalign=0), 0, i, 1, 1)
            grid.attach(w, 1, i, 1, 1)
        caja.pack_start(grid, False, False, 8)
        b = Gtk.Button(label="Analizar ahora (rápido)")
        b.connect("clicked", lambda _b: self.ir_a_analisis_rapido())
        caja.pack_start(b, False, False, 0)
        aviso = Gtk.Label(xalign=0, wrap=True)
        aviso.set_text("Ocelote Escudo es un antivirus básico: detecta el archivo de prueba EICAR, firmas "
                       "de una lista local y trucos comunes (doble extensión, autorun.inf).")
        caja.pack_end(aviso, False, False, 0)
        return caja

    def vigia_activo(self):
        return bool(self.cfg.get("vigia"))

    def actualizar_resumen(self):
        self.cfg = engine.leer_config()
        ok = self.vigia_activo() and not self.hallazgos
        self.lbl_estado.get_style_context().remove_class("escudo-titulo")
        self.lbl_estado.get_style_context().remove_class("escudo-aviso")
        if ok:
            self.lbl_estado.set_text("PROTEGIDO")
            self.lbl_estado.get_style_context().add_class("escudo-titulo")
            self.lbl_sub.set_text("Su sistema está protegido.")
        else:
            self.lbl_estado.set_text("ATENCIÓN")
            self.lbl_estado.get_style_context().add_class("escudo-aviso")
            self.lbl_sub.set_text("Hay amenazas sin resolver." if self.hallazgos
                                  else "El escudo en tiempo real está apagado.")
        self.val_escudo.set_text("Activado" if self.vigia_activo() else "Apagado")
        self.val_ultimo.set_text(self.cfg.get("ultimo_analisis", "Nunca"))
        self.icono_estado.queue_draw()

    def dibujar_estado(self, widget, cr):
        ok = self.vigia_activo() and not self.hallazgos
        cr.arc(48, 48, 44, 0, 6.2832)
        cr.set_source_rgb(*((0.18, 0.62, 0.31) if ok else (0.93, 0.52, 0.0)))
        cr.fill()
        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(9)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        if ok:
            cr.move_to(27, 50)
            cr.line_to(42, 65)
            cr.line_to(70, 32)
            cr.stroke()
        else:
            cr.move_to(48, 24)
            cr.line_to(48, 54)
            cr.stroke()
            cr.arc(48, 70, 5, 0, 6.2832)
            cr.fill()
        return False

    # ------------------------------------------------------------ analizar
    def pagina_analizar(self):
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        caja.set_border_width(16)
        fila = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for texto, cb in (("Análisis rápido", lambda _b: self.ir_a_analisis_rapido()),
                          ("Carpeta personal", lambda _b: self.iniciar_analisis([os.path.expanduser("~")])),
                          ("Elegir carpeta...", self.elegir_carpeta),
                          ("Detener", lambda _b: setattr(self, "cancelar", True))):
            b = Gtk.Button(label=texto)
            b.connect("clicked", cb)
            fila.pack_start(b, False, False, 0)
        caja.pack_start(fila, False, False, 0)
        self.barra = Gtk.ProgressBar()
        caja.pack_start(self.barra, False, False, 0)
        self.lbl_actual = Gtk.Label(label="Listo para analizar.", xalign=0)
        self.lbl_actual.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        caja.pack_start(self.lbl_actual, False, False, 0)
        self.modelo = Gtk.ListStore(str, str, str)
        vista = Gtk.TreeView(model=self.modelo)
        for i, titulo in enumerate(("Archivo", "Amenaza", "Tipo")):
            vista.append_column(Gtk.TreeViewColumn(titulo, Gtk.CellRendererText(), text=i))
        sc = Gtk.ScrolledWindow()
        sc.add(vista)
        caja.pack_start(sc, True, True, 0)
        return caja

    def raices_rapidas(self):
        r = engine.carpetas_vigiladas()
        return r or [os.path.expanduser("~")]

    def ir_a_analisis_rapido(self):
        self.iniciar_analisis(self.raices_rapidas())

    def elegir_carpeta(self, *_):
        d = Gtk.FileChooserDialog(title="Elegir carpeta a analizar", transient_for=self,
                                  action=Gtk.FileChooserAction.SELECT_FOLDER)
        d.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        d.add_button("Analizar", Gtk.ResponseType.OK)
        if d.run() == Gtk.ResponseType.OK:
            ruta = d.get_filename()
            d.destroy()
            self.iniciar_analisis([ruta])
        else:
            d.destroy()

    def iniciar_analisis(self, raices):
        if self.escaneando:
            return
        self.stack.set_visible_child_name("analizar")
        self.escaneando = True
        self.cancelar = False
        self.hallazgos = []
        self.modelo.clear()
        self.lbl_actual.set_text("Analizando...")
        threading.Thread(target=self._trabajo, args=(list(raices),), daemon=True).start()
        GLib.timeout_add(120, self._pulsar)

    def _pulsar(self):
        if self.escaneando:
            self.barra.pulse()
            return True
        return False

    def _trabajo(self, raices):
        cont = 0
        for tipo, dato in engine.escanear(raices, self.firmas, cancelar=lambda: self.cancelar):
            if tipo == "archivo":
                cont += 1
                if cont % 25 == 0:
                    GLib.idle_add(self.lbl_actual.set_text, "%d archivos... %s" % (cont, dato))
                    time.sleep(0.01)  # cede CPU para no congelar el equipo
            else:
                GLib.idle_add(self._agregar_hallazgo, dato)
        GLib.idle_add(self._fin_analisis, cont)

    def _agregar_hallazgo(self, h):
        self.hallazgos.append(h)
        self.modelo.append([h.ruta, h.nombre, h.tipo])
        return False

    def _fin_analisis(self, cont):
        self.escaneando = False
        self.barra.set_fraction(1.0 if not self.cancelar else 0.0)
        estado = "cancelado" if self.cancelar else "terminado"
        self.lbl_actual.set_text("Análisis %s: %d archivos, %d amenazas." % (estado, cont, len(self.hallazgos)))
        if not self.cancelar:
            self.cfg["ultimo_analisis"] = time.strftime("%Y-%m-%d %H:%M")
            engine.guardar_config(self.cfg)
        pendientes = list(self.hallazgos)
        for h in pendientes[:5]:
            self.mostrar_alerta(h)
        self.actualizar_resumen()
        return False

    def mostrar_alerta(self, h):
        dlg = AlertaVirus(self, h)
        resp = dlg.run()
        dlg.destroy()
        if resp in (RESP_MOVER, RESP_ELIMINAR):
            err = aplicar_accion(h, resp)
            if err:
                mensaje(self, "No se pudo completar la acción:\n%s" % err)
            elif h in self.hallazgos:
                self.hallazgos.remove(h)

    # ------------------------------------------------------------ escudo
    def pagina_escudo(self):
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        caja.set_border_width(20)
        d = Gtk.Label(xalign=0, wrap=True)
        d.set_text("El escudo revisa las carpetas Descargas y Escritorio cada pocos segundos. "
                   "Usa muy poca CPU y se inicia solo al entrar. Está apagado por defecto para no "
                   "gastar recursos en equipos justos.")
        caja.pack_start(d, False, False, 0)
        fila = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        fila.pack_start(Gtk.Label(label="Vigilar Descargas y Escritorio"), False, False, 0)
        self.sw = Gtk.Switch()
        self.sw.set_active(self.vigia_activo())
        self.sw.connect("notify::active", self.on_vigia)
        fila.pack_start(self.sw, False, False, 0)
        caja.pack_start(fila, False, False, 0)
        caja.pack_start(Gtk.Separator(), False, False, 6)
        pruebas = Gtk.Label(xalign=0, wrap=True)
        pruebas.set_text("Pruebas (seguras):")
        caja.pack_start(pruebas, False, False, 0)
        b1 = Gtk.Button(label="Crear archivo de prueba EICAR en Descargas")
        b1.connect("clicked", self.crear_eicar)
        b2 = Gtk.Button(label="Simular alerta de virus")
        b2.connect("clicked", self.simular)
        caja.pack_start(b1, False, False, 0)
        caja.pack_start(b2, False, False, 0)
        return caja

    def on_vigia(self, sw, _p):
        activo = sw.get_active()
        self.cfg = engine.leer_config()
        self.cfg["vigia"] = activo
        engine.guardar_config(self.cfg)
        if activo:
            os.makedirs(os.path.dirname(AUTOSTART), exist_ok=True)
            with open(AUTOSTART, "w", encoding="utf-8") as f:
                f.write(AUTOSTART_TXT)
            subprocess.Popen(["ocelote-escudo-vigia"], start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            try:
                os.remove(AUTOSTART)
            except OSError:
                pass
            subprocess.run(["pkill", "-f", "ocelote-escudo-vigia"], check=False)
        self.actualizar_resumen()

    def crear_eicar(self, *_):
        carpeta = engine.carpeta_xdg("DOWNLOAD", ("Descargas", "Downloads")) or os.path.expanduser("~")
        ruta = engine.crear_archivo_eicar(carpeta)
        mensaje(self, "Se creó el archivo de prueba:\n%s\n\nEs inofensivo. Analiza Descargas para verlo "
                      "detectado (o activa el escudo en tiempo real)." % ruta)

    def simular(self, *_):
        h = engine.Hallazgo("C:\\windows\\syschecks.dll", "Win32:Trojan-gen {Simulado}", "Virus/Worm (simulación)")
        dlg = AlertaVirus(self, h, simulacion=True)
        dlg.run()
        dlg.destroy()

    # ------------------------------------------------------------ cofre
    def pagina_cofre(self):
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        caja.set_border_width(16)
        caja.pack_start(Gtk.Label(label="Archivos en el cofre (aislados, sin permiso de ejecución):", xalign=0),
                        False, False, 0)
        self.modelo_cofre = Gtk.ListStore(str, str, str)
        self.items_cofre = []
        vista = Gtk.TreeView(model=self.modelo_cofre)
        self.sel_cofre = vista.get_selection()
        for i, titulo in enumerate(("Archivo original", "Amenaza", "Fecha")):
            vista.append_column(Gtk.TreeViewColumn(titulo, Gtk.CellRendererText(), text=i))
        sc = Gtk.ScrolledWindow()
        sc.add(vista)
        caja.pack_start(sc, True, True, 0)
        fila = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        b1 = Gtk.Button(label="Restaurar")
        b1.connect("clicked", self.restaurar)
        b2 = Gtk.Button(label="Eliminar definitivamente")
        b2.connect("clicked", self.eliminar_cofre)
        fila.pack_start(b1, False, False, 0)
        fila.pack_start(b2, False, False, 0)
        caja.pack_start(fila, False, False, 0)
        return caja

    def refrescar_cofre(self):
        self.modelo_cofre.clear()
        self.items_cofre = engine.listar_cofre()
        for i in self.items_cofre:
            self.modelo_cofre.append([i["original"], i.get("amenaza", ""), i.get("fecha", "")])

    def _item_seleccionado(self):
        modelo, it = self.sel_cofre.get_selected()
        if it is None:
            return None
        return self.items_cofre[modelo.get_path(it).get_indices()[0]]

    def restaurar(self, *_):
        item = self._item_seleccionado()
        if item:
            try:
                engine.restaurar(item)
            except OSError as e:
                mensaje(self, "No se pudo restaurar:\n%s" % e)
            self.refrescar_cofre()

    def eliminar_cofre(self, *_):
        item = self._item_seleccionado()
        if item:
            engine.eliminar_del_cofre(item)
            self.refrescar_cofre()


def main():
    try:
        os.nice(10)  # prioridad baja: que el analisis no congele el equipo
    except OSError:
        pass
    aplicar_estilos()
    args = sys.argv[1:]
    if args[:1] == ["--alerta"] and len(args) > 1:
        h = engine.analizar_archivo(args[1], engine.cargar_firmas())
        if h:
            dlg = AlertaVirus(None, h)
            resp = dlg.run()
            dlg.destroy()
            if resp in (RESP_MOVER, RESP_ELIMINAR):
                err = aplicar_accion(h, resp)
                if err:
                    mensaje(None, "No se pudo completar la acción:\n%s" % err)
        return
    if args[:1] == ["--simular"]:
        h = engine.Hallazgo("C:\\windows\\syschecks.dll", "Win32:Trojan-gen {Simulado}", "Virus/Worm (simulación)")
        dlg = AlertaVirus(None, h, simulacion=True)
        dlg.run()
        dlg.destroy()
        return
    Escudo()
    Gtk.main()


if __name__ == "__main__":
    main()
