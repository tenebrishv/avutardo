# Qué mostraron los PDR ganadores en "GCS Software"

Investigación para la issue #3. Alimenta el prototipo de la pantalla de la
estación terrena, cuyas capturas van en la diapositiva "GCS Software" de
nuestra PDR (punto 74, diap. 77).

## Fuente y alcance

- Los diez PDF de `9. Ganadores anteriores 2026/` de la biblioteca del equipo:
  PDR y CDR de los cinco ganadores de la **CanSat Competition 2026** (la
  internacional, no el certamen de la CONAE). Son las diapositivas tal como
  las entregaron, sin anotaciones: **no hay observaciones del jurado** en
  ninguno (se revisaron las anotaciones de los diez PDF; hay cero).
- Los números de página citados son los del PDF, que coinciden con el número
  impreso al pie de cada diapositiva.
- El texto se sacó con PyMuPDF y cada pantalla se miró renderizada; las
  descripciones de distribución salen de mirar la imagen, no del texto.
- En la guía de la competencia internacional los requisitos de la pantalla
  están numerados distinto que en nuestro Anexo A v2: lo que para nosotros es
  **G12** (legible a pleno sol) y **G13** (sin pestañas), en las tablas de
  cumplimiento de los ganadores figura como **G14** y **G15**, con el mismo
  texto ("larger fonts (14 point minimum), bold plot traces and axes, and a
  dark text on light background theme"; "Tabs are not allowed").
- **No se incluyen recortes de las capturas.** Son diapositivas de otros
  equipos y este repo va a ser público; en vez de copiarlas, se describen y se
  cita la página. Para verlas, abrir el PDF de la biblioteca en la página
  indicada.

Qué pide la plantilla en esa diapositiva (punto 74, según `puntos.md` de la
skill `pdr-punto`): prototipos de la pantalla de telemetría, paquetes COTS,
diseño del graficado en tiempo real, cómo se transmite y verifica el comando
de calibración, registro de la telemetría y presentación al jurado, y creación
del `.csv`. Todos los ganadores siguieron ese orden de subtítulos casi al pie
de la letra.

## Resumen por equipo

| Equipo | Págs. "GCS Software" (PDR) | Diap. | Capturas de pantalla | Tecnología | Tipo de captura |
|---|---|---|---|---|---|
| 1043 Daedalus (Tailandia) | 129–137 | 9 | 4 (pantalla completa 1, gráficos 1, panel de comandos 2) | FastAPI + ECharts, web local | Mockup funcionando con datos ficticios |
| 1093 Vortex (UAH, EE. UU.) | 243–245 | 3 | 1 (pantalla completa) | PyQt5 + pyqtgraph | Maqueta vacía, sin datos |
| 1064 Bamantara EEPISAT (Indonesia) | 135–138 | 4 | 3 (dos mitades anotadas + vista completa) | Flutter + fl_chart | Mockup con datos ficticios |
| 1094 MetalHawk (UAH, EE. UU.) | 181–182 | 2 | 1 (pantalla completa) | PySide6 + pyqtgraph | App real con senoidales de prueba |
| 1081 SEDS ITBA (Argentina) | 137–144 | 8 | 3 (un gráfico suelto, pantalla completa, la misma con el panel de comandos resaltado) | PyQt6 + pyqtgraph | Mockup con datos ficticios |

### 1043 Daedalus — PDR págs. 129–137

- **Capturas.** Pág. 129: los cuatro gráficos solos (altitud grande arriba;
  debajo, en fila, "Power System" con tensión y corriente, aceleración X/Y/Z
  en m/s² y giróscopo X/Y/Z en °/s). Pág. 131: la pantalla completa. Págs. 132
  y 134: recortes del panel "Telemetry Control & Logs" (el desplegable de
  comandos abierto, y el log con paquetes).
- **Distribución (pág. 131).** Página web en dos columnas bajo una franja
  superior:
  - Franja superior: estado de vuelo en grande ("ASCENT"), altitud en grande,
    modo, satélites GPS, una brújula, paquetes recibidos y perdidos, hora UTC y
    tiempo de misión, y botones "Log Folder" y "Run Sim".
  - Columna izquierda: los cuatro gráficos de la pág. 129 y, debajo, "Key
    Values" en tarjetas (temperatura, presión, tensión, corriente, giro y
    aceleración con unidad).
  - Columna derecha: mapa (Leaflet) con la posición GPS, el botón "Start
    Mission" y un reloj "T+ 00:00:05"; debajo, el panel de comandos con un
    desplegable de comandos rápidos (CX,ON; CAL; SIM,ENABLE…), una línea de
    texto con botón "Send", el último comando con su eco ("CMD_OK") y un log
    de texto con una línea resumida por paquete.
