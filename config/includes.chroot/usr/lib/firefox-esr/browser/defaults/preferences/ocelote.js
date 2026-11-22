// Ajustes de Ocelote OS para equipos con poca RAM / maquinas virtuales
pref("dom.ipc.processCount", 2);
pref("dom.ipc.processPrelaunch.enabled", false);
pref("browser.tabs.unloadOnLowMemory", true);
pref("layers.acceleration.disabled", true);
pref("gfx.canvas.accelerated", false);
pref("media.hardware-video-decoding.enabled", false);
pref("browser.cache.disk.enable", false);
pref("browser.cache.memory.enable", true);
pref("browser.cache.memory.capacity", 65536);
pref("browser.sessionstore.interval", 60000);
pref("general.smoothScroll", false);
pref("app.normandy.enabled", false);
pref("extensions.pocket.enabled", false);
