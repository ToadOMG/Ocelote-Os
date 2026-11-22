#!/usr/bin/env python3
"""Escudo en tiempo real de Ocelote: revisa Descargas y Escritorio cada 5 s (consumo minimo)."""
import fcntl
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine  # noqa: E402


def main():
    try:
        os.nice(15)
    except OSError:
        pass
    lock_dir = os.path.join(os.path.expanduser("~"), ".cache")
    os.makedirs(lock_dir, exist_ok=True)
    lock = open(os.path.join(lock_dir, "ocelote-escudo-vigia.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return  # ya hay un vigia corriendo
    firmas = engine.cargar_firmas()
    estado = {"pendientes": {}, "vistos": set()}
    while True:
        for h in engine.vigilar_una_vez(estado, engine.carpetas_vigiladas(), firmas):
            subprocess.Popen(["ocelote-escudo", "--alerta", h.ruta], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
        time.sleep(5)


if __name__ == "__main__":
    main()
