# Estación terrena: decisiones

Del grilling del 2026-11-05 al 2026-11-07. Los requisitos se citan por su código
del Anexo A v2 del certamen.

## Decidido

| Tema | Decisión | Por qué |
|---|---|---|
| Alcance para la PDR | Prototipo que funciona con datos simulados, sin radio | Sus capturas van en el punto 74; el formato todavía no existe |
| Plataforma | Python + PySide6 + pyqtgraph. Respaldo: web local con FastAPI | Lo usaron MetalHawk, Vortex y SEDS ITBA |
| Repo | Uno solo para todo el código del CanSat | El formato de telemetría es compartido y vive en un solo lugar |
| Formato | `protocolo/telemetria.toml` como única fuente; la GCS lo lee al arrancar y un script genera el `telemetria.h` de la Pico | Un cambio de campo se hace en un archivo, sin tocar código |
| Paquete (versión 1, #10) | 61 B binarios, big-endian: cabecera primaria CCSDS 133.0-B-2 (APID 106, contador de 14 bits = F1), 1 B de versión del formato, 52 B de campos enteros con divisor y CRC-16/CCITT-FALSE. Un solo paquete a 1 Hz; sin dato = centinela del tipo; campos nuevos al final y sube la versión | Entra a SF9 con margen para un telecomando en el mismo segundo; el APID separa nuestros paquetes de los de otros equipos (X2) |
| Clasificación de cada línea del puente | En orden: forma inválida → descartado; largo ≠ 61 → ajeno; CRC inválido → descartado; otro APID o tipo TC → ajeno; versión desconocida → descartado; si no, recibido. Todo va al log crudo | Recibidos, perdidos y descartados en pantalla (G14, F1); lo ajeno no ensucia los conteos |
| Perdidos | `(actual − anterior − 1) mod 16384`; un salto hacia adelante de más de 8 000 es un contador reiniciado, sin perdidos; contador repetido con datos distintos se acepta y se marca, idéntico se ignora | La vuelta de 16 383 a 0 no cuenta como pérdida |
| Módulos | Fuente → Decodificador → Estado de misión → GUI y Registro | Sólo el decodificador conoce el formato; el estado se testea sin Qt |
| Lectura serie | `QSerialPort` con `readyRead`, sin hilos | Sin hilos no hay carreras; el simulador emite la misma señal |
| Entorno | `uv` con `pyproject.toml` y `uv.lock` | La notebook del lanzamiento se reinstala con un comando, idéntica a la probada |
| Tests | pytest, test primero, sobre el decodificador, el estado de misión y la validez del `.toml`. La GUI no se testea | Los conteos de G14 y de perdidos (F1) son donde se esconde el error que nadie ve |
| GitHub | Issues, ramas cortas y PR a `main`; CI con `ruff` y pytest; sin aprobación obligatoria | No frenarse antes de la PDR si no hay quien revise |
| Empaquetado | `.exe` con PyInstaller, generado por el CI en cada tag `v*`. No para la PDR | El día del lanzamiento no se depende de internet ni de `uv` |
| Heltec de tierra | Puente transparente que agrega el RSSI y el SNR | Toda la lógica en la notebook; un cambio de formato no reflashea la Heltec |
| Registro | CSV por paquete, con escritura forzada, en el disco y en el pendrive de etiqueta `AVUTARDO`, más log crudo. Sin pendrive, aviso en rojo y se sigue | G2 se cumple durante todo el vuelo, no sólo al final |
| CSV | Encabezado `campo [unidad]`, nombre con la fecha y hora UTC del arranque, hora UTC de recepción en cada fila, punto decimal | G3, G6; el log crudo permite rehacer el CSV |
| Telecomandos | Botones para los fijos más una línea de texto; eco en la telemetría y verificación por el efecto; confirmación para los comandos que hacen daño mandados por error en vuelo (comandos con confirmación) | El eco queda en el CSV como prueba para el jurado |
| Simulador | Dentro de la app, con el perfil del Prometeo (673 m, eyección a los 12 s, 15 m/s, v₂ como parámetro entre 2.5 y 4.3 m/s); arma paquetes y los pasa por el decodificador | El decodificador y los contadores trabajan desde el primer día |
| Licencia | MIT (confirmada el 2026-11-07) | Que otro equipo pueda reutilizarlo |
| Resolución de diseño | Mínimo de 1366×768 píxeles **lógicos** (después de la escala de Windows), sin elegir todavía la notebook (#4) | Entra en cualquier notebook a su escala de fábrica; bajar la escala para ganar lugar achica la letra real y va contra G12 |
| Ventana | Pantalla completa por defecto; F11 la pasa a ventana. Una sola pantalla | Unos 80 px más de alto a 1366×768; en el campo puede no haber segunda pantalla |
| Pantallas grandes | Sin scroll y con letra fija en 14 pt: lo que sobra lo toman los gráficos. Por debajo del mínimo, aviso y se sigue. Sin zoom de letra para la PDR | Un scroll esconde datos igual que una pestaña (G13) |
| Capturas de la diap. 77 | A 1366×768 lógicos con el doble de píxeles (2732×1536) | El jurado ve lo que vuela, nítido en una diapositiva 16:9 |
| Pantalla | Variante G2 del prototipo (#7): Vuelo y GPS alta a la izquierda, Energía en dos celdas, telecomandos y Recorrido en una columna derecha de 230 px; barra de fases con los cinco estados de STANDBY a LANDED y pie de estado | Sin pestañas (G13), 14 pt y fondo claro (G12), con 20 px de holgura a 1366 de ancho |
| Gráficos | Sin título ni leyenda; x, y, z en una línea de valores del color de su curva, que hace de leyenda; la unidad en el título de la tarjeta. Ventanas de 30, 60 y 120 s y Misión, arranca en 120 s; zoom sólo en Misión | Ganan alto los gráficos sin repetir la unidad |
| Recorrido | Mapa sin fondo, en metros desde el lanzamiento; en LANDED pasa una vez al QR con el enlace a Google Maps, con un botón Mapa/QR | Sin sitio definido no hay fondo que precargar; el QR acelera la recuperación |
| Velocidad vertical | Calculada en la GCS; recuadro verde dentro de la banda de la fase (C3, C4), rojo fuera y ámbar 5 s tras un cambio de estado | La banda va en el tooltip |
| Umbrales de la GUI | Fijos en el código: 3 s sin paquetes para mostrar el enlace cortado y 5 s de transición | No hay nada que configurar en el campo |

## Abierto

- **Fondo del mapa precargado** del campo de lanzamiento: después de la PDR,
  cuando esté definido el sitio.
- **Nombre legible por campo** en `telemetria.toml`: pregunta al equipo. (Los
  decimales del CSV ya salen del `divisor`.)
- **Notebook del lanzamiento:** 2 h de batería (G9) y 1366×768 lógicos o más a
  su escala de fábrica.
- **Disposición amplia** (vistas extra con 1920×1080 o más): después de la PDR,
  si aparece algo que valga la pena mostrar sólo en pantalla grande.
- **Zoom de letra** (Ctrl+ y Ctrl−, con piso en 14 pt): se reabre si en un
  ensayo a pleno sol los 14 pt no alcanzan.
- **Formato de los telecomandos y contenido del `eco_comando`:** #11. El campo
  ya tiene su lugar en el paquete (`reservado`).
- **Si las dos Heltec comparten firmware.** La línea del puente ya está fijada:
  `<hex>,<rssi>,<snr>`.
