#!/usr/bin/env bash
# Ocelote OS 0.4 - script de construccion de la ISO
# Uso:  sudo ./build.sh            (version base, ligera)
#       sudo WITH_WINE=1 ./build.sh   (incluye Wine para abrir .exe)
#       sudo WITH_FIRMWARE=1 ./build.sh   (para instalar en un PC real)
set -euo pipefail

# ====== AJUSTES (cambialos si quieres) ======
export LOCALE="${LOCALE:-es_MX.UTF-8}"
export KEYMAP="${KEYMAP:-latam}"
export TIMEZONE="${TIMEZONE:-America/Mexico_City}"
WITH_WINE="${WITH_WINE:-0}"
export WITH_FIRMWARE="${WITH_FIRMWARE:-0}"   # 1 = incluir firmware para PCs reales (ISO mas grande)
# ============================================

if [ "$(id -u)" -ne 0 ]; then
  echo "Ejecuta con sudo:  sudo ./build.sh"; exit 1
fi

cd "$(dirname "$0")"

echo "==> Instalando herramientas de construccion (necesita internet)..."
apt-get update
apt-get install -y live-build debootstrap debian-archive-keyring xorriso \
  squashfs-tools mtools dosfstools isolinux syslinux-common \
  grub-pc-bin grub-efi-amd64-bin git

echo "==> Preparando permisos..."
chmod +x auto/* config/hooks/live/*.hook.chroot config/includes.chroot/usr/local/bin/* 2>/dev/null || true

if [ "$WITH_WINE" = "1" ]; then
  echo "==> Wine activado"
  printf '# Wine (opcional)\nwine\n' > config/package-lists/wine.list.chroot
else
  rm -f config/package-lists/wine.list.chroot
fi

echo "==> Limpiando construcciones anteriores..."
lb clean --purge >/dev/null 2>&1 || true

echo "==> Configurando..."
lb config

echo "==> Construyendo (puede tardar 20-60 min). El registro queda en build.log"
lb build 2>&1 | tee build.log

mkdir -p salida
cp -v ./*.iso salida/
echo "==> Comprobando que la ISO tenga sector de arranque..."
for iso in salida/*.iso; do
  echo "Archivo: $iso ($(du -h "$iso" | cut -f1))" | tee -a build.log
  out=$(xorriso -indev "$iso" -report_el_torito plain 2>&1 || true)
  echo "$out" | tee -a build.log
  case "$out" in
    *"El Torito boot img"*) echo "OK: la ISO tiene arranque." ;;
    *) echo "ADVERTENCIA: no se detecto arranque en la ISO (revisa build.log)." ;;
  esac
  sha256sum "$iso" | tee -a build.log
done
echo
echo "Listo. Tu ISO esta en: $(pwd)/salida/"
