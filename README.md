# Ocelote OS 0.1 (nombre clave provisional)

Sistema liviano basado en **Debian 13 (trixie) + XFCE**, pensado para probar en VirtualBox.
Estilo visual tipo Mac OS X (barra superior translucida + dock) y atajos tipo Windows.

> Esta es una version de PRUEBA. La receta no ha sido probada todavia: es normal que
> haya que ajustar cosas despues del primer arranque.

## Como construir la ISO
Necesitas un Debian o Ubuntu (puede ser una VM en VirtualBox con ~25 GB libres) con internet.

    unzip ocelote-os-0.1.zip && cd ocelote-os
    sudo ./build.sh                # version ligera
    sudo WITH_WINE=1 ./build.sh    # con Wine para abrir .exe (ISO mas grande)

Al terminar, la ISO queda en `salida/`. Si algo falla, el registro esta en `build.log`
(pegame las ultimas ~40 lineas y lo arreglo).

Idioma/teclado/zona horaria: se cambian al inicio de `build.sh`
(por defecto es_MX, teclado latam, America/Mexico_City).

## Opcion sin instalar nada: construir en GitHub (gratis)
1. Crea un repositorio **publico** en github.com y sube todo el contenido de esta carpeta
   (incluida la carpeta `.github`).
2. Pestana **Actions** > "Construir ISO Ocelote" > **Run workflow**.
3. Cuando termine (30-60 min), en la ejecucion baja el artefacto `ocelote-os-iso`
   (viene en .zip; dentro esta la .iso).

## Maquina virtual en VirtualBox
- Tipo: Linux / Debian (64-bit)
- RAM: 2048 MB, CPUs: 2
- Pantalla: controlador grafico **VMSVGA**, memoria de video 128 MB
- Disco: no hace falta (arranca en modo live desde la ISO)
- Almacenamiento: monta la ISO en la unidad optica y arranca

Usuario: `ocelote`  |  contrasena: `live`  (entra solo, sin pedir clave)

## Que incluye
- Barra superior con menu "Ocelote" (hace de menu Inicio), sonido, reloj
- Dock Plank abajo (Archivos, Firefox, Terminal, Editor, Ajustes)
- Botones de ventana a la izquierda (cerrar/minimizar/maximizar) estilo Mac
- Atajos tipo Windows: Super+E explorador, Super+R ejecutar, Super+D escritorio,
  Super+L bloquear, Ctrl+Shift+Esc administrador de tareas, Super+flechas acomodar ventana
- Wine opcional para programas .exe

## Pendiente para proximas versiones
- Tema mas fiel a Leopard (botones Aqua brillantes, dock 3D de cristal)
- Menu de Apple propio, fondo y sonidos propios
- Instalador a disco
