#!/usr/bin/env python3
"""Ocelote Paint 0.1 - programa de dibujo sencillo (GTK 3 + cairo)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf  # noqa: E402
import cairo  # noqa: E402

from core import flood_fill, History  # noqa: E402

TOOLS = [
    ("lapiz", "Lápiz"), ("pincel", "Pincel"), ("borrador", "Borrador"),
    ("linea", "Línea"), ("rect", "Rectángulo"), ("elipse", "Elipse"),
    ("relleno", "Relleno"), ("gotero", "Gotero"),
]
SHAPES = ("linea", "rect", "elipse")
PALETTE = [
    "#000000", "#7f7f7f", "#c3c3c3", "#ffffff", "#fe9100", "#e53935", "#ec407a", "#8e24aa",
    "#3949ab", "#1e88e5", "#00acc1", "#43a047", "#c0ca33", "#fdd835", "#8d6e63", "#5d4037",
]
DEFAULT_W, DEFAULT_H = 900, 600
MAX_PIXELS = 25_000_000


def hex_to_rgb(h):
    rgba = Gdk.RGBA()
    rgba.parse(h)
    return (rgba.red, rgba.green, rgba.blue)


def draw_shape(cr, tool, x0, y0, x1, y1, rgb, width, filled):
    cr.set_source_rgb(*rgb)
    cr.set_line_width(width)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    if tool == "linea":
        cr.move_to(x0, y0)
        cr.line_to(x1, y1)
        cr.stroke()
    elif tool == "rect":
        cr.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        if filled:
            cr.fill()
        else:
            cr.stroke()
    elif tool == "elipse":
        rx = max(abs(x1 - x0) / 2.0, 0.5)
        ry = max(abs(y1 - y0) / 2.0, 0.5)
        cr.save()
        cr.translate((x0 + x1) / 2.0, (y0 + y1) / 2.0)
        cr.scale(rx, ry)
        cr.arc(0, 0, 1, 0, 2 * math.pi)
        cr.restore()
        if filled:
            cr.fill()
        else:
            cr.stroke()


class Canvas(Gtk.DrawingArea):
    def __init__(self, on_motion=None, on_pick=None):
        super().__init__()
        self.on_motion_cb = on_motion
        self.on_pick_cb = on_pick
        self.history = History()
        self.tool = "pincel"
        self.color = (0.0, 0.0, 0.0)
        self.size = 6
        self.filled = False
        self.dirty = False
        self.filename = None
        self.start = None
        self.last = None
        self.preview = None
        self.stroking = False
        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.START)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_press)
        self.connect("button-release-event", self.on_release)
        self.connect("motion-notify-event", self.on_motion)
        self.new_surface(DEFAULT_W, DEFAULT_H)

    # ---------- superficie ----------
    def new_surface(self, w, h):
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(self.surface)
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        self.surface.flush()
        self.set_size_request(w, h)
        self.history.clear()
        self.dirty = False
        self.queue_draw()

    def snapshot(self):
        self.surface.flush()
        return (self.surface.get_width(), self.surface.get_height(), bytes(self.surface.get_data()))

    def restore(self, snap):
        w, h, data = snap
        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, w)
        self.surface = cairo.ImageSurface.create_for_data(bytearray(data), cairo.FORMAT_ARGB32, w, h, stride)
        self.set_size_request(w, h)
        self.dirty = True
        self.queue_draw()

    def push_history(self):
        self.history.push(self.snapshot())
        self.dirty = True

    def undo(self):
        snap = self.history.undo(self.snapshot())
        if snap:
            self.restore(snap)

    def redo(self):
        snap = self.history.redo(self.snapshot())
        if snap:
            self.restore(snap)

    # ---------- dibujo ----------
    def on_draw(self, widget, cr):
        cr.set_source_surface(self.surface, 0, 0)
        cr.paint()
        if self.preview:
            tool, x0, y0, x1, y1 = self.preview
            draw_shape(cr, tool, x0, y0, x1, y1, self.color, self.size, self.filled)
        return False

    def stroke_segment(self, x0, y0, x1, y1):
        tool = self.tool
        if tool == "borrador":
            rgb, width = (1.0, 1.0, 1.0), max(self.size * 2, 4)
        elif tool == "lapiz":
            rgb, width = self.color, 1.5
        else:
            rgb, width = self.color, self.size
        cr = cairo.Context(self.surface)
        cr.set_source_rgb(*rgb)
        cr.set_line_width(width)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        if (x0, y0) == (x1, y1):
            cr.arc(x0, y0, width / 2.0, 0, 2 * math.pi)
            cr.fill()
        else:
            cr.move_to(x0, y0)
            cr.line_to(x1, y1)
            cr.stroke()
        self.surface.flush()
        self.queue_draw()

    def pixel_at(self, x, y):
        w, h = self.surface.get_width(), self.surface.get_height()
        x, y = int(x), int(y)
        if not (0 <= x < w and 0 <= y < h):
            return None
        self.surface.flush()
        data = self.surface.get_data()
        o = y * self.surface.get_stride() + x * 4
        b, g, r, a = data[o], data[o + 1], data[o + 2], data[o + 3]
        return (r / 255.0, g / 255.0, b / 255.0)

    # ---------- eventos ----------
    def on_press(self, widget, event):
        if event.button != 1:
            return False
        x, y = event.x, event.y
        if self.tool == "relleno":
            self.push_history()
            rgb = tuple(int(round(c * 255)) for c in self.color)
            self.surface.flush()
            flood_fill(self.surface.get_data(), self.surface.get_width(), self.surface.get_height(),
                       self.surface.get_stride(), x, y, rgb + (255,))
            self.surface.mark_dirty()
            self.queue_draw()
        elif self.tool == "gotero":
            c = self.pixel_at(x, y)
            if c and self.on_pick_cb:
                self.on_pick_cb(c)
        elif self.tool in SHAPES:
            self.push_history()
            self.start = (x, y)
            self.preview = (self.tool, x, y, x, y)
        else:  # lapiz, pincel, borrador
            self.push_history()
            self.stroking = True
            self.last = (x, y)
            self.stroke_segment(x, y, x, y)
        return True

    def on_motion(self, widget, event):
        if self.on_motion_cb:
            self.on_motion_cb(int(event.x), int(event.y))
        if self.stroking and self.last:
            self.stroke_segment(self.last[0], self.last[1], event.x, event.y)
            self.last = (event.x, event.y)
        elif self.start:
            self.preview = (self.tool, self.start[0], self.start[1], event.x, event.y)
            self.queue_draw()
        return True

    def on_release(self, widget, event):
        if event.button != 1:
            return False
        if self.stroking:
            self.stroking = False
            self.last = None
        elif self.start:
            x0, y0 = self.start
            cr = cairo.Context(self.surface)
            draw_shape(cr, self.tool, x0, y0, event.x, event.y, self.color, self.size, self.filled)
            self.surface.flush()
            self.start = None
            self.preview = None
            self.queue_draw()
        return True

    # ---------- archivos ----------
    def save_png(self, path):
        self.surface.flush()
        self.surface.write_to_png(path)
        self.filename = path
        self.dirty = False

    def open_image(self, path):
        pb = GdkPixbuf.Pixbuf.new_from_file(path)
        w, h = pb.get_width(), pb.get_height()
        if w * h > MAX_PIXELS:
            raise ValueError("La imagen es demasiado grande (%dx%d)." % (w, h))
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(surf)
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
        cr.paint()
        surf.flush()
        self.surface = surf
        self.set_size_request(w, h)
        self.history.clear()
        self.filename = path
        self.dirty = False
        self.queue_draw()


class PaintWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Ocelote Paint")
        self.set_default_size(1100, 720)
        self.set_icon_name("ocelote-paint")
        self.connect("delete-event", self.on_close)
        self.connect("key-press-event", self.on_key)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        root.set_border_width(6)
        self.add(root)

        # barra superior
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for label, cb in (("Nuevo", self.act_new), ("Abrir", self.act_open), ("Guardar", self.act_save),
                          ("Deshacer", self.act_undo), ("Rehacer", self.act_redo)):
            b = Gtk.Button(label=label)
            b.connect("clicked", cb)
            top.pack_start(b, False, False, 0)
        self.status = Gtk.Label(label="")
        top.pack_end(self.status, False, False, 6)
        root.pack_start(top, False, False, 0)

        # centro: herramientas + lienzo
        mid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        root.pack_start(mid, True, True, 0)
        tools = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        mid.pack_start(tools, False, False, 0)

        self.canvas = Canvas(on_motion=self.on_canvas_motion, on_pick=self.set_color)
        first = None
        for key, label in TOOLS:
            if first is None:
                btn = Gtk.RadioButton.new_with_label(None, label)
                first = btn
            else:
                btn = Gtk.RadioButton.new_with_label_from_widget(first, label)
            btn.set_mode(False)
            btn.connect("toggled", self.on_tool_toggled, key)
            if key == "pincel":
                btn.set_active(True)
            tools.pack_start(btn, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.add(self.canvas)
        mid.pack_start(scroll, True, True, 0)

        # barra inferior: paleta, color, grosor, relleno
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        root.pack_start(bottom, False, False, 0)
        for hx in PALETTE:
            b = Gtk.Button()
            b.set_size_request(24, 24)
            prov = Gtk.CssProvider()
            prov.load_from_data(("button { background-image: none; background-color: %s; "
                                 "min-width: 20px; min-height: 20px; padding: 0; }" % hx).encode())
            b.get_style_context().add_provider(prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            b.connect("clicked", lambda _b, h=hx: self.set_color(hex_to_rgb(h)))
            bottom.pack_start(b, False, False, 0)
        self.color_btn = Gtk.ColorButton()
        self.color_btn.connect("color-set", self.on_color_set)
        bottom.pack_start(self.color_btn, False, False, 8)
        bottom.pack_start(Gtk.Label(label="Grosor"), False, False, 0)
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 60, 1)
        scale.set_value(self.canvas.size)
        scale.set_size_request(160, -1)
        scale.connect("value-changed", lambda s: setattr(self.canvas, "size", s.get_value()))
        bottom.pack_start(scale, False, False, 0)
        fill = Gtk.CheckButton(label="Formas rellenas")
        fill.connect("toggled", lambda c: setattr(self.canvas, "filled", c.get_active()))
        bottom.pack_start(fill, False, False, 8)

        self.set_color((0.0, 0.0, 0.0))
        self.update_title()
        self.show_all()

    # ---------- utilidades ----------
    def update_title(self):
        name = os.path.basename(self.canvas.filename) if self.canvas.filename else "Sin título"
        mark = "*" if self.canvas.dirty else ""
        title = "%s%s - Ocelote Paint" % (mark, name)
        if title != self.get_title():
            self.set_title(title)

    def message(self, text, kind=Gtk.MessageType.ERROR):
        d = Gtk.MessageDialog(transient_for=self, modal=True, message_type=kind,
                              buttons=Gtk.ButtonsType.OK, text=text)
        d.run()
        d.destroy()

    def confirm_discard(self):
        if not self.canvas.dirty:
            return True
        d = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                              buttons=Gtk.ButtonsType.NONE, text="Hay cambios sin guardar. ¿Descartarlos?")
        d.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        d.add_button("Descartar", Gtk.ResponseType.OK)
        resp = d.run()
        d.destroy()
        return resp == Gtk.ResponseType.OK

    def set_color(self, rgb):
        self.canvas.color = tuple(rgb)
        self.color_btn.set_rgba(Gdk.RGBA(rgb[0], rgb[1], rgb[2], 1.0))

    # ---------- señales ----------
    def on_tool_toggled(self, btn, key):
        if btn.get_active():
            self.canvas.tool = key

    def on_color_set(self, btn):
        c = btn.get_rgba()
        self.canvas.color = (c.red, c.green, c.blue)

    def on_canvas_motion(self, x, y):
        self.status.set_text("%d, %d px" % (x, y))
        self.update_title()

    def on_key(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            k = (Gdk.keyval_name(event.keyval) or "").lower()
            if k == "z":
                self.act_undo()
                return True
            if k == "y":
                self.act_redo()
                return True
            if k == "s":
                self.act_save()
                return True
            if k == "o":
                self.act_open()
                return True
            if k == "n":
                self.act_new()
                return True
        return False

    def on_close(self, widget, event):
        if self.confirm_discard():
            Gtk.main_quit()
            return False
        return True

    # ---------- acciones ----------
    def act_new(self, *_):
        if self.confirm_discard():
            self.canvas.filename = None
            self.canvas.new_surface(DEFAULT_W, DEFAULT_H)
            self.update_title()

    def act_undo(self, *_):
        self.canvas.undo()
        self.update_title()

    def act_redo(self, *_):
        self.canvas.redo()
        self.update_title()

    def file_dialog(self, title, action, label):
        d = Gtk.FileChooserDialog(title=title, transient_for=self, action=action)
        d.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        d.add_button(label, Gtk.ResponseType.OK)
        flt = Gtk.FileFilter()
        flt.set_name("Imágenes (PNG, JPG, BMP)")
        for pat in ("*.png", "*.jpg", "*.jpeg", "*.bmp"):
            flt.add_pattern(pat)
        d.add_filter(flt)
        return d

    def act_open(self, *_):
        if not self.confirm_discard():
            return
        d = self.file_dialog("Abrir imagen", Gtk.FileChooserAction.OPEN, "Abrir")
        if d.run() == Gtk.ResponseType.OK:
            path = d.get_filename()
            d.destroy()
            try:
                self.canvas.open_image(path)
            except Exception as e:  # noqa: BLE001
                self.message("No se pudo abrir la imagen:\n%s" % e)
            self.update_title()
        else:
            d.destroy()

    def act_save(self, *_):
        path = self.canvas.filename
        if not path or not path.lower().endswith(".png"):
            d = self.file_dialog("Guardar imagen", Gtk.FileChooserAction.SAVE, "Guardar")
            d.set_do_overwrite_confirmation(True)
            d.set_current_name("dibujo.png")
            if d.run() != Gtk.ResponseType.OK:
                d.destroy()
                return
            path = d.get_filename()
            d.destroy()
            if not path.lower().endswith(".png"):
                path += ".png"
        try:
            self.canvas.save_png(path)
        except Exception as e:  # noqa: BLE001
            self.message("No se pudo guardar:\n%s" % e)
        self.update_title()


def main():
    PaintWindow()
    Gtk.main()


if __name__ == "__main__":
    main()