- **G12/G13.** En la tabla de cumplimiento dice "Comply" para los dos y remite
  a la pág. 131 (pág. 168). En la pág. 124 promete "Outdoor-optimized UI —
  High contrast, 14pt+ fonts". La captura tiene fondo claro y una sola vista
  sin pestañas, pero los trazos son finos, con relleno de área, y la letra de
  ejes y tarjetas es claramente chica; hay un botón "Theme", así que el tema
  claro sería uno de dos.
- **Texto que acompaña.** Viñetas cortas debajo de cada captura: "Plot using
  Echarts", ventana deslizante FIFO para que el navegador no se ponga lento en
  misiones largas, comandos en una cola asincrónica para que la interfaz no
  se congele, doble registro (crudo y CSV), y un botón que abre la carpeta de
  registros para los jueces (pág. 135). El CSV arma su encabezado desde un
  `telemetry_config.json` y se fuerza a disco después de cada paquete (pág.
  136).
- **CDR (págs. 158–163).** Repite los mismos gráficos como "screen shots"
  (pág. 158) y suma tooltips al pasar el mouse.

### 1093 Vortex — PDR págs. 243–245

- **Capturas.** Una sola, en la pág. 243, de la pantalla entera.
- **Distribución.** Grilla fija de PyQt5 en una ventana:
  - Fila superior de tres campos anchos: "FSW State", "CMD Echo" y
    "Velocity (m/s)".
  - Columna izquierda: tabla de dos columnas nombre–valor (tiempo de misión,
    paquetes recibidos, paquetes perdidos, liberaciones, temperatura (°C),
    latitud (°N), longitud (°E), satélites) y debajo diez botones de comando
    en dos columnas (SIM Enable, SIM Activate, SIM Disable, CX On, CX Off,
    Calibrate, Set Time, Release, Egg Drop, ACS).
  - Resto: grilla de 3 × 2 con un mapa y cinco gráficos (altitud, tensión,
    corriente, aceleración, rotación), cada uno con título, eje "Time (s)" y
    eje vertical con la unidad entre paréntesis.
- **G12/G13.** Recuadro al pie de la propia captura: "**NOTE:** There are no
  tabs in the GCS display and all units are SI". Cumplimiento "Comply" con
  remisión a la pág. 243 (pág. 272). Fondo claro y títulos y rótulos de ejes
  grandes; los gráficos están vacíos (ejes de 0 a 1 de prueba), así que no se
  ven trazos.
- **Texto que acompaña (pág. 244).** Una lista que recorre los requisitos:
  "Required altitude, voltage, current, acceleration, and rotation graphs are
  included" y "Required mission time, received and lost packet counts,
  temperature, GPS position, and flight software state is included", más lo
  agregado (mapa, estados de liberación, satélites, eco, velocidad).
  Actualización a 1 Hz y los últimos diez puntos en cada gráfico (pág. 245).
- **CDR (págs. 131–134).** La misma pantalla con el mapa cambiado por una
  trayectoria 3D y un selector de puerto COM; mantiene la nota de "no tabs".

### 1064 Bamantara EEPISAT — PDR págs. 135–138

- **Capturas.** Tres: la mitad superior de la pantalla (pág. 136), la mitad
  inferior (pág. 137) y la vista completa reducida (pág. 138). Las dos
  primeras llevan flechas con el nombre de cada bloque al costado.
- **Distribución.** Página larga en vertical, de arriba abajo:
  - "Header" con el nombre de la estación y logos; "Status Bar" con equipo,
    tiempo de misión, modo, estado, eco, satélites, batería del CanSat y
    estado de la GCS.
  - Izquierda: "Serial Log Data" (texto crudo de los paquetes, con
    recibidos, válidos y corruptos o perdidos), "Command Box" (puerto,
    baudios, desplegable con el comando y línea de texto con "Send") y
    "Realtime Data Graph" con ocho mini gráficos (altitud, tensión,
    temperatura, presión, corriente, distancia al blanco, acelerómetro,
    giróscopo), cada uno con su último valor en una etiqueta.
  - Derecha: "CanSat Data" y valores del acelerómetro y el giróscopo, el mapa
    y una vista 3D del CanSat.
  - Abajo: "Mission Progress" (barra con las fases, de la plataforma al
    aterrizaje), "Data Table" con todos los paquetes en filas y "Footer" con
    datos de la notebook (hora, ubicación, CPU, batería).
