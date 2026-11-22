"""Motor de Ocelote Escudo: deteccion basica, cofre (cuarentena) y configuracion.

No es un antivirus profesional: detecta el archivo de prueba EICAR, firmas SHA-256
de una lista local y algunos trucos tipicos (doble extension, autorun.inf).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass

VERSION_PROGRAMA = "0.1"
VERSION_FIRMAS = "2026-11-21 (basicas)"
EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
MAX_EICAR_BYTES = 4096            # el archivo EICAR real mide menos de 128 bytes
MAX_HASH_BYTES = 20 * 1024 * 1024  # no se calcula hash de archivos mas grandes (evita lentitud)
FIRMAS_SISTEMA = "/usr/share/ocelote/escudo/firmas.txt"
EXCLUIR_DIRS = {".cache", "node_modules", "__pycache__", ".wine", "proc", "sys", "dev"}
DOBLE_EXT = re.compile(
    r"\.(jpe?g|png|gif|bmp|pdf|docx?|xlsx?|pptx?|txt|mp3|mp4|zip|rar)\.(exe|scr|pif|bat|cmd|com|vbs|js|jar|msi)$",
    re.IGNORECASE)


@dataclass
class Hallazgo:
    ruta: str
    nombre: str      # nombre de la amenaza
    tipo: str        # tipo
    motivo: str = ""


# ---------------------------------------------------------------- rutas / config
def datos_dir():
    return os.environ.get("OCELOTE_ESCUDO_DATOS") or os.path.join(os.path.expanduser("~"), ".local", "share", "ocelote-escudo")


def cofre_dir():
    return os.path.join(datos_dir(), "cofre")


def config_path():
    base = os.environ.get("OCELOTE_ESCUDO_CONFIG") or os.path.join(os.path.expanduser("~"), ".config", "ocelote")
    return os.path.join(base, "escudo.json")


def leer_config():
    try:
        with open(config_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def guardar_config(cfg):
    p = config_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cfg, f)


# ---------------------------------------------------------------- firmas
def cargar_firmas(rutas=None):
    if rutas is None:
        rutas = [FIRMAS_SISTEMA, os.path.join(os.path.dirname(config_path()), "escudo-firmas.txt")]
    firmas = {}
    for r in rutas:
        try:
            with open(r, encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if not linea or linea.startswith("#"):
                        continue
                    partes = linea.split("\t") if "\t" in linea else linea.split(None, 2)
                    if len(partes) >= 2 and re.fullmatch(r"[0-9a-fA-F]{64}", partes[0]):
                        nombre = partes[1]
                        tipo = partes[2] if len(partes) > 2 else "Malware"
                        firmas[partes[0].lower()] = (nombre, tipo)
        except OSError:
            continue
    return firmas


def sha256_de(ruta, limite=MAX_HASH_BYTES):
    try:
        if os.path.getsize(ruta) > limite:
            return None
        h = hashlib.sha256()
        with open(ruta, "rb") as f:
            for bloque in iter(lambda: f.read(1024 * 256), b""):
                h.update(bloque)
        return h.hexdigest()
    except OSError:
        return None


# ---------------------------------------------------------------- analisis
def analizar_archivo(ruta, firmas):
    """Devuelve un Hallazgo o None."""
    try:
        if os.path.islink(ruta) or not os.path.isfile(ruta):
            return None
        tam = os.path.getsize(ruta)
    except OSError:
        return None
    base = os.path.basename(ruta)

    if tam <= MAX_EICAR_BYTES:
        try:
            with open(ruta, "rb") as f:
                if EICAR in f.read(MAX_EICAR_BYTES):
                    return Hallazgo(ruta, "EICAR-Test-File", "Archivo de prueba (no es un virus)", "Cadena EICAR")
        except OSError:
            return None

    if base.lower() == "autorun.inf" and tam < 65536:
        try:
            with open(ruta, "rb") as f:
                txt = f.read().lower()
            if b"open=" in txt or b"shellexecute" in txt:
                return Hallazgo(ruta, "Sospechoso: autorun.inf", "Heurística", "Ejecuta programas al conectar un disco")
        except OSError:
            pass

    if DOBLE_EXT.search(base):
        return Hallazgo(ruta, "Sospechoso: doble extensión", "Heurística",
                        "Parece un documento pero es un programa")

    if firmas:
        h = sha256_de(ruta)
        if h and h in firmas:
            nombre, tipo = firmas[h]
            return Hallazgo(ruta, nombre, tipo, "Coincide con una firma")
    return None


def escanear(raices, firmas, cancelar=lambda: False):
    """Generador: produce ('archivo', ruta) por cada archivo y ('hallazgo', Hallazgo)."""
    cofre = os.path.abspath(cofre_dir())
    for raiz in raices:
        if os.path.isfile(raiz):
            yield ("archivo", raiz)
            h = analizar_archivo(raiz, firmas)
            if h:
                yield ("hallazgo", h)
            continue
        for dirpath, dirnames, filenames in os.walk(raiz, followlinks=False):
            if cancelar():
                return
            if os.path.abspath(dirpath).startswith(cofre):
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if d not in EXCLUIR_DIRS]
            for nombre in filenames:
                if cancelar():
                    return
                ruta = os.path.join(dirpath, nombre)
                yield ("archivo", ruta)
                h = analizar_archivo(ruta, firmas)
                if h:
                    yield ("hallazgo", h)


# ---------------------------------------------------------------- cofre (cuarentena)
def _indice_path():
    return os.path.join(cofre_dir(), "indice.json")


def _leer_indice():
    try:
        with open(_indice_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def _guardar_indice(items):
    os.makedirs(cofre_dir(), mode=0o700, exist_ok=True)
    with open(_indice_path(), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)


def mover_al_cofre(ruta, amenaza=""):
    os.makedirs(cofre_dir(), mode=0o700, exist_ok=True)
    destino = os.path.join(cofre_dir(), "%d_%s.cofre" % (time.time() * 1000, os.path.basename(ruta)))
    shutil.move(ruta, destino)
    os.chmod(destino, 0o600)  # sin permiso de ejecucion
    items = _leer_indice()
    items.append({"original": ruta, "cofre": destino, "amenaza": amenaza, "fecha": time.strftime("%Y-%m-%d %H:%M")})
    _guardar_indice(items)
    return destino


def listar_cofre():
    return [i for i in _leer_indice() if os.path.exists(i["cofre"])]


def restaurar(item):
    os.makedirs(os.path.dirname(item["original"]) or ".", exist_ok=True)
    shutil.move(item["cofre"], item["original"])
    _guardar_indice([i for i in _leer_indice() if i["cofre"] != item["cofre"]])


def eliminar_del_cofre(item):
    try:
        os.remove(item["cofre"])
    except OSError:
        pass
    _guardar_indice([i for i in _leer_indice() if i["cofre"] != item["cofre"]])


def eliminar_archivo(ruta):
    os.remove(ruta)


# ---------------------------------------------------------------- vigia (escudo en tiempo real)
def vigilar_una_vez(estado, carpetas, firmas):
    """Una pasada del vigia. 'estado' = {'pendientes': {}, 'vistos': set()}.
    Un archivo se analiza cuando su tamano no cambia entre dos pasadas (descarga terminada)."""
    hallazgos = []
    for carpeta in carpetas:
        try:
            entradas = list(os.scandir(carpeta))
        except OSError:
            continue
        for e in entradas:
            try:
                if not e.is_file(follow_symlinks=False):
                    continue
                st = e.stat(follow_symlinks=False)
            except OSError:
                continue
            clave = (e.path, st.st_mtime_ns, st.st_size)
            if clave in estado["vistos"]:
                continue
            previo = estado["pendientes"].get(e.path)
            if previo == (st.st_mtime_ns, st.st_size):
                estado["vistos"].add(clave)
                estado["pendientes"].pop(e.path, None)
                h = analizar_archivo(e.path, firmas)
                if h:
                    hallazgos.append(h)
            else:
                estado["pendientes"][e.path] = (st.st_mtime_ns, st.st_size)
    return hallazgos


def crear_archivo_eicar(carpeta):
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "prueba-eicar.txt")
    with open(ruta, "wb") as f:
        f.write(EICAR)
    return ruta


def carpeta_xdg(nombre, alternativas=()):
    """Carpeta del usuario (DOWNLOAD, DESKTOP...). Nunca devuelve la carpeta personal a secas."""
    home = os.path.expanduser("~")
    try:
        out = subprocess.run(["xdg-user-dir", nombre], capture_output=True, text=True, timeout=3).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        out = ""
    if out and os.path.abspath(out) != os.path.abspath(home) and os.path.isdir(out):
        return out
    for alt in alternativas:
        ruta = os.path.join(home, alt)
        if os.path.isdir(ruta):
            return ruta
    return None


def carpetas_vigiladas():
    c = [carpeta_xdg("DOWNLOAD", ("Descargas", "Downloads")), carpeta_xdg("DESKTOP", ("Escritorio", "Desktop"))]
    return [x for x in c if x]
