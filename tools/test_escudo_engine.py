import os, sys, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config", "includes.chroot", "usr", "local", "lib", "ocelote-escudo"))
import engine

tmp = tempfile.mkdtemp()
os.environ["OCELOTE_ESCUDO_DATOS"] = os.path.join(tmp, "datos")
os.environ["OCELOTE_ESCUDO_CONFIG"] = os.path.join(tmp, "cfg")
try:
    firmas = engine.cargar_firmas([os.path.join(os.path.dirname(__file__), "..", "config", "includes.chroot", "usr", "share", "ocelote", "escudo", "firmas.txt")])
    assert len(firmas) == 3, firmas

    d = os.path.join(tmp, "carpeta"); os.makedirs(d)
    limpio = os.path.join(d, "nota.txt"); open(limpio, "w").write("hola")
    eicar = engine.crear_archivo_eicar(d)
    doble = os.path.join(d, "foto.jpg.exe"); open(doble, "wb").write(b"MZ")
    autor = os.path.join(d, "autorun.inf"); open(autor, "w").write("[autorun]\nopen=virus.exe\n")
    ok_exe = os.path.join(d, "instalador.exe"); open(ok_exe, "wb").write(b"MZ")
    # firma por hash (archivo grande con contenido propio)
    malo = os.path.join(d, "raro.bin"); open(malo, "wb").write(b"contenido-malicioso-de-prueba" * 500)
    import hashlib
    h = hashlib.sha256(open(malo, "rb").read()).hexdigest()
    firmas[h] = ("Prueba.Hash", "Troyano de prueba")

    assert engine.analizar_archivo(limpio, firmas) is None
    r = engine.analizar_archivo(eicar, firmas); assert r and r.nombre == "EICAR-Test-File"
    r = engine.analizar_archivo(doble, firmas); assert r and r.tipo == "Heurística"
    r = engine.analizar_archivo(autor, firmas); assert r and "autorun" in r.nombre
    assert engine.analizar_archivo(ok_exe, firmas) is None          # un .exe normal NO es sospechoso
    r = engine.analizar_archivo(malo, firmas); assert r and r.nombre == "Prueba.Hash"

    # escaneo de carpeta
    res = list(engine.escanear([d], firmas))
    archivos = [x for k, x in res if k == "archivo"]; halls = [x for k, x in res if k == "hallazgo"]
    assert len(archivos) == 6, len(archivos)
    assert sorted(h.nombre for h in halls) == sorted(["EICAR-Test-File", "Sospechoso: doble extensión", "Sospechoso: autorun.inf", "Prueba.Hash"])

    # cancelar
    n = 0
    for _ in engine.escanear([d], firmas, cancelar=lambda: True): n += 1
    assert n == 0

    # cofre
    dest = engine.mover_al_cofre(eicar, "EICAR-Test-File")
    assert not os.path.exists(eicar) and os.path.exists(dest)
    assert oct(os.stat(dest).st_mode & 0o777) == "0o600"
    items = engine.listar_cofre(); assert len(items) == 1
    # un escaneo no debe analizar el propio cofre
    assert not [1 for k, x in engine.escanear([engine.datos_dir()], firmas) if k == "hallazgo"]
    engine.restaurar(items[0]); assert os.path.exists(eicar) and not engine.listar_cofre()
    dest = engine.mover_al_cofre(eicar, "x"); engine.eliminar_del_cofre(engine.listar_cofre()[0])
    assert not os.path.exists(dest) and not engine.listar_cofre()

    # vigia: necesita dos pasadas (archivo estable) y no repite
    vig = os.path.join(tmp, "descargas"); os.makedirs(vig)
    estado = {"pendientes": {}, "vistos": set()}
    engine.crear_archivo_eicar(vig)
    assert engine.vigilar_una_vez(estado, [vig], firmas) == []       # 1a pasada: aun pendiente
    hs = engine.vigilar_una_vez(estado, [vig], firmas); assert len(hs) == 1 and hs[0].nombre == "EICAR-Test-File"
    assert engine.vigilar_una_vez(estado, [vig], firmas) == []       # ya visto
    # config
    engine.guardar_config({"vigia": True}); assert engine.leer_config() == {"vigia": True}
    print("OK todas las pruebas del motor")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