- **G12/G13.** "Comply" con remisión a págs. 135–137 (pág. 170). Sin
  pestañas, pero la vista completa (pág. 138) es más alta que una pantalla, así
  que en la notebook habría que desplazarse: eso cumple la letra de G13 pero
  no su intención ("todos los datos a la vez"). El fondo es beige con letra
  chica y gráficos muy pequeños. El sol sólo aparece en la pág. 132, y como
  problema de temperatura: una cubierta sobre su "cyberdeck" portátil para
  que no se recaliente.
- **Texto que acompaña.** La pág. 135 es una tabla de dos columnas con un
  párrafo por subtítulo de la plantilla (prototipo, COTS, graficado,
  comandos, registro, CSV, simulación). Las capturas no llevan texto, sólo
  los nombres de los bloques.
- **CDR (págs. 139–143).** Repite la tabla (pág. 139) y sigue con capturas.

### 1094 MetalHawk — PDR págs. 181–182

Es el más parecido a nuestra elección: **Python 3.13, PySide6 y pyqtgraph**,
con la interfaz armada en Qt Widgets Designer.

- **Capturas.** Una, en la pág. 182, de la ventana real de Windows.
- **Distribución.** Tres columnas y una fila de botones:
  - Izquierda: altitud contra tiempo arriba y giróscopo (°/s) abajo.
  - Centro: una columna de texto, "campo (unidad): valor", con toda la
    telemetría (tiempo, tiempo de misión, paquetes, modo, estado, altitud,
    temperatura, presión, tensión, corriente, giros, aceleraciones, GPS, eco,
    paquetes recibidos y enviados, ángulos de los servos).
  - Derecha: tensión y corriente en un mismo gráfico arriba, acelerómetro
    abajo.
  - Al pie: once botones de comando en una fila (CX_ON, CX_OFF, SIM_ENABLE,
    SIM_ACTIVATE, liberaciones, Calibrate…).
- **G12/G13.** "Comply" con remisión a la pág. 182 (pág. 208). En la pág. 181
  dice "Plots with bold traces for easy visibility". Los trazos son gruesos y
  cada gráfico tiene título, ejes con unidad y grilla; el panel de fondo es
  lila, no blanco, y la columna de texto central es chica. El sol sólo aparece en la pág. 177, como riesgo de
  recalentamiento: "an umbrella" para la notebook.
- **Texto que acompaña (pág. 181).** Cinco recuadros con viñetas (lenguajes y
  bibliotecas, comandos, graficado, telemetría y registro, simulación). La
  captura va sola en la diapositiva siguiente, sin texto.
- **CDR (págs. 126–128).** La misma ventana con datos de un vuelo de prueba
  real (altitud que sube a unos 600 m y baja), más botones (dos filas) y un
  selector de puerto. Aclara que los "Simulated Data" son datos aleatorios de
  prueba y que no hay que confundirlos con el modo simulación (pág. 128).

### 1081 SEDS ITBA — PDR págs. 137–144

- **Capturas.** Un gráfico suelto de temperatura (pág. 137), la pantalla
  completa (pág. 139) y la misma con el panel de comandos enmarcado en rojo
  (pág. 140). La pág. 142 muestra código, no la pantalla.
- **Distribución (pág. 139).**
  - Columna izquierda angosta: logo y texto en bloques (equipo, tiempo,
    paquetes recibidos y perdidos; modo, estado, altitud, temperatura,
    presión, tensión; posición GPS; aceleración X/Y/Z en m/s²).
  - Arriba a la derecha: el panel de comandos, "Positioned in the top-right
    corner" según el texto de la pág. 140, con nueve botones (Start/End
    Telemetry, Clear Plot Data, Set Time, Cal. Altitude, Cal. PRY, Enable,
    Activate y Deactivate SIM) y una línea "Send Command: CMD,1234," con
    "Send".
  - Debajo: grilla de gráficos (altitud, temperatura, tensión, aceleración y
    presión), con líneas finas y grilla punteada.
- **G12/G13.** "Comply" en la tabla (pág. 174), pero remite a la pág. 132 (el
  diseño de la GCS) para G12 y a la 139 para G13. Fondo claro y sin pestañas;
  los trazos son finos y los ejes no llevan unidad. En el CDR (pág. 141) la
  ventana real muestra una barra de pestañas con una sola pestaña,
  "Dashboard", heredada del widget de Qt: un detalle que un jurado estricto
  con G13 podría marcar.
- **Texto que acompaña.** Una línea por captura: "Plot using PyQtGraph / The
  graph will expand as more data is received" (pág. 137); "Buttons for
  frequently used commands and command prompt / Positioned in the top-right
  corner" (pág. 140).
