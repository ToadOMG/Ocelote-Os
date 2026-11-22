"""Logica de Ocelote Paint sin dependencias graficas (se puede probar sola)."""


def flood_fill(buf, width, height, stride, x, y, color):
    """Relleno por inundacion sobre un bufer ARGB32 de cairo (bytes B,G,R,A).

    color = (r, g, b, a) con valores 0-255. Devuelve cuantos pixeles cambio.
    """
    x, y = int(x), int(y)
    if not (0 <= x < width and 0 <= y < height):
        return 0
    r, g, b, a = color
    if a != 255:  # cairo guarda los colores premultiplicados por alfa
        r, g, b = r * a // 255, g * a // 255, b * a // 255
    new = bytes((b, g, r, a))
    off = y * stride + x * 4
    target = bytes(buf[off:off + 4])
    if target == new:
        return 0
    stack = [(x, y)]
    count = 0
    while stack:
        cx, cy = stack.pop()
        row = cy * stride
        lx = cx
        while lx >= 0 and buf[row + lx * 4:row + lx * 4 + 4] == target:
            lx -= 1
        lx += 1
        rx = cx
        while rx < width and buf[row + rx * 4:row + rx * 4 + 4] == target:
            rx += 1
        if rx <= lx:
            continue
        buf[row + lx * 4:row + rx * 4] = new * (rx - lx)
        count += rx - lx
        for ny in (cy - 1, cy + 1):
            if 0 <= ny < height:
                nrow = ny * stride
                span = False
                for i in range(lx, rx):
                    if buf[nrow + i * 4:nrow + i * 4 + 4] == target:
                        if not span:
                            stack.append((i, ny))
                            span = True
                    else:
                        span = False
    return count


class History:
    """Pila de deshacer/rehacer con limite de memoria."""

    def __init__(self, max_bytes=64 * 1024 * 1024):
        self.undo_stack = []
        self.redo_stack = []
        self.max_bytes = max_bytes

    def _size(self):
        return sum(len(s[2]) for s in self.undo_stack) + sum(len(s[2]) for s in self.redo_stack)

    def push(self, snapshot):
        """Guarda el estado ANTES de un cambio. snapshot = (ancho, alto, bytes)."""
        self.undo_stack.append(snapshot)
        self.redo_stack.clear()
        while len(self.undo_stack) > 1 and self._size() > self.max_bytes:
            self.undo_stack.pop(0)

    def undo(self, current):
        if not self.undo_stack:
            return None
        self.redo_stack.append(current)
        return self.undo_stack.pop()

    def redo(self, current):
        if not self.redo_stack:
            return None
        self.undo_stack.append(current)
        return self.redo_stack.pop()

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()

    def can_undo(self):
        return bool(self.undo_stack)

    def can_redo(self):
        return bool(self.redo_stack)