- **CDR (págs. 139–145).** Versión beta real con ocho gráficos (suma
  giróscopo, motores, corriente) y el panel de comandos pasado abajo; dice que
  se probó la interfaz "with mock data" (pág. 145).

## Patrones comunes

1. **Una captura de la pantalla entera es lo central.** Los cinco la ponen;
   cuatro de cinco la ponen en una diapositiva casi sin texto. Los que tienen
   más diapositivas suman recortes del panel de comandos o del log, uno por
   subtítulo de la plantilla.
2. **Datos simulados en el PDR.** Nadie mostró un vuelo real en el PDR:
   maqueta vacía (Vortex), senoidales (MetalHawk) o datos ficticios (el
   resto). Es exactamente lo que vamos a tener.
3. **La misma geometría casi siempre:** una franja o columna de texto con el
   estado y los contadores, una grilla de gráficos que ocupa la mayor parte, y
   el panel de comandos en un borde (abajo a la izquierda en Vortex, al pie en
   MetalHawk, arriba a la derecha en SEDS ITBA, a la derecha en Daedalus).
4. **Comandos: botones para los fijos más una línea de texto.** Daedalus, SEDS
   ITBA y Bamantara tienen las dos cosas; Vortex y MetalHawk, sólo botones. El
   eco del comando está a la vista en todos.
5. **Gráficos de G7 uno por magnitud**, con aceleración y giro como tres
   trazos (X/Y/Z o roll/pitch/yaw) en un mismo gráfico. Tensión y corriente
   comparten gráfico en Daedalus y MetalHawk.
6. **G12 y G13 se declaran más de lo que se muestran.** Todos ponen "Comply";
   sólo Vortex lo escribe en la diapositiva de la captura y sólo MetalHawk
   muestra trazos gruesos de verdad. Ninguno muestra letra de 14 pt a ojo en
   la captura. Bamantara y MetalHawk tratan el sol sólo como riesgo de
   recalentamiento (cubierta, paraguas), no de legibilidad.
7. **El mapa aparece en cuatro de cinco** (no lo pide el anexo).

## Qué conviene copiar y qué evitar

**Copiar:**

- La nota de Vortex al pie de la captura, adaptada a nuestros requisitos:
  "Sin pestañas (G13); todo en unidades SI con la unidad a la vista (G6);
  letra de 14 pt o más, trazos y ejes en negrita, fondo blanco (G12)". Es la
  forma más barata de que el jurado lo vea sin buscarlo.
- La lista de Vortex que recorre G7 y G8 diciendo dónde está cada cosa, en la
  diapositiva que acompaña. Mejor todavía: rotular en la captura dónde está
  cada requisito, como hace Bamantara con sus flechas, pero con los códigos
  (`G7`, `G8`, `G14`, `G15`).
- La geometría de MetalHawk o de Vortex (columna de valores en texto, grilla
  de gráficos, botonera), que entra en una sola pantalla y es la nuestra en
  PySide6 + pyqtgraph.
- Los trazos gruesos de MetalHawk y los ejes con título y unidad de Vortex.
- El estado del software de vuelo y el eco del comando en grande, arriba
  (Daedalus, Vortex).
- Botones para los comandos fijos más una línea de texto (Daedalus, SEDS
  ITBA), que coincide con lo ya decidido en `docs/gcs-decisiones.md`.
- Una captura **con datos** que se muevan (el simulador con el perfil del
  Prometeo), no la maqueta vacía de Vortex: muestra que el graficado anda.

**Evitar:**

- Una pantalla más alta que la notebook (Bamantara): obliga a desplazarse y
  debilita G13.
- Cualquier rastro de pestañas, aunque sea una sola (la "Dashboard" de SEDS
  ITBA en su CDR). En Qt, no usar `QTabWidget` ni `QMainWindow` con docks
  tabulados.
- Fondos de color (beige, lila) y trazos finos o con relleno: G12 pide texto
  oscuro sobre fondo claro y trazos en negrita.
- Ejes sin unidad (SEDS ITBA) y valores como "85900000 Pa" (SEDS ITBA, CDR
  pág. 141): con G6 conviene kPa o hPa y el número formateado.
- Declarar "Comply" remitiendo a una diapositiva que no muestra el requisito
  (SEDS ITBA remite G12 a la pág. 132, el hardware).
- Código en la diapositiva en lugar de la pantalla (SEDS ITBA pág. 142, que
  además abre el CSV con `'w'` dos veces y pisaría el encabezado).

## Lo que quedó sin poder leer

Nada. Los diez PDF abrieron y tienen texto extraíble; las pantallas se miraron
renderizadas. Lo único que no existe en la biblioteca son las observaciones o
los puntajes del jurado sobre estas diapositivas.
