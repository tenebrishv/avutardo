"""PROTOTIPO DESCARTABLE: pantallas de la GCS para comparar.

Responde la issue #7, "¿Cómo es la pantalla de la GCS?". No es código de la
estación terrena: no tiene tests, el simulador es de juguete y los
telecomandos sólo vuelven como eco. Cuando se elija una variante, la buena
se reescribe en `src/` y este archivo queda en la rama `prototype/pantalla-gcs`.

Variantes, en la misma ventana de 1366×768 lógicos (el mínimo de #4):

    A  Franja + tabla + grilla   (la geometría que repiten los ganadores)
    B  Altitud protagonista      (un gráfico grande y el texto como registro)
    C  Tablero por subsistema    (cada valor al lado de su gráfico)

Ronda 2: híbridos A + C (franja arriba, tarjetas sin tabla, cada dato una vez,
toggle En vivo / Histórico global y por tarjeta, velocidad vertical). Cambian
en dónde van los avisos y los telecomandos:

    D  Chips de estado           (avisos como chips fijos en la franja, estilo
                                  Bamantara; telecomandos abajo)
    E  Pie de estado             (fases como barra de progreso, avisos en un
                                  pie de la GCS; telecomandos en columna)
    F  Línea de avisos           (una línea fija que se pone roja; Vuelo alto a
                                  la izquierda; telecomandos abajo)

Ronda 3: lo elegido en la ronda 2, junto.

    G  Fases y pie de E, Vuelo y GPS alto de F, tarjeta Recorrido (en metros
       desde el lanzamiento; en LANDED pasa a un QR de la última posición),
       ventanas de 30, 60 y 120 s o Misión, telecomandos en columna
    G2 Como G, con el Recorrido bajo los telecomandos y Energía en dos celdas;
       x, y, z en una línea que hace de leyenda, con la unidad en el título
    G3 Como G, con Vuelo y GPS de una fila y el Recorrido debajo

Ronda 5 (#23): tres variantes del bloque de energía, dentro de G2. Los tres
canales del INA3221 (batería, barra de 3.3 V y panel) y el rendimiento del
buck, calculado en la GCS paquete por paquete.

    G2A Por magnitud     un gráfico de tensión y otro de corriente, cada uno
                         con la batería y la barra; el valor al lado; panel y
                         rendimiento en una fila abajo (lo que pide la #23)
    G2B Por canal        una fila por canal: batería y barra, cada una con su
                         gráfico de dos ejes (V a la izquierda, A a la derecha)
    G2C Números primero  tabla canal × V, A, W con el rendimiento grande, y
                         dos gráficos angostos al lado

    Elegida: G2B (2026-11-15). Gráficos anchos y cada canal se lee entero;
    G2A dejaba los gráficos en unos 90 px por el ancho de las etiquetas.

Ronda 6 (#24): dónde va la sección de enlace RF, sobre G2B. Las tres llevan el
panel de telecomandos de la #21 (abajo); los conteos salen de la franja (cada
dato una vez) y el pie sólo avisa LINK LOST.

    L1  Columna derecha  telecomandos, enlace (una fila por valor) y Recorrido
    L2  Franja           el enlace en una franja a lo ancho, bajo la de arriba
    L3  Celda de grilla  el enlace bajo Vuelo y GPS, en dos columnas de pares

    Elegida: L3 (2026-11-16), con el enlace del alto justo de sus números y la
    columna derecha en 260 px para agrandar el Recorrido. L1 no entra en 768 px
    de alto aun con el Recorrido aplastado; L2 entra con 2 px y se pasa del
    ancho cuando los conteos llegan a cuatro cifras.

Ronda 7 (#22): la consola de depuración, sobre L3. Fina, abajo de todo, entre
la grilla y el pie; arranca oculta y un botón la muestra. Muestra cada línea
del puente tal cual (`<hex>,<rssi>,<snr>`, los bytes reales de la v2 armados
con `protocolo/vista_formato.py`: cabecera en azul, CRC en ocre), los CRC
rotos, los ajenos, los huecos del contador, los telecomandos que salen (TX,
14 B) y el texto de la Heltec de tierra (de juguete: su formato no está
definido). A 14 pt cada paquete ocupa dos líneas.

    K3   3 líneas, el botón en el pie
    K6   6 líneas, el botón en el pie
    K6F  6 líneas, el botón en la franja de arriba

    Elegida: K6 (2026-11-16). Seis líneas cuentan un CRC roto entero (el
    paquete descartado, el hueco del contador y el siguiente) y el botón en el
    pie no le quita ancho a la franja. K3 muestra poco más de un paquete. Con
    la consola abierta, los gráficos bajan su mínimo de 140 a 100 px: si no,
    la ventana pide 790 px de alto.

Telecomandos (#21), en las variantes de las rondas 6 y 7: un combobox con los
19 de `telecomandos.toml` y, al lado, el parámetro que pide cada uno (lista de
valores, número con su unidad y el rango del .toml, o nada; TIME_SET toma la
hora de la notebook). Send pide confirmación a los que la llevan en el .toml.
Debajo, los últimos tres con su estado: PENDING, ACK, REJECTED o NO ACK. La
cola sigue la ADR 0003: de a uno, justo después de un recibido (o en el
momento, con el enlace perdido), reintento con el mismo número si a los 3 s
no está en el eco y NO ACK después del tercer intento; un rechazado no se
reintenta. A bordo, de juguete, se valida contra el .toml y un número repetido
se confirma sin volver a ejecutarse. Para verlo: SIMP en FLIGHT sale REJECTED,
con F7 (enlace cortado) cualquiera termina NO ACK, y después de CX OFF los
demás quedan NO ACK hasta que CX ON vuelve con ACK.

Correr, desde `gcs/`:

    uv run python prototipos/pantalla.py        # arranca en G2B, la elegida
    uv run python prototipos/pantalla.py A      # arranca en A
    uv run python prototipos/pantalla.py G2A    # la ronda 5 (#23)
    uv run python prototipos/pantalla.py L1     # la ronda 6 (#24)
    uv run python prototipos/pantalla.py K6     # la ronda 7 (#22)

Teclas: ← y → cambian de variante, F11 alterna pantalla completa, F12 guarda
una captura al doble de píxeles en `prototipos/capturas/` (como pide #4, Q6).
Para ver los avisos: F6 saca y pone el pendrive, F7 corta y repone el enlace.
F8 adelanta 30 s de vuelo (para llegar al aterrizaje y ver el QR de G).

Para probar la simulación:

    F5        reinicia el vuelo desde STANDBY
    Shift+F5  arranque en frío: la estación abre sin paquetes (NO LINK) y la
              FSW tarda 10 s en transmitir (sólo L1 a L3 lo dibujan)
    Espacio   pausa y reanuda
    F9        velocidad ×1 → ×5 → ×10
    1 a 5     salta a STANDBY, ASCENT, DESCENT_1, DESCENT_2 o LANDED
    F1        ráfaga de 5 paquetes perdidos
    F2        el próximo paquete llega con el CRC roto (descartado y perdido)
    Shift+F2  llega un paquete de otro equipo (ajeno)
    Shift+F7  señal débil (SNR negativa, para ver el noise floor) / normal
    F3        GPS sin fix (0 satélites, posición sin dato) / con fix
    F4        batería baja (1.5 V menos) / normal
    Shift+F4  BAT_CURRENT sin dato / con dato (hueco en la curva, "—" en el
              número y en el rendimiento)
    F10       reinicio de la FSW: 3 s sin transmitir, un paquete en BOOT y
              sigue en su estado; el contador y el tiempo de misión siguen
              (F1, F2, F5)

Vuelo de demostración y capturas de la diap. 77 (#26): el mismo vuelo en cada
corrida, con los instantes `standby`, `descenso` y `aterrizado`.

    uv run python prototipos/pantalla.py --simular demo --hasta descenso
    uv run --with segno python prototipos/pantalla.py --captura salida.png --hasta aterrizado
    uv run python prototipos/pantalla.py K6 --captura salida.png --hasta consola

--captura corre fuera de pantalla (1366×768 lógicos con escala 2, según
`pantalla-captura.json`), graba el PNG a 2732×1536 y sale; en `standby` graba
además los recortes del diálogo de altitud cero, los telecomandos y Vuelo y GPS.

El QR de G necesita `segno`, que no es dependencia de la GCS: correr con
`uv run --with segno python prototipos/pantalla.py G`.
"""

from __future__ import annotations

import argparse
import bisect
import math
import os
import random
import sys
import tomllib
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QImage,
    QKeySequence,
    QPixmap,
    QShortcut,
    QTextOption,
    QValidator,
)
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

RAIZ = Path(__file__).resolve().parents[2]
TOML = RAIZ / "protocolo" / "telemetria.toml"
TOML_TC = RAIZ / "protocolo" / "telecomandos.toml"
CAPTURAS = Path(__file__).resolve().parent / "capturas"

PT = 14  # G12: letra de 14 pt o más, en toda la pantalla
TRAZO = 3  # G12: trazos en negrita
HISTORIA = 120  # segundos que muestra cada gráfico

NAN = float("nan")
COLORES = {"x": "#c0392b", "y": "#1e8449", "z": "#1f4e9c", "uno": "#1f4e9c", "dos": "#b9770e"}

# --- formato --------------------------------------------------------------

with TOML.open("rb") as f:
    FORMATO = tomllib.load(f)
CAMPOS = FORMATO["campo"]
UNIDAD = {c["nombre"]: c["unidad"] for c in CAMPOS}
ETIQUETA = {c["nombre"]: c["etiqueta"] for c in CAMPOS}
# Los que se muestran de otra forma (la hora, en hh:mm:ss): su unidad no es la
# del texto en pantalla, así que van sin corchetes.
SIN_CORCHETES = {c["nombre"] for c in CAMPOS if c.get("mostrar")}
with TOML_TC.open("rb") as f:
    FORMATO_TC = tomllib.load(f)
COMANDOS = {c["nombre"]: c for c in FORMATO_TC["comando"]}
CODIGO_TC = {c["nombre"]: i for i, c in enumerate(FORMATO_TC["comando"])}

# El codificador de la vista del formato (#16): los bytes reales de la v2, con
# cabecera CCSDS y CRC, para la consola de depuración (#22).
sys.path.insert(0, str(RAIZ / "protocolo"))
import vista_formato as vf  # noqa: E402

# Lo que cuenta o calcula la GCS, que no es un campo del formato: inglés común,
# nunca una etiqueta inventada en mayúsculas (#25). Los conteos, con la forma en
# pantalla de GLOSSARY.md.
CALCULADO = {
    "contador": "Sequence count",  # el de la cabecera CCSDS
    "recibidos": "Received",
    "perdidos": "Lost",
    "descartados": "Discarded",
    "eco": "CMD_ECHO",  # los tres campos del eco en una línea
    "vel_vertical": "Vertical speed [m/s]",
    "alt_max": "Max altitude [m]",
    "rendimiento": "Buck efficiency [%]",
    "potencia_bateria": "Battery power [W]",
    "potencia_3v3": "3.3 V bus power [W]",
    "potencia_panel": "Solar panel power [W]",
}

MILES = " "  # espacio fino irrompible


def agrupar(texto: str) -> str:
    """Agrupa de a tres la parte entera, desde 4 dígitos: 1245 → 1 245."""
    signo, texto = ("-", texto[1:]) if texto.startswith("-") else ("", texto)
    entera, punto, decimales = texto.partition(".")
    if len(entera) >= 4:
        primero = len(entera) % 3 or 3
        resto = [entera[i : i + 3] for i in range(primero, len(entera), 3)]
        entera = MILES.join([entera[:primero], *resto])
    return signo + entera + punto + decimales


def fmt(nombre: str, valor) -> str:
    """Punto decimal y espacio fino irrompible de miles, como la norma del equipo."""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, float) and math.isnan(valor):
        return "—"  # sin dato
    if isinstance(valor, int):
        return agrupar(str(valor))
    dec = 6 if nombre.startswith("gps_l") else 2 if abs(valor) < 100 else 1
    return agrupar(f"{valor:.{dec}f}")


def con_unidad(nombre: str) -> str:
    """Cómo se rotula en pantalla: la etiqueta del .toml con su unidad
    (`TX_POWER [dBm]`), o el inglés común de lo que calcula la GCS."""
    if nombre in CALCULADO:
        return CALCULADO[nombre]
    u = UNIDAD[nombre]
    if u and nombre not in SIN_CORCHETES:
        return f"{ETIQUETA[nombre]} [{u}]"
    return ETIQUETA[nombre]


# --- bytes del paquete (#22) ---------------------------------------------


def codigo_tc(nombre: str) -> int | None:
    """El código de telecomando que viaja en el eco; sin eco, el centinela."""
    if not nombre:
        return None
    return CODIGO_TC.get(nombre, 200)  # «?X»: un código que el .toml no tiene


def bytes_paquete(p: dict, hora: datetime) -> bytes:
    """Los 75 B del paquete que armaría la FSW con los valores del simulador."""
    valores = {}
    for c in CAMPOS:
        v = p[c["nombre"]]
        sin_dato = v == "" or (isinstance(v, float) and math.isnan(v))
        valores[c["nombre"]] = None if sin_dato else v
    valores["hora"] = hora.isoformat()
    valores["eco_codigo"] = codigo_tc(p["eco_codigo"])
    valores["extra_id"] = codigo_tc(p["extra_id"])
    return vf.codificar_telemetria(FORMATO, p["contador"] % 2**14, valores)


def bytes_ajeno(numero: int, largo: int) -> bytes:
    """Un paquete de otro equipo: cabecera CCSDS con otro APID y bytes al azar
    (con su propia semilla, para no mover el vuelo de demostración)."""
    azar = random.Random(numero)
    cabecera = vf.cabecera_ccsds(vf.TM, 0x2B1, numero % 2**14, largo)
    return cabecera + bytes(azar.randrange(256) for _ in range(largo - 6))


# --- simulador de juguete -------------------------------------------------

# Vuelo de demostración (#8, "Vuelo de demostración" en docs/gcs-decisiones.md):
# el mismo en cada corrida, del que salen las capturas de la diap. 77.
SEMILLA_DEMO = 8
HORA_DEMO = datetime(2026, 11, 17, 15, 0, tzinfo=UTC)  # hora UTC al arrancar
EYECCION = 12  # s desde el despegue: comienzo de misión (X3)
GUION_DEMO = {  # segundo de la notebook → telecomando, mandado en STANDBY
    5: ("GET_SENSORS", ""),  # F4: así el par extra tiene dato todo el vuelo (#26)
    10: ("TIME_SET", str(int(HORA_DEMO.timestamp()) + 10)),
    15: ("CAL_ALT", ""),
}
# Segundos desde el despegue → falla. El descartado también deja un hueco, así
# que es el perdido del descenso: 3 perdidos y 1 descartado hasta `descenso`.
FALLAS_DEMO = {4: "perdido", 5: "perdido", 30: "crc", 100: "perdido"}
INSTANTES = ("standby", "descenso", "aterrizado", "consola")


def llego(sim: Simulador, instante: str) -> bool:
    """Si el vuelo de demostración ya está en el instante con nombre."""
    if instante == "standby":
        return sim.reloj >= 20
    if instante == "descenso":
        return sim.t - sim.despegue >= EYECCION + 40
    if instante == "consola":  # #22: justo después del paquete con el CRC roto
        return sim.t - sim.despegue >= 31
    return sim.t_aterrizaje is not None and sim.t - sim.t_aterrizaje >= 10


# --- cola de telecomandos (#21, ADR 0003) ---------------------------------

LOST_TRAS = 3  # s sin un recibido para LINK LOST (GLOSSARY: enlace perdido)
ESPERA_ECO = 3  # s que la estación espera el eco antes de reintentar
INTENTOS = 3  # el primero y dos reintentos; después, NO ACK


@dataclass
class Envio:
    """Un telecomando de la estación terrena y lo que se sabe de él."""

    numero: int  # el número de telecomando: un reintento lleva el mismo
    nombre: str
    parametro: str | int | None
    estado: str = "PENDING"  # PENDING, ACK, REJECTED o NO ACK (#21)
    intentos: int = 0
    t_envio: int = 0  # segundo de la notebook del último intento
    por_mandar: bool = True


class ColaTelecomandos:
    """El lado de la estación de la ADR 0003, sin Qt: de a un telecomando por
    vez, mandado justo después de un recibido (o en el momento, con el enlace
    perdido); si a los ESPERA_ECO s su número no está en el eco, se reintenta,
    y después de INTENTOS queda NO ACK. Un rechazado no se reintenta. Los que
    esperan en la cola también se ven PENDING."""

    def __init__(self) -> None:
        self.entero = 0
        self.cola: deque[Envio] = deque()
        self.en_vuelo: Envio | None = None
        self.historia: list[Envio] = []  # el más nuevo primero

    def encolar(self, nombre: str, parametro: str | int | None) -> Envio:
        self.entero = self.entero % 16383 + 1  # el contador CCSDS de 14 bits, sin el 0
        envio = Envio(self.entero, nombre, parametro)
        self.cola.append(envio)
        self.historia.insert(0, envio)
        del self.historia[20:]
        return envio

    def tic(self, reloj: int, enlace_perdido: bool) -> list[Envio]:
        """Cada segundo: vence la espera del eco; con el enlace perdido, manda."""
        e = self.en_vuelo
        if e is not None and not e.por_mandar and reloj - e.t_envio >= ESPERA_ECO:
            if e.intentos >= INTENTOS:
                e.estado = "NO ACK"
                self.en_vuelo = None
            else:
                e.por_mandar = True
        return self._salientes(reloj) if enlace_perdido else []

    def al_recibir(self, paquete: dict, reloj: int) -> list[Envio]:
        """Con cada recibido: el eco confirma o rechaza el que está en vuelo, y
        sale el que sigue (o el reintento)."""
        e = self.en_vuelo
        if e is not None and e.intentos and paquete.get("eco_id") == e.numero:
            e.estado = "ACK" if paquete["resultado_comando"] == "ACCEPTED" else "REJECTED"
            self.en_vuelo = None
        return self._salientes(reloj)

    def _salientes(self, reloj: int) -> list[Envio]:
        if self.en_vuelo is None and self.cola:
            self.en_vuelo = self.cola.popleft()
        e = self.en_vuelo
        if e is None or not e.por_mandar:
            return []
        e.intentos += 1
        e.t_envio = reloj
        e.por_mandar = False
        return [e]


def texto_parametro(nombre: str, parametro: str | int | None) -> str:
    """El parámetro como se lee: el valor, el número con su unidad, o la hora
    UTC de TIME_SET."""
    definicion = COMANDOS.get(nombre, {})
    if parametro is None:
        return ""
    if nombre == "TIME_SET" and isinstance(parametro, int):
        return datetime.fromtimestamp(parametro, UTC).strftime("%H:%M:%S")
    if isinstance(parametro, int) and definicion.get("unidad"):
        return f"{agrupar(str(parametro))} {definicion['unidad']}"
    return str(parametro)


def texto_envio(nombre: str, parametro: str | int | None) -> str:
    """El comando con su parámetro, como se lee en el panel y en la consola."""
    return f"{nombre} {texto_parametro(nombre, parametro)}".rstrip()


def pide_confirmacion(nombre: str, parametro: str | int | None) -> bool:
    """`confirmar` del .toml: true, o la lista de valores que la piden."""
    confirmar = COMANDOS.get(nombre, {}).get("confirmar", False)
    return confirmar is True or (isinstance(confirmar, list) and parametro in confirmar)


class Simulador:
    """Un vuelo tipo Prometeo a 1 Hz, con algún paquete perdido; con `demo`,
    el vuelo de demostración: semilla fija, sin pérdidas al azar y con las
    fallas y los telecomandos de su guion."""

    def __init__(self, precarga: bool = True, demo: bool = False) -> None:
        self.demo = demo
        self.azar = random.Random(SEMILLA_DEMO if demo else None)
        self.despegue = 30 if demo else 45  # segundos de STANDBY
        self.v2 = 4.3 if demo else 3.5  # bajada con el segundo descenso [m/s]
        self.p_perdida = 0.0 if demo else 0.04
        self.sesgo_alt = 3.0 if demo else 0.0  # corrida hasta la altitud cero
        self.t = 0.0
        self.contador = 0
        self.recibidos = 0
        self.perdidos = 0
        self.ultimo_contador: int | None = None
        # Eco y par extra (ADR 0003): sin telecomandos todavía, en blanco.
        self.eco_id = 0
        self.eco_codigo = ""
        self.resultado_comando = ""
        self.extra_id = ""
        self.extra_valor = 0
        self.cortado = False
        self.cortar_tras_paquete = False  # CX OFF: corta después del próximo paquete
        self.modo = "FLIGHT"  # lo cambia SIM
        # #21: la cola de la estación terrena, con los reintentos y el estado de
        # cada envío. Vive acá y no en el panel, que se rehace con ← y →.
        self.cola = ColaTelecomandos()
        self.offset_alt = 0.0
        self.alt_max = 0.0
        # La misión entera: el modo "Histórico" la necesita (son ~10 min a 1 Hz).
        # El contador viene en la cabecera CCSDS (telemetria.toml), no en CAMPOS.
        self.historia: dict[str, list] = {c["nombre"]: [] for c in CAMPOS} | {"contador": []}
        self.tiempos: list[float] = []
        # Lo que agrega la GCS, fuera del formato.
        self.reloj = 0  # segundos de la notebook, avanzan aunque no llegue nada
        self.ultimo_rx = 0
        self.enlace_caido = False
        self.pendrive = True
        self.t_lanzamiento: float | None = None
        self.t_cambio = 0.0  # cuándo cambió el estado por última vez (para G)
        self.deriva = 0.0  # segundos de deriva con el viento: sólo en vuelo
        self.vel_vertical = 0.0
        self.rssi = NAN  # sólo cambian con un recibido (#24, Q2)
        self.snr = NAN
        self.ajenos = 0  # #24: paquetes de otros equipos (otro APID u otro largo)
        self.senal_debil = False  # #24: SNR negativa, para ver el noise floor
        self.ultimo: dict = {}
        self.registro: deque[str] = deque(maxlen=200)
        # #22: lo que muestra la consola de depuración, (hora UTC, tipo, texto).
        self.consola: deque[tuple[str, str, str]] = deque(maxlen=60)
        # Texto de juguete: el formato de la salida de texto de la Heltec de
        # tierra todavía no está definido.
        self.anotar("heltec", "ground bridge ready")
        # Fallas que se disparan con el teclado (ver el encabezado).
        self.descartados = 0
        self.rafaga = 0  # paquetes que quedan por perder
        self.crc_roto = 0  # paquetes que quedan por llegar con el CRC roto
        self.sin_fix = False
        self.bateria_baja = False
        self.ina_sin_dato = False  # BAT_CURRENT sin dato (Shift+F4)
        # Energía (#23): el estado del perfil en el paso anterior (para ver el
        # segundo en que libera el servo), cuándo aterrizó y el ángulo del panel.
        self.estado_sim = "STANDBY"
        self.t_aterrizaje: float | None = None
        self.angulo_panel = 0.0
        self.reinicio = 0  # segundos que le faltan a la FSW para volver
        self.boot = False  # el próximo paquete sale en BOOT
        # Arranca con 40 s en la rampa y el lanzamiento a los 45 s, para que los
        # gráficos no estén vacíos al abrir. El de demostración arranca de cero.
        for _ in range(40 if precarga and not demo else 0):
            self.paso()

    def _perfil(self, tv: float) -> tuple[float, str]:
        if tv < 0:
            return 0.0, "STANDBY"
        if tv < 12:
            return 673 * math.sin(tv / 12 * math.pi / 2), "ASCENT"
        alt = 673 - 15 * (tv - 12)
        if alt > 0.8 * 673:
            return alt, "DESCENT_1"
        t2 = 12 + (673 - 0.8 * 673) / 15
        alt = 0.8 * 673 - self.v2 * (tv - t2)
        return (alt, "DESCENT_2") if alt > 0 else (0.0, "LANDED")

    def paso(self) -> None:
        self.reloj += 1
        if self.demo and self.reloj in GUION_DEMO:
            self.telecomando(*GUION_DEMO[self.reloj])
        # #21: los reintentos corren con el reloj de la notebook, llegue o no
        # un paquete; con el enlace perdido, la estación manda en el momento.
        self.mandar(self.cola.tic(self.reloj, self.enlace_perdido()))
        # #24: otro equipo transmite cada 4 s desde el despegue, y una vez llega
        # un paquete de otro largo. Los ajenos no tocan los otros conteos.
        tl = self.reloj - self.despegue
        if tl >= 0 and tl % 4 == 0:
            self.ajeno()
        if tl == 21:
            self.ajeno(48)
        if self.cortado:
            return
        # CX OFF: el eco sale en un último paquete y después, silencio.
        cortar, self.cortar_tras_paquete = self.cortar_tras_paquete, False
        self.transmitir_paquete()
        if cortar:
            self.cortado = True

    def enlace_perdido(self) -> bool:
        """Sin recibidos todavía, o más de LOST_TRAS s sin uno (GLOSSARY)."""
        return self.recibidos == 0 or self.reloj - self.ultimo_rx > LOST_TRAS

    def transmitir_paquete(self) -> None:
        """La FSW arma y manda el paquete del segundo; puede perderse en el aire."""
        if self.reinicio > 0:
            # La FSW está reiniciando: no transmite, pero el tiempo de misión
            # sigue (F2) y el contador no salta (F1), así que no hay perdidos.
            self.reinicio -= 1
            self.t += 1
            self.boot = self.reinicio == 0
            return
        self.t += 1
        self.contador += 1
        tv = self.t - self.despegue
        alt, estado = self._perfil(tv)
        rot_z = self.azar.gauss(0, 3) + (90 if 12 <= tv < 60 else 0)
        energia = self._energia(estado, rot_z)
        if self.boot:  # el primer paquete después del reinicio
            estado = "BOOT"
            self.boot = False
        if estado not in ("STANDBY", "LANDED"):
            self.deriva += 1
        if self.ultimo and estado != self.ultimo["estado_fsw"]:
            self.t_cambio = self.t
        alt += self.azar.gauss(0, 0.4)
        r = self.azar.gauss
        g = 9.81
        empuje = 60 if 0 <= tv < 2 else 0
        golpe = 80 if 12 <= tv < 13 else 0
        liberado = estado in ("DESCENT_2", "LANDED")
        # Los 32 campos de la v2, en el orden del .toml. Los campos con `valores`
        # (estado_fsw, modo…) y los códigos de telecomando van ya con su nombre:
        # el prototipo no arma bytes. Fuera de energía y enlace, valores de juguete.
        p = {
            "contador": self.contador,  # cabecera CCSDS, no es un campo
            # Operación
            "estado_fsw": estado,
            "modo": self.modo,
            "hora": self.hora().strftime("%H:%M:%S"),
            # Segundos enteros desde el comienzo de misión; antes, sin dato (.toml).
            "tiempo_mision": int(tv - EYECCION) if tv >= EYECCION else NAN,
            # Ambiental
            "presion": 101325 * (1 - 2.25577e-5 * alt) ** 5.25588 + r(0, 3),
            "altitud": alt + self.sesgo_alt - self.offset_alt,
            "temperatura": 18.0 - 0.0065 * alt + r(0, 0.1),
            "humedad": round(45 + r(0, 0.5)),
            # Energía (#23)
            **energia,
            # Navegación
            "gps_latitud": -53.7860 + 0.00002 * self.deriva + r(0, 0.000005),
            "gps_longitud": -67.7000 + 0.00003 * self.deriva + r(0, 0.000005),
            "gps_altitud": 30 + alt + r(0, 2),
            "gps_satelites": 9,
            # Inercial
            "acel_x": r(0, 0.3) + golpe * 0.3,
            "acel_y": r(0, 0.3),
            "acel_z": g + empuje + golpe + r(0, 0.3),
            "rot_x": r(0, 3) + (40 * math.sin(tv) if 12 <= tv < 60 else 0),
            "rot_y": r(0, 3),
            "rot_z": rot_z,
            # Descenso
            "estado_descenso2": "TRIGGERED" if liberado else "ARMED",
            "servo": 90 if liberado else 0,
            # Enlace
            "potencia_tx": 20,
            # Telecomandos
            "eco_id": self.eco_id,
            "eco_codigo": self.eco_codigo,
            "resultado_comando": self.resultado_comando,
            "extra_id": self.extra_id,
            "extra_valor": self.extra_valor,
        }
        assert p.keys() == self.historia.keys(), "el simulador no arma los campos del .toml"
        if self.sin_fix:  # 0 satélites es un dato real; la posición, sin dato
            nan = float("nan")
            p.update(gps_latitud=nan, gps_longitud=nan, gps_altitud=nan, gps_satelites=0)
        falla = FALLAS_DEMO.get(tv) if self.demo else None
        if falla == "perdido":
            return
        if falla == "crc":
            self.crc_roto += 1
        if self.rafaga > 0:
            self.rafaga -= 1
            return
        if self.crc_roto > 0:  # llega, pero no se decodifica: descartado y hueco
            self.crc_roto -= 1
            self.descartados += 1
            roto = bytearray(bytes_paquete(p, self.hora()))
            roto[40] ^= 0x10  # un bit cambiado en el aire
            self.anotar("crc", self.linea_puente(bytes(roto), self.rssi, self.snr))
            return
        if self.enlace_caido or (self.azar.random() < self.p_perdida and self.contador > 3):
            return  # paquete perdido en el aire
        if self.ultimo_contador is not None:
            hueco = self.contador - self.ultimo_contador - 1
            self.perdidos += hueco
            if hueco > 0:
                a, b = self.ultimo_contador + 1, self.contador - 1
                rango = f"{a}" if a == b else f"{a}–{b}"
                self.anotar("lost", f"{hueco} lost: sequence count {rango}")
        self.ultimo_contador = self.contador
        self.recibidos += 1
        self.ultimo_rx = self.reloj
        self.alt_max = max(self.alt_max, p["altitud"])
        self.ultimo = p
        self.tiempos.append(self.t)
        for k, v in p.items():
            self.historia[k].append(v)
        if self.t_lanzamiento is None and estado != "STANDBY":
            self.t_lanzamiento = self.t
        # Velocidad vertical: pendiente de la altitud en los últimos ~2 s.
        ts, hs = self.tiempos[-3:], self.historia["altitud"][-3:]
        if len(ts) >= 2:
            mt, mh = sum(ts) / len(ts), sum(hs) / len(hs)
            den = sum((t - mt) ** 2 for t in ts)
            self.vel_vertical = sum((t - mt) * (h - mh) for t, h in zip(ts, hs, strict=True)) / den
        # RSSI y SNR: los agregaría la Heltec de tierra; acá, de juguete.
        if self.senal_debil:  # por debajo del ruido: LoRa todavía recibe
            self.rssi = -118 + r(0, 1)
            self.snr = -8 + r(0, 0.5)
        else:
            self.rssi = -68 - alt / 25 + r(0, 1.5)
            self.snr = 10 - alt / 120 + r(0, 0.5)
        self.registro.append(",".join(fmt(c["nombre"], p[c["nombre"]]) for c in CAMPOS))
        self.anotar("rx", self.linea_puente(bytes_paquete(p, self.hora()), self.rssi, self.snr))
        # #21: la estación lee el eco y manda justo después de un recibido.
        self.mandar(self.cola.al_recibir(p, self.reloj))

    # --- consola de depuración (#22) ---

    def anotar(self, tipo: str, texto: str) -> None:
        """Una línea de la consola, con la hora UTC de la notebook."""
        hora = HORA_DEMO + timedelta(seconds=self.reloj) if self.demo else datetime.now(UTC)
        self.consola.append((hora.strftime("%H:%M:%S"), tipo, texto))

    @staticmethod
    def linea_puente(datos: bytes, rssi: float, snr: float) -> str:
        """Lo que manda la Heltec de tierra por USB: `linea_puente` del .toml."""
        rssi_txt = "nan" if math.isnan(rssi) else f"{rssi:.1f}"
        snr_txt = "nan" if math.isnan(snr) else f"{snr:.1f}"
        return f"{datos.hex().upper()},{rssi_txt},{snr_txt}"

    def ajeno(self, largo: int = 75) -> None:
        """#24: llega un paquete de otro equipo (otro APID u otro largo)."""
        self.ajenos += 1
        datos = bytes_ajeno(self.ajenos, largo)
        self.anotar("foreign", self.linea_puente(datos, -97.0, 2.5))

    def _energia(self, estado: str, rot_z: float) -> dict:
        """Los seis campos del INA3221 (#23). Corriente positiva = consumo.

        La barra de 3.3 V sale de la tabla de consumos de la planilla (punto 65
        de la PDR), con la Heltec al 57 % de TX: cierra con 4.64 Wh en 120 min.
        Cada corriente es el promedio del segundo, no una muestra de la TX.
        """
        r = self.azar.gauss
        previo, self.estado_sim = self.estado_sim, estado
        if estado == "LANDED" and self.t_aterrizaje is None:
            self.t_aterrizaje = self.t
        recien_aterrizado = estado == "LANDED" and self.t - self.t_aterrizaje < 30
        if estado == "DESCENT_2" and previo == "DESCENT_1":
            i33 = 1.33  # el segundo en que el servo libera el segundo descenso
        elif estado in ("DESCENT_1", "DESCENT_2") or recien_aterrizado:
            i33 = 1.03  # cámaras grabando (#31)
        else:
            i33 = 0.69  # reposo
        i33 += r(0, 0.01)
        v33 = 3.30 - 0.02 * i33 + r(0, 0.004)
        # Batería 2S cargada: rendimiento cercano al 90 %, resistencia interna de
        # unos 0.1 Ω y una descarga casi nula en el vuelo.
        rend = 0.90 - 0.01 * (i33 - 0.69) + r(0, 0.004)
        p_bat = v33 * i33 / rend
        v_abierto = 8.25 - 0.00002 * self.t - 1.5 * self.bateria_baja
        i_bat = p_bat / v_abierto
        for _ in range(3):
            i_bat = p_bat / (v_abierto - 0.1 * i_bat)
        v_bat = v_abierto - 0.1 * i_bat + r(0, 0.003)
        # Panel sobre 100 Ω, de juguete (unos 5 V / 50 mA de pico) hasta tener su
        # hoja: adentro del cohete no ve luz, en el descenso gira con rot_z y en
        # tierra queda fijo.
        if estado in ("STANDBY", "ASCENT"):
            v_panel = abs(r(0, 0.01))
        else:
            if estado != "LANDED":
                self.angulo_panel += rot_z  # 1 s de giro
            v_panel = max(0.0, 2.5 + 2.5 * math.cos(math.radians(self.angulo_panel)) + r(0, 0.03))
        return {
            "tension_bateria": v_bat,
            "corriente_bateria": float("nan") if self.ina_sin_dato else i_bat,
            "tension_3v3": v33,
            "corriente_3v3": i33,
            "tension_panel": v_panel,
            "corriente_panel": v_panel / 100 + r(0, 0.0005),
        }

    def hora(self) -> datetime:
        """La del reloj de la notebook; en el de demostración, fija."""
        if self.demo:
            return HORA_DEMO + timedelta(seconds=self.t)
        return datetime.now(UTC)

    def saltar(self, estado: str) -> None:
        """Corre el vuelo hasta que el perfil llegue a `estado` (sólo hacia adelante)."""
        for _ in range(1000):
            if self.cortado or self._perfil(self.t - self.despegue)[1] == estado:
                return
            self.paso()

    # --- telecomandos (#21, ADR 0003) ---

    def telecomando(self, nombre: str, argumento: str = "") -> None:
        """La estación encola un telecomando escrito como texto («CX OFF»,
        «TX_POWER 20»): el guion del vuelo de demostración y la línea de texto
        de las variantes viejas. Sale cuando le toca, por la cola."""
        nombre = nombre.upper()
        definicion = COMANDOS.get(nombre, {})
        parametro: str | int | None = None
        if "valores" in definicion:
            parametro = argumento.upper()
        elif argumento:
            try:
                parametro = int(argumento)
            except ValueError:
                parametro = argumento  # no se codifica y a bordo se rechaza
        self.cola.encolar(nombre, parametro)

    def mandar(self, envios: list[Envio]) -> None:
        """La estación transmite: una línea TX en la consola por intento."""
        for e in envios:
            texto = texto_envio(e.nombre, e.parametro)
            if e.intentos > 1:
                texto += f"  (attempt {e.intentos} of {INTENTOS})"
            try:
                tc = vf.codificar_telecomando(FORMATO, FORMATO_TC, e.numero, e.nombre, e.parametro)
                self.anotar("tx", f"{tc.hex().upper()}  {texto}")
            except (KeyError, ValueError, AttributeError, OverflowError, TypeError):
                self.anotar("tx", f"{texto}  (not encodable)")
            self.recibir_telecomando(e.numero, e.nombre, e.parametro)

    def recibir_telecomando(self, numero: int, nombre: str, parametro) -> None:
        """A bordo: el telecomando llega y vuelve como eco en el paquete
        siguiente (número, código y resultado). Un número repetido se confirma
        sin volver a ejecutarse. De juguete: se valida contra el .toml, pero
        sólo CAL_ALT, GET_SENSORS, CX y SIM tienen efecto."""
        if self.enlace_caido or self.reinicio > 0:
            return  # no llega: perdido en el aire, o la FSW está reiniciando
        if numero == self.eco_id:
            return  # repetido: el eco ya lo confirma
        comando = COMANDOS.get(nombre)
        aceptado = comando is not None and self.acepta(comando, parametro)
        self.eco_id = numero
        self.eco_codigo = nombre if comando else f"?{nombre}"
        self.resultado_comando = "ACCEPTED" if aceptado else "REJECTED"
        if not aceptado:
            return
        if nombre == "CAL_ALT":
            self.offset_alt += self.ultimo.get("altitud", 0.0)
        if nombre == "GET_SENSORS":  # F4: responde por el par extra
            self.extra_id, self.extra_valor = nombre, 0b11111  # los cinco sensores
        if nombre == "CX":
            self.cortar_tras_paquete = parametro == "OFF"
            if parametro == "ON":
                self.cortado = False  # se confirma con el primer paquete que vuelve
        if nombre == "SIM":
            self.modo = {"OFF": "FLIGHT", "PRESSURE": "SIM_PRESSURE", "FULL": "SIM_FULL"}[parametro]

    def acepta(self, comando: dict, parametro) -> bool:
        """Las reglas de rechazo de telecomandos.toml: estado, modo y rango."""
        estado = self.ultimo.get("estado_fsw", "STANDBY")
        if estado not in comando.get("solo_en_estado", [estado]):
            return False
        if self.modo not in comando.get("solo_en_modo", [self.modo]):
            return False
        if "valores" in comando:
            return parametro in comando["valores"]
        if "unidad" in comando:
            if not isinstance(parametro, int):
                return False
            return comando.get("minimo", parametro) <= parametro <= comando.get("maximo", parametro)
        return parametro in (None, 0)


# --- piezas comunes -------------------------------------------------------


def texto_eco(p: dict) -> str:
    """Los tres campos del eco en una línea: «#3 CAL_ALT ACCEPTED»."""
    if not p.get("eco_id"):
        return "—"
    return f"#{p['eco_id']} {p['eco_codigo']} {p['resultado_comando']}"


def configurar_pyqtgraph() -> None:
    pg.setConfigOptions(background="w", foreground="k", antialias=True)


def grafico(titulo: str, unidad: str, series: list[str]) -> tuple[pg.PlotWidget, dict]:
    w = pg.PlotWidget()
    fuente = QFont()
    fuente.setPointSize(PT)
    fuente.setBold(True)
    w.setTitle(f"<b>{titulo} [{unidad}]</b>", size=f"{PT}pt")
    for lado in ("left", "bottom"):
        eje = w.getAxis(lado)
        eje.setPen(pg.mkPen("k", width=2))
        eje.setTextPen("k")
        eje.setStyle(tickFont=fuente)
    estilo = {"color": "#000", "font-size": f"{PT}pt", "font-weight": "bold"}
    # Segundos desde que arrancó la estación: MISSION_TIME no tiene dato antes de
    # la eyección.
    w.setLabel("bottom", "Time [s]", **estilo)
    w.showGrid(x=True, y=True, alpha=0.25)
    w.setMouseEnabled(False, False)
    w.hideButtons()
    if len(series) > 1:
        w.addLegend(offset=(5, 5), labelTextSize=f"{PT}pt")
    curvas = {}
    for s in series:
        color = COLORES.get(s[-1], COLORES["uno"]) if len(series) > 1 else COLORES["uno"]
        curvas[s] = w.plot(
            pen=pg.mkPen(color, width=TRAZO), name=s[-1] if len(series) > 1 else None
        )
    return w, curvas


def label(texto: str = "", negrita: bool = False, pt: int = PT, alinear=None) -> QLabel:
    lb = QLabel(texto)
    f = lb.font()
    f.setPointSize(pt)
    f.setBold(negrita)
    lb.setFont(f)
    if alinear is not None:
        lb.setAlignment(alinear)
    return lb


class PanelComandos(QWidget):
    """Botones fijos + línea de texto + eco. Igual en las tres variantes,
    salvo la orientación: el panel no es lo que se compara."""

    def __init__(self, sim: Simulador, vertical: bool, mostrar_eco: bool = True) -> None:
        super().__init__()
        self.sim = sim
        caja = QVBoxLayout(self) if vertical else QHBoxLayout(self)
        caja.setContentsMargins(4, 4, 4, 4)
        botones = [
            ("Zero altitude", "CAL_ALT", True),
            ("Set UTC time", "TIME_SET", False),
            ("Extra data", "GET_SENSORS", False),
            ("Telemetry off", "CX OFF", True),
        ]
        for texto, nombre, confirmar in botones:
            b = QPushButton(texto)
            b.setMinimumHeight(36)
            if confirmar:
                b.setStyleSheet("QPushButton { border: 2px solid #b03a2e; padding: 4px 10px; }")
            b.clicked.connect(lambda _=False, n=nombre, c=confirmar, t=texto: self.mandar(n, c, t))
            caja.addWidget(b)
        self.linea = QLineEdit()
        self.linea.setPlaceholderText("Telecommand…")
        self.linea.returnPressed.connect(self.mandar_linea)
        caja.addWidget(self.linea, 1)
        self.eco = label("CMD_ECHO: —", negrita=True)
        caja.addWidget(self.eco)
        self.eco.setVisible(mostrar_eco)  # en los híbridos el eco va en la franja

    def mandar(self, nombre: str, confirmar: bool, texto: str) -> None:
        if confirmar:
            r = QMessageBox.question(self, "Confirm", f"Send “{texto}”?")
            if r != QMessageBox.StandardButton.Yes:
                return
        self.sim.telecomando(*nombre.split())

    def mandar_linea(self) -> None:
        if partes := self.linea.text().split():
            self.sim.telecomando(*partes[:2])
            self.linea.clear()

    def actualizar(self) -> None:
        self.eco.setText(f"CMD_ECHO: {texto_eco(self.sim.ultimo)}")


GRAFICOS_G7 = [
    (ETIQUETA["altitud"], UNIDAD["altitud"], ["altitud"]),
    (ETIQUETA["tension_bateria"], UNIDAD["tension_bateria"], ["tension_bateria"]),
    (ETIQUETA["corriente_bateria"], UNIDAD["corriente_bateria"], ["corriente_bateria"]),
    ("Acceleration", "m/s²", ["acel_x", "acel_y", "acel_z"]),
    ("Rotation rate", "°/s", ["rot_x", "rot_y", "rot_z"]),
]


def refrescar_curvas(sim: Simulador, curvas: dict, inicio: float | None = None) -> None:
    """Dibuja desde `inicio`; por defecto, los últimos HISTORIA segundos."""
    t = sim.tiempos
    if not t:
        return
    if inicio is None:
        inicio = t[-1] - HISTORIA
    i = bisect.bisect_left(t, inicio)
    for nombre, curva in curvas.items():
        curva.setData(t[i:], sim.historia[nombre][i:], connect="finite")


def indicador(titulo: str) -> tuple[QFrame, QLabel]:
    caja = QFrame()
    caja.setFrameShape(QFrame.Shape.StyledPanel)
    v = QVBoxLayout(caja)
    v.setContentsMargins(8, 2, 8, 2)
    v.setSpacing(0)
    v.addWidget(label(titulo, pt=PT))
    valor = label("—", negrita=True, pt=PT + 6)
    v.addWidget(valor)
    return caja, valor


# --- variante A: franja + tabla + grilla ----------------------------------


class VarianteA(QWidget):
    nombre = "Strip + table + grid"

    def __init__(self, sim: Simulador) -> None:
        super().__init__()
        self.sim = sim
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(4, 4, 4, 4)
        raiz.setSpacing(4)

        franja = QHBoxLayout()
        self.ind = {}
        for clave in ["estado_fsw", "tiempo_mision", "recibidos", "perdidos", "hora", "alt_max"]:
            caja, valor = indicador(con_unidad(clave))
            self.ind[clave] = valor
            franja.addWidget(caja)
        raiz.addLayout(franja)

        medio = QHBoxLayout()
        self.tabla = QTableWidget(len(CAMPOS), 2)
        self.tabla.horizontalHeader().hide()
        self.tabla.verticalHeader().hide()
        self.tabla.setShowGrid(False)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setMinimumSectionSize(20)
        self.tabla.verticalHeader().setDefaultSectionSize(25)
        self.tabla.setFixedWidth(400)
        self.tabla.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for i, c in enumerate(CAMPOS):
            self.tabla.setItem(i, 0, QTableWidgetItem(con_unidad(c["nombre"])))
            it = QTableWidgetItem("—")
            it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla.setItem(i, 1, it)
        medio.addWidget(self.tabla)

        grilla = QGridLayout()
        self.curvas = {}
        for i, (titulo, unidad, series) in enumerate(GRAFICOS_G7):
            w, c = grafico(titulo, unidad, series)
            self.curvas.update(c)
            grilla.addWidget(w, i // 3, i % 3)
        # sexto lugar: temperatura (G8), para cerrar la grilla de 3 × 2
        w, c = grafico(ETIQUETA["temperatura"], UNIDAD["temperatura"], ["temperatura"])
        self.curvas.update(c)
        grilla.addWidget(w, 1, 2)
        medio.addLayout(grilla, 1)
        raiz.addLayout(medio, 1)

        self.comandos = PanelComandos(sim, vertical=False)
        raiz.addWidget(self.comandos)

    def actualizar(self) -> None:
        s, p = self.sim, self.sim.ultimo
        self.ind["estado_fsw"].setText(p["estado_fsw"])
        self.ind["tiempo_mision"].setText(fmt("tiempo_mision", p["tiempo_mision"]))
        self.ind["recibidos"].setText(fmt("", s.recibidos))
        self.ind["perdidos"].setText(fmt("", s.perdidos))
        self.ind["perdidos"].setStyleSheet("color: #b03a2e" if s.perdidos else "")
        self.ind["hora"].setText(p["hora"])
        self.ind["alt_max"].setText(fmt("altitud", s.alt_max))
        for i, c in enumerate(CAMPOS):
            self.tabla.item(i, 1).setText(fmt(c["nombre"], p[c["nombre"]]))
        refrescar_curvas(s, self.curvas)
        self.comandos.actualizar()


# --- variante B: altitud protagonista + registro de paquetes --------------


class VarianteB(QWidget):
    nombre = "Altitude first"

    def __init__(self, sim: Simulador) -> None:
        super().__init__()
        self.sim = sim
        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(4, 4, 4, 4)
        raiz.setSpacing(4)

        izq = QVBoxLayout()
        cabeza = QHBoxLayout()
        self.estado = label("—", negrita=True, pt=PT + 14)
        self.alt = label("—", negrita=True, pt=PT + 14)
        cabeza.addWidget(self.estado)
        cabeza.addStretch(1)
        cabeza.addWidget(label(con_unidad("altitud"), pt=PT))
        cabeza.addWidget(self.alt)
        izq.addLayout(cabeza)
        w, self.c_alt = grafico(ETIQUETA["altitud"], UNIDAD["altitud"], ["altitud"])
        izq.addWidget(w, 3)

        # Toda la telemetría en texto (G5) como registro: una fila por paquete,
        # las columnas son los campos del .toml.
        self.tabla = QTableWidget(0, len(CAMPOS))
        self.tabla.setHorizontalHeaderLabels([con_unidad(c["nombre"]) for c in CAMPOS])
        self.tabla.verticalHeader().hide()
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla.verticalHeader().setDefaultSectionSize(28)
        izq.addWidget(self.tabla, 2)
        raiz.addLayout(izq, 3)

        der = QVBoxLayout()
        cifras = QGridLayout()
        self.ind = {}
        for i, clave in enumerate(
            ["tiempo_mision", "hora", "recibidos", "perdidos", "temperatura", "gps"]
        ):
            caja, valor = indicador("GPS [°]" if clave == "gps" else con_unidad(clave))
            if clave == "gps":
                valor.setFont(label(pt=PT).font())
            self.ind[clave] = valor
            cifras.addWidget(caja, i // 2, i % 2)
        der.addLayout(cifras)
        self.curvas = {}
        for titulo, unidad, series in GRAFICOS_G7[1:]:
            w, c = grafico(titulo, unidad, series)
            w.setLabel("bottom", "")
            self.curvas.update(c)
            der.addWidget(w, 1)
        self.comandos = PanelComandos(sim, vertical=True)
        der.addWidget(self.comandos)
        raiz.addLayout(der, 2)
        self._filas = 0

    def actualizar(self) -> None:
        s, p = self.sim, self.sim.ultimo
        self.estado.setText(p["estado_fsw"])
        self.alt.setText(fmt("altitud", p["altitud"]))
        self.ind["tiempo_mision"].setText(fmt("tiempo_mision", p["tiempo_mision"]))
        self.ind["hora"].setText(p["hora"])
        self.ind["recibidos"].setText(fmt("", s.recibidos))
        self.ind["perdidos"].setText(fmt("", s.perdidos))
        self.ind["perdidos"].setStyleSheet("color: #b03a2e" if s.perdidos else "")
        self.ind["temperatura"].setText(fmt("temperatura", p["temperatura"]))
        self.ind["gps"].setText(
            f"{fmt('gps_latitud', p['gps_latitud'])}  {fmt('gps_longitud', p['gps_longitud'])}"
            f"  ({p['gps_satelites']} sats)"
        )
        refrescar_curvas(s, self.c_alt)
        refrescar_curvas(s, self.curvas)
        if s.recibidos != self._filas:
            self._filas = s.recibidos
            self.tabla.insertRow(0)
            for j, c in enumerate(CAMPOS):
                self.tabla.setItem(0, j, QTableWidgetItem(fmt(c["nombre"], p[c["nombre"]])))
            if self.tabla.rowCount() > 50:
                self.tabla.removeRow(50)
            if self._filas < 3:
                self.tabla.resizeColumnsToContents()
        self.comandos.actualizar()


# --- variante C: tablero por subsistema -----------------------------------


class Tarjeta(QFrame):
    """Un subsistema: título, sus valores en texto y (opcional) su gráfico."""

    def __init__(self, titulo: str, campos: list[str], graf=None) -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("Tarjeta { border: 2px solid #555; border-radius: 4px; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(6, 4, 6, 4)
        v.setSpacing(2)
        v.addWidget(label(titulo, negrita=True, pt=PT + 2))
        filas = QGridLayout()
        filas.setHorizontalSpacing(10)
        filas.setVerticalSpacing(0)
        self.valores = {}
        for i, nombre in enumerate(campos):
            fila, col = (i, 0) if graf is None or len(campos) <= 3 else (i % 3, (i // 3) * 2)
            filas.addWidget(label(con_unidad(nombre)), fila, col)
            val = label("—", negrita=True, alinear=Qt.AlignmentFlag.AlignRight)
            self.valores[nombre] = val
            filas.addWidget(val, fila, col + 1)
        v.addLayout(filas)
        if graf is None:
            v.addStretch(1)
        self.curvas = {}
        if graf is not None:
            w, self.curvas = grafico(*graf)
            w.setLabel("bottom", "")
            v.addWidget(w, 1)

    def actualizar(self, sim: Simulador, extra: dict | None = None) -> None:
        datos = {**sim.ultimo, **(extra or {})}
        for nombre, val in self.valores.items():
            prefijo = getattr(self, "prefijos", {}).get(nombre, "")
            val.setText(prefijo + fmt(nombre, datos[nombre]))
        refrescar_curvas(sim, self.curvas)


class VarianteC(QWidget):
    nombre = "Subsystem board"

    def __init__(self, sim: Simulador) -> None:
        super().__init__()
        self.sim = sim
        g = QGridLayout(self)
        g.setContentsMargins(4, 4, 4, 4)
        g.setSpacing(4)
        self.tarjetas = [
            Tarjeta(
                "Mission",
                [
                    "estado_fsw",
                    "contador",
                    "tiempo_mision",
                    "hora",
                    "recibidos",
                    "perdidos",
                    "descartados",
                ],
            ),
            Tarjeta(
                "Flight",
                ["altitud", "presion", "temperatura"],
                (ETIQUETA["altitud"], UNIDAD["altitud"], ["altitud"]),
            ),
            Tarjeta(
                "Power",
                ["tension_bateria", "corriente_bateria"],
                (ETIQUETA["tension_bateria"], UNIDAD["tension_bateria"], ["tension_bateria"]),
            ),
            Tarjeta(
                "Acceleration",
                ["acel_x", "acel_y", "acel_z"],
                ("Acceleration", "m/s²", ["acel_x", "acel_y", "acel_z"]),
            ),
            Tarjeta(
                "Rotation rate",
                ["rot_x", "rot_y", "rot_z"],
                ("Rotation rate", "°/s", ["rot_x", "rot_y", "rot_z"]),
            ),
            Tarjeta(
                "GPS",
                ["gps_latitud", "gps_longitud", "gps_altitud", "gps_satelites"],
            ),
        ]
        # La corriente también tiene que graficarse (G7): segunda curva en Energía.
        energia = self.tarjetas[2]
        w = energia.findChild(pg.PlotWidget)
        energia.curvas["corriente_bateria"] = w.plot(pen=pg.mkPen(COLORES["dos"], width=TRAZO))
        titulo = f"{con_unidad('tension_bateria')} and {con_unidad('corriente_bateria')}"
        w.setTitle(f"<b>{titulo}</b>", size=f"{PT}pt")

        g.addWidget(self.tarjetas[0], 0, 0)
        g.addWidget(self.tarjetas[1], 0, 1, 1, 2)
        g.addWidget(self.tarjetas[5], 1, 0)
        g.addWidget(self.tarjetas[2], 1, 1)
        g.addWidget(self.tarjetas[3], 1, 2)
        comandos = QFrame()
        comandos.setFrameShape(QFrame.Shape.StyledPanel)
        cv = QVBoxLayout(comandos)
        cv.setContentsMargins(4, 4, 4, 4)
        cv.addWidget(label("Telecommands", negrita=True, pt=PT + 2))
        self.comandos = PanelComandos(sim, vertical=True)
        cv.addWidget(self.comandos)
        g.addWidget(comandos, 0, 3)
        g.addWidget(self.tarjetas[4], 1, 3)
        for col, estirar in enumerate([2, 3, 3, 3]):
            g.setColumnStretch(col, estirar)
        g.setRowStretch(0, 1)
        g.setRowStretch(1, 1)

    def actualizar(self) -> None:
        extra = {
            "recibidos": self.sim.recibidos,
            "perdidos": self.sim.perdidos,
            "descartados": self.sim.descartados,
        }
        for t in self.tarjetas:
            t.actualizar(self.sim, extra)
        self.comandos.actualizar()


# --- variantes D, E y F: híbridos A + C (ronda 2 de la #7) ----------------

# Formas cortas donde la etiqueta entera no entra; la etiqueta va en el tooltip.
ETIQUETA_GCS = {
    **{f"acel_{e}": f"{e} [m/s²]" for e in "xyz"},
    **{f"rot_{e}": f"{e} [°/s]" for e in "xyz"},
}
FASES = ["STANDBY", "ASCENT", "DESCENT_1", "DESCENT_2", "LANDED"]


def indice_fase(estado: str) -> int:
    """BOOT (tras un reinicio) no es una fase de la barra: no se marca ninguna."""
    return FASES.index(estado) if estado in FASES else -1


BANDA = {"DESCENT_1": (15, 3, "C3"), "DESCENT_2": (5, 3, "C4")}  # bajada [m/s]
NIVEL = {
    "ok": "background: #e8f6ee; color: #145a32; border: 2px solid #1e8449;",
    "aviso": "background: #fdf2e0; color: #6e4608; border: 2px solid #b9770e;",
    "error": "background: #b03a2e; color: white; border: 2px solid #78281f;",
    "nada": "background: #f2f2f2; color: #333; border: 2px solid #999;",
}


def inicio_ventana(sim: Simulador, modo: str) -> float:
    """En vivo: los últimos HISTORIA s. Histórico: desde que sale de STANDBY."""
    if modo == "historico" and sim.t_lanzamiento is not None:
        return sim.t_lanzamiento
    return sim.tiempos[-1] - HISTORIA


def estado_gcs(sim: Simulador, widget: QWidget) -> list[tuple[str, str, str]]:
    """Las cuatro condiciones de la GCS: (título, texto, nivel)."""
    sin_rx = sim.reloj - sim.ultimo_rx
    if sin_rx > 3:
        enlace = ("Link", f"LINK LOST {fmt('', sin_rx)} s", "error")
    else:
        enlace = ("Link", f"{sim.rssi:.0f} dBm · {sim.snr:.1f} dB", "ok")
    if sim.pendrive:
        pendrive = ("USB drive", "AVUTARDO", "ok")
    else:
        pendrive = ("USB drive", "NO USB DRIVE", "error")
    if FORMATO.get("provisorio"):
        formato = ("Format", "PROVISIONAL", "aviso")
    else:
        formato = ("Format", f"v{FORMATO.get('version', '?')}", "ok")
    geo = widget.screen().availableGeometry()
    ancho, alto = geo.width(), geo.height()
    if ancho >= 1366 and alto >= 768:
        pantalla = ("Screen", f"{ancho}×{alto}", "ok")
    else:
        pantalla = ("Screen", f"LOW {ancho}×{alto}", "aviso")
    return [enlace, pendrive, formato, pantalla]


def texto_banda(sim: Simulador) -> tuple[str, str]:
    """La nota de la velocidad vertical: calculada en la GCS, contra C3 o C4."""
    estado = sim.ultimo["estado_fsw"]
    if estado not in BANDA:
        return "Vertical speed calculated by the GCS (not a telemetry field)", "nada"
    objetivo, tol, req = BANDA[estado]
    bajada = -sim.vel_vertical
    nivel = "ok" if abs(bajada - objetivo) <= tol else "error"
    marca = "in range" if nivel == "ok" else "OUT OF RANGE"
    return (
        f"Descent rate {bajada:.1f} m/s · expected {objetivo} ± {tol} ({req}): {marca}"
        " · calculated by the GCS",
        nivel,
    )


class TarjetaH(QFrame):
    """Un subsistema: valores en texto, gráficos y su propio toggle de modo."""

    def __init__(self, titulo: str, filas: list[str], graficos=(), columnas: int = 1) -> None:
        super().__init__()
        self.setObjectName("tarjeta")
        self.setStyleSheet("#tarjeta { border: 2px solid #555; border-radius: 4px; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(6, 4, 6, 4)
        v.setSpacing(2)
        # columnas=0: x, y, z en una línea; cada uno con el color de su curva
        # hace de leyenda, y la unidad sube al título de la tarjeta.
        en_linea = columnas == 0
        if en_linea:
            titulo = f"{titulo} [{graficos[0][1]}]"
        cab = QHBoxLayout()
        cab.addWidget(label(titulo, negrita=True, pt=PT + 2))
        cab.addStretch(1)
        self.boton = None
        if graficos:
            self.boton = QPushButton()
            self.boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.boton.clicked.connect(
                lambda: self.poner_modo("vivo" if self.modo == "historico" else "historico")
            )
            cab.addWidget(self.boton)
        v.addLayout(cab)
        grilla = QGridLayout()
        grilla.setHorizontalSpacing(4 if en_linea else 10)
        grilla.setVerticalSpacing(0)
        por_col = len(filas) if en_linea else math.ceil(len(filas) / columnas)
        self.valores = {}
        self.prefijos = {}  # en línea, la letra va en el mismo label que el valor
        for i, nombre in enumerate(filas):
            if en_linea:
                eje = nombre[-1]
                self.prefijos[nombre] = f"<span style='color:{COLORES[eje]}'>{eje}</span>&nbsp;"
                val = label("—", negrita=True)
                val.setToolTip(con_unidad(nombre))
                self.valores[nombre] = val
                grilla.addWidget(val, 0, i)
                grilla.setColumnStretch(i, 1)
                continue
            f, c = i % por_col, (i // por_col) * 2
            rotulo = label(ETIQUETA_GCS.get(nombre) or con_unidad(nombre))
            rotulo.setToolTip(con_unidad(nombre))
            grilla.addWidget(rotulo, f, c)
            val = label("—", negrita=True, alinear=Qt.AlignmentFlag.AlignRight)
            self.valores[nombre] = val
            grilla.addWidget(val, f, c + 1)
        v.addLayout(grilla)
        self.nota = label()
        self.nota.setWordWrap(True)
        self.nota.hide()
        v.addWidget(self.nota)
        self.curvas: dict = {}
        self.plots: list[pg.PlotWidget] = []
        if graficos:
            h = QHBoxLayout()
            for g in graficos:
                w, c = grafico(*g)
                w.setLabel("bottom", "")
                if en_linea:  # el título y la leyenda ya están arriba
                    w.setTitle(None)
                    w.plotItem.legend.hide()
                # Que el alto lo repartan las filas de la grilla, no el gráfico.
                w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
                w.setMinimumHeight(140)
                self.curvas.update(c)
                self.plots.append(w)
                h.addWidget(w)
            v.addLayout(h, 1)
        else:
            v.addStretch(1)
        self.poner_modo("vivo")

    def poner_modo(self, modo: str) -> None:
        self.modo = modo
        if self.boton is not None:
            self.boton.setText(f"Live ({HISTORIA} s)" if modo == "vivo" else "History (mission)")
            self.boton.setStyleSheet(
                "" if modo == "vivo" else "QPushButton { background: #1f4e9c; color: white; }"
            )
        for w in self.plots:
            # En histórico se puede hacer zoom y arrastrar; en vivo, no.
            w.setMouseEnabled(modo == "historico", modo == "historico")
            w.enableAutoRange()

    def actualizar(self, sim: Simulador, datos: dict) -> None:
        for nombre, val in self.valores.items():
            prefijo = getattr(self, "prefijos", {}).get(nombre, "")
            val.setText(prefijo + fmt(nombre, datos[nombre]))
        refrescar_curvas(sim, self.curvas, inicio_ventana(sim, self.modo))


class Franja(QWidget):
    """Arriba de todo: estado, tiempos, contadores, eco y el toggle global."""

    CLAVES = ["estado_fsw", "tiempo_mision", "hora", "recibidos", "perdidos", "descartados", "eco"]

    def __init__(self, con_estado: bool = True) -> None:
        super().__init__()
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        self.ind = {}
        for clave in self.CLAVES:
            if clave == "estado_fsw" and not con_estado:
                continue
            caja, valor = indicador(con_unidad(clave))
            self.ind[clave] = valor
            h.addWidget(caja, 1)
        self.toggle = QPushButton("All: Live")
        self.toggle.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.toggle.setMinimumHeight(48)
        h.addWidget(self.toggle)

    def actualizar(self, datos: dict) -> None:
        for clave, valor in self.ind.items():
            valor.setText(fmt(clave, datos[clave]) if datos[clave] != "" else "—")
        self.ind["perdidos"].setStyleSheet("color: #b03a2e" if datos["perdidos"] else "")
        self.ind["descartados"].setStyleSheet("color: #b03a2e" if datos["descartados"] else "")


def chip(texto: str, nivel: str) -> QLabel:
    lb = label(texto, negrita=True)
    lb.setStyleSheet(NIVEL[nivel] + "border-radius: 12px; padding: 2px 12px;")
    return lb


class Hibrido(QWidget):
    """Lo común de D, E y F: franja, tarjetas y el toggle global."""

    nombre = ""
    gps_en_vuelo = False
    con_estado = True
    clase_tarjeta = TarjetaH
    clase_franja = Franja
    columnas_xyz = 3

    def __init__(self, sim: Simulador) -> None:
        super().__init__()
        self.sim = sim
        self.franja = self.clase_franja(self.con_estado)
        self.modo_global = "vivo"
        self.franja.toggle.clicked.connect(self.alternar_global)
        gps = ["gps_latitud", "gps_longitud", "gps_altitud", "gps_satelites"]
        vuelo = ["altitud", "vel_vertical", "presion", "temperatura"]
        self.t = {
            "vuelo": self.clase_tarjeta(
                "Flight and GPS" if self.gps_en_vuelo else "Flight",
                vuelo + (gps if self.gps_en_vuelo else []),
                [(ETIQUETA["altitud"], UNIDAD["altitud"], ["altitud"])],
                columnas=2,
            ),
            "energia": self.tarjeta_energia(),
            "acel": self.clase_tarjeta(
                "Accel.",
                ["acel_x", "acel_y", "acel_z"],
                [("Acceleration", "m/s²", ["acel_x", "acel_y", "acel_z"])],
                columnas=self.columnas_xyz,
            ),
            "rot": self.clase_tarjeta(
                "Rotation",
                ["rot_x", "rot_y", "rot_z"],
                [("Rotation rate", "°/s", ["rot_x", "rot_y", "rot_z"])],
                columnas=self.columnas_xyz,
            ),
        }
        if not self.gps_en_vuelo:
            self.t["gps"] = self.clase_tarjeta("GPS", gps)
        self.t["vuelo"].nota.show()

    def tarjeta_energia(self) -> QFrame:
        """La tarjeta de energía de las rondas 2 a 4; la ronda 5 la reemplaza."""
        return self.clase_tarjeta(
            "Power",
            ["tension_bateria", "corriente_bateria"],
            [
                (ETIQUETA["tension_bateria"], UNIDAD["tension_bateria"], ["tension_bateria"]),
                (ETIQUETA["corriente_bateria"], UNIDAD["corriente_bateria"], ["corriente_bateria"]),
            ],
            columnas=2,
        )

    def alternar_global(self) -> None:
        self.modo_global = "historico" if self.modo_global == "vivo" else "vivo"
        for t in self.t.values():
            t.poner_modo(self.modo_global)
        texto = "Live" if self.modo_global == "vivo" else "History"
        self.franja.toggle.setText(f"All: {texto}")

    def actualizar(self) -> None:
        s = self.sim
        datos = {
            **s.ultimo,
            "recibidos": s.recibidos,
            "perdidos": s.perdidos,
            "descartados": s.descartados,
            "vel_vertical": s.vel_vertical,
            "eco": texto_eco(s.ultimo),
        }
        self.franja.actualizar(datos)
        for t in self.t.values():
            t.actualizar(s, datos)
        texto, nivel = texto_banda(s)
        nota = self.t["vuelo"].nota
        nota.setText(texto)
        nota.setStyleSheet(NIVEL[nivel] + "padding: 2px 6px;")
        self.comandos.actualizar()
        self.actualizar_avisos(estado_gcs(s, self))

    def actualizar_avisos(self, condiciones) -> None:
        raise NotImplementedError

    def grilla_3x2(self) -> QGridLayout:
        g = QGridLayout()
        g.setSpacing(4)
        g.addWidget(self.t["vuelo"], 0, 0)
        g.addWidget(self.t["energia"], 0, 1, 1, 2)
        g.addWidget(self.t["acel"], 1, 0)
        g.addWidget(self.t["rot"], 1, 1)
        g.addWidget(self.t["gps"], 1, 2)
        g.setColumnStretch(0, 1)
        g.setColumnStretch(1, 1)
        g.setColumnStretch(2, 1)
        g.setRowStretch(0, 3)
        g.setRowStretch(1, 2)
        return g


class VarianteD(Hibrido):
    nombre = "Hybrid: status chips"

    def __init__(self, sim: Simulador) -> None:
        super().__init__(sim)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(4, 4, 4, 4)
        raiz.setSpacing(4)
        raiz.addWidget(self.franja)
        fila = QHBoxLayout()
        self.chips = []
        for _ in range(4):
            c = chip("—", "nada")
            self.chips.append(c)
            fila.addWidget(c)
        fila.addStretch(1)
        raiz.addLayout(fila)
        raiz.addLayout(self.grilla_3x2(), 1)
        self.comandos = PanelComandos(sim, vertical=False, mostrar_eco=False)
        raiz.addWidget(self.comandos)

    def actualizar_avisos(self, condiciones) -> None:
        for c, (titulo, texto, nivel) in zip(self.chips, condiciones, strict=True):
            c.setText(f"{titulo}: {texto}")
            c.setStyleSheet(NIVEL[nivel] + "border-radius: 12px; padding: 2px 12px;")


class VarianteE(Hibrido):
    nombre = "Hybrid: phases + status footer"
    con_estado = False  # el estado lo cuenta la barra de fases

    def __init__(self, sim: Simulador) -> None:
        super().__init__(sim)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(4, 4, 4, 0)
        raiz.setSpacing(4)
        raiz.addWidget(self.franja)
        fases = QHBoxLayout()
        fases.setSpacing(2)
        self.fases = []
        for f in FASES:
            lb = label(f, negrita=True, alinear=Qt.AlignmentFlag.AlignCenter)
            self.fases.append(lb)
            fases.addWidget(lb, 1)
        raiz.addLayout(fases)
        medio = QHBoxLayout()
        medio.addLayout(self.grilla_3x2(), 1)
        caja = QFrame()
        caja.setObjectName("comandos")
        caja.setStyleSheet("#comandos { border: 2px solid #555; border-radius: 4px; }")
        caja.setFixedWidth(250)
        cv = QVBoxLayout(caja)
        cv.setContentsMargins(4, 4, 4, 4)
        cv.addWidget(label("Telecommands", negrita=True, pt=PT + 2))
        self.comandos = PanelComandos(sim, vertical=True, mostrar_eco=False)
        cv.addWidget(self.comandos)
        cv.addStretch(1)
        medio.addWidget(caja)
        raiz.addLayout(medio, 1)
        pie = QFrame()
        pie.setObjectName("pie")
        pie.setStyleSheet("#pie { background: #f2f2f2; border-top: 2px solid #999; }")
        ph = QHBoxLayout(pie)
        ph.setContentsMargins(8, 2, 8, 2)
        ph.addWidget(label("GCS", negrita=True))
        self.pie = []
        for _ in range(4):
            lb = label("—")
            self.pie.append(lb)
            ph.addWidget(lb, 1)
        raiz.addWidget(pie)

    def actualizar(self) -> None:
        super().actualizar()
        actual = indice_fase(self.sim.ultimo["estado_fsw"])
        for i, lb in enumerate(self.fases):
            if i == actual:
                estilo = "background: #1f4e9c; color: white; border: 2px solid #1f4e9c;"
            elif i < actual:
                estilo = "background: #d6dde8; color: #333; border: 2px solid #d6dde8;"
            else:
                estilo = "background: white; color: #666; border: 2px solid #bbb;"
            lb.setStyleSheet(estilo + "padding: 2px;")

    def actualizar_avisos(self, condiciones) -> None:
        colores = {"ok": "#145a32", "aviso": "#8a5a0b", "error": "#b03a2e"}
        for lb, (titulo, texto, nivel) in zip(self.pie, condiciones, strict=True):
            marca = "●" if nivel == "ok" else "▲"
            lb.setText(
                f"<span style='color:{colores[nivel]}'>{marca}</span> {titulo}: <b>{texto}</b>"
            )
            lb.setStyleSheet(
                "background: #b03a2e; color: white;" if nivel == "error" else "color: black;"
            )


class VarianteF(Hibrido):
    nombre = "Hybrid: warning line"
    gps_en_vuelo = True

    def __init__(self, sim: Simulador) -> None:
        super().__init__(sim)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(4, 4, 4, 4)
        raiz.setSpacing(4)
        raiz.addWidget(self.franja)
        self.linea = label("No warnings", negrita=True)
        self.linea.setFixedHeight(32)
        raiz.addWidget(self.linea)
        g = QGridLayout()
        g.setSpacing(4)
        g.addWidget(self.t["vuelo"], 0, 0, 2, 1)
        g.addWidget(self.t["energia"], 0, 1, 1, 2)
        g.addWidget(self.t["acel"], 1, 1)
        g.addWidget(self.t["rot"], 1, 2)
        g.setColumnStretch(0, 4)
        g.setColumnStretch(1, 3)
        g.setColumnStretch(2, 3)
        g.setRowStretch(0, 3)
        g.setRowStretch(1, 2)
        raiz.addLayout(g, 1)
        self.comandos = PanelComandos(sim, vertical=False, mostrar_eco=False)
        raiz.addWidget(self.comandos)

    def actualizar_avisos(self, condiciones) -> None:
        malos = [(t, x, n) for t, x, n in condiciones if n != "ok"]
        if not malos:
            self.linea.setText("No warnings")
            nivel = "nada"
        else:
            self.linea.setText("   ▲   ".join(f"{t}: {x}" for t, x, _ in malos))
            nivel = "error" if any(n == "error" for *_, n in malos) else "aviso"
        self.linea.setStyleSheet(NIVEL[nivel] + "padding: 2px 8px;")


# --- variante G: lo elegido en la ronda 2 de la #7 ------------------------

VENTANAS = [("30 s", 30), ("60 s", 60), ("120 s", 120), ("Mission", None)]
TRANSICION = 5  # s en ámbar tras un cambio de estado


def combo_ventana(prefijo: str = "") -> QComboBox:
    c = QComboBox()
    c.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    for texto, seg in VENTANAS:
        c.addItem(prefijo + texto, seg)
    c.setCurrentIndex(2)  # 120 s
    return c


class TarjetaG(TarjetaH):
    """Como TarjetaH, pero la ventana se elige entre 30, 60, 120 s y Misión."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.combo = None
        if self.boton is not None:
            self.boton.hide()
            self.combo = combo_ventana()
            self.combo.currentIndexChanged.connect(
                lambda _: self.poner_modo(self.combo.currentData())
            )
            self.layout().itemAt(0).layout().addWidget(self.combo)
        self.poner_modo(120)

    def poner_modo(self, modo) -> None:
        if modo in ("vivo", "historico"):  # lo que llama TarjetaH al construirse
            modo = 120 if modo == "vivo" else None
        self.modo = modo
        if getattr(self, "combo", None) is not None:
            self.combo.blockSignals(True)
            self.combo.setCurrentIndex([s for _, s in VENTANAS].index(modo))
            self.combo.blockSignals(False)
        for w in self.plots:
            w.setMouseEnabled(modo is None, modo is None)  # zoom sólo en Misión
            w.enableAutoRange()

    def actualizar(self, sim: Simulador, datos: dict) -> None:
        for nombre, val in self.valores.items():
            prefijo = getattr(self, "prefijos", {}).get(nombre, "")
            val.setText(prefijo + fmt(nombre, datos[nombre]))
        if self.modo is None and sim.t_lanzamiento is not None:
            inicio = sim.t_lanzamiento
        else:
            inicio = sim.tiempos[-1] - (self.modo or HISTORIA)
        refrescar_curvas(sim, self.curvas, inicio)


def pixmap_qr(texto: str, lado: int) -> QPixmap | None:
    """QR del texto, o None si no está `segno` (uv run --with segno ...)."""
    try:
        import segno
    except ImportError:
        return None
    filas = [list(f) for f in segno.make(texto, error="m").matrix]
    n = len(filas) + 8  # 4 módulos de margen por lado
    img = QImage(n, n, QImage.Format.Format_RGB32)
    img.fill(QColor("white"))
    for y, fila in enumerate(filas):
        for x, m in enumerate(fila):
            if m:
                img.setPixel(x + 4, y + 4, QColor("black").rgb())
    return QPixmap.fromImage(img).scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatio)


class TarjetaRecorrido(QFrame):
    """El recorrido en metros desde el punto de lanzamiento; en LANDED, un QR
    con la última posición para el equipo de recuperación."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("tarjeta")
        self.setStyleSheet("#tarjeta { border: 2px solid #555; border-radius: 4px; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(6, 4, 6, 4)
        v.setSpacing(2)
        cab = QHBoxLayout()
        self.titulo = label("Ground track", negrita=True, pt=PT + 2)
        cab.addWidget(self.titulo)
        cab.addStretch(1)
        self.boton = QPushButton("QR")
        self.boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.boton.clicked.connect(self.alternar)
        self.boton.hide()
        cab.addWidget(self.boton)
        v.addLayout(cab)
        self.pila = QStackedWidget()
        self.plot = pg.PlotWidget()
        fuente = QFont()
        fuente.setPointSize(PT)
        fuente.setBold(True)
        for lado, texto in (("left", "North [m]"), ("bottom", "East [m]")):
            eje = self.plot.getAxis(lado)
            eje.setPen(pg.mkPen("k", width=2))
            eje.setTextPen("k")
            eje.setStyle(tickFont=fuente)
            self.plot.setLabel(lado, texto, color="#000", **{"font-size": f"{PT}pt"})
        self.plot.setAspectLocked(True)
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setMouseEnabled(False, False)
        self.plot.hideButtons()
        self.plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.plot.setMinimumHeight(140)
        self.traza = self.plot.plot(pen=pg.mkPen(COLORES["uno"], width=TRAZO))
        self.base = self.plot.plot(
            symbol="t", symbolSize=14, symbolBrush="#1e8449", pen=None
        )  # lanzamiento
        self.punto = self.plot.plot(symbol="o", symbolSize=14, symbolBrush="#c0392b", pen=None)
        self.pila.addWidget(self.plot)
        qr = QWidget()
        qv = QVBoxLayout(qr)
        qv.setContentsMargins(0, 0, 0, 0)
        self.qr = QLabel()
        self.qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        qv.addWidget(self.qr, 1)
        self.coords = label(negrita=True, alinear=Qt.AlignmentFlag.AlignCenter)
        qv.addWidget(self.coords)
        self.pila.addWidget(qr)
        v.addWidget(self.pila, 1)
        self.vio_aterrizaje = False
        self.ultimo_qr = ""

    def alternar(self) -> None:
        ver_qr = self.pila.currentIndex() == 0
        self.pila.setCurrentIndex(1 if ver_qr else 0)
        self.boton.setText("Map" if ver_qr else "QR")

    def poner_modo(self, modo) -> None:
        pass  # el recorrido es siempre la misión entera

    def actualizar(self, sim: Simulador, datos: dict) -> None:
        if sim.t_lanzamiento is None:
            return
        i = bisect.bisect_left(sim.tiempos, sim.t_lanzamiento)
        pares = zip(sim.historia["gps_latitud"][i:], sim.historia["gps_longitud"][i:], strict=True)
        con_fix = [(la, lo) for la, lo in pares if not math.isnan(la)]
        if not con_fix:
            return
        lats, lons = [la for la, _ in con_fix], [lo for _, lo in con_fix]
        lat0, lon0 = lats[0], lons[0]
        k = 111_320.0
        xs = [(lo - lon0) * k * math.cos(math.radians(lat0)) for lo in lons]
        ys = [(la - lat0) * k for la in lats]
        self.traza.setData(xs, ys)
        self.base.setData([0], [0])
        self.punto.setData(xs[-1:], ys[-1:])
        if datos["estado_fsw"] == "LANDED":
            lat, lon = lats[-1], lons[-1]  # la última posición con fix
            texto = f"https://maps.google.com/?q={lat:.6f},{lon:.6f}"
            if texto != self.ultimo_qr:
                self.ultimo_qr = texto
                lado = max(80, min(self.pila.width(), self.pila.height() - 30))
                px = pixmap_qr(texto, lado)
                if px is None:
                    self.qr.setText("(segno missing:\nuv run --with segno ...)")
                else:
                    self.qr.setPixmap(px)
            self.coords.setText(f"{lat:.6f}\n{lon:.6f}")
            if not self.vio_aterrizaje:  # al aterrizar pasa solo al QR, una vez
                self.vio_aterrizaje = True
                self.boton.show()
                self.alternar()


class VarianteG(Hibrido):
    nombre = "Round 2: phases + footer, flight and GPS, ground track"
    gps_en_vuelo = True
    con_estado = False  # el estado lo cuenta la barra de fases
    clase_tarjeta = TarjetaG
    columnas_xyz = 1  # x, y, z apiladas: si no, no entra en 1366 px
    ancho_comandos = 230

    def __init__(self, sim: Simulador) -> None:
        super().__init__(sim)
        self.t["vuelo"].nota.hide()  # Q7: menos texto; la banda va en el color
        self.t["recorrido"] = TarjetaRecorrido()
        # El toggle global elige la ventana de todas las tarjetas a la vez.
        self.franja.toggle.hide()
        self.global_ = combo_ventana("All: ")
        self.global_.setMinimumHeight(48)
        self.global_.currentIndexChanged.connect(
            lambda _: [t.poner_modo(self.global_.currentData()) for t in self.t.values()]
        )
        self.franja.layout().addWidget(self.global_)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(4, 4, 4, 0)
        raiz.setSpacing(4)
        raiz.addWidget(self.franja)
        fases = QHBoxLayout()
        fases.setSpacing(2)
        self.fases = []
        for f in FASES:
            lb = label(f, negrita=True, alinear=Qt.AlignmentFlag.AlignCenter)
            self.fases.append(lb)
            fases.addWidget(lb, 1)
        raiz.addLayout(fases)
        medio = QHBoxLayout()
        medio.setSpacing(4)
        self.grilla = QGridLayout()
        g = self.grilla
        g.setSpacing(4)
        medio.addLayout(g, 1)
        columna = QVBoxLayout()
        columna.setContentsMargins(0, 0, 0, 0)
        columna.setSpacing(4)
        caja = QFrame()
        caja.setObjectName("comandos")
        caja.setStyleSheet("#comandos { border: 2px solid #555; border-radius: 4px; }")
        cv = QVBoxLayout(caja)
        cv.setContentsMargins(4, 4, 4, 4)
        cv.addWidget(label("Telecommands", negrita=True, pt=PT + 2))
        self.caja_comandos = caja  # el recorte de `standby`
        self.comandos = self.panel_comandos(sim)
        cv.addWidget(self.comandos)
        columna.addWidget(caja)
        contenedor = QWidget()
        contenedor.setLayout(columna)
        contenedor.setFixedWidth(self.ancho_comandos)
        medio.addWidget(contenedor)
        self.ubicar(g, columna)
        raiz.addLayout(medio, 1)
        pie = QFrame()
        pie.setObjectName("pie")
        pie.setStyleSheet("#pie { background: #f2f2f2; border-top: 2px solid #999; }")
        ph = QHBoxLayout(pie)
        ph.setContentsMargins(8, 2, 8, 2)
        ph.addWidget(label("GCS", negrita=True))
        self.pie = []
        for _ in range(4):
            lb = label("—")
            self.pie.append(lb)
            ph.addWidget(lb, 1)
        raiz.addWidget(pie)

    def panel_comandos(self, sim: Simulador) -> QWidget:
        return PanelComandos(sim, vertical=True, mostrar_eco=False)

    def actualizar(self) -> None:
        super().actualizar()
        s = self.sim
        actual = indice_fase(s.ultimo["estado_fsw"])
        for i, lb in enumerate(self.fases):
            if i == actual:
                estilo = "background: #1f4e9c; color: white; border: 2px solid #1f4e9c;"
            elif i < actual:
                estilo = "background: #d6dde8; color: #333; border: 2px solid #d6dde8;"
            else:
                estilo = "background: white; color: #666; border: 2px solid #bbb;"
            lb.setStyleSheet(estilo + "padding: 2px;")
        # Q7: la velocidad vertical con la banda en el color y casi sin texto.
        val = self.t["vuelo"].valores["vel_vertical"]
        estado = s.ultimo["estado_fsw"]
        if estado in BANDA:
            objetivo, tol, req = BANDA[estado]
            bajada = -s.vel_vertical
            if s.t - s.t_cambio < TRANSICION:
                nivel = "aviso"
            else:
                nivel = "ok" if abs(bajada - objetivo) <= tol else "error"
            val.setText(f"{s.vel_vertical:.1f} · {req}")
            val.setToolTip(f"Expected descent rate {objetivo} ± {tol} m/s ({req})")
            val.setStyleSheet(NIVEL[nivel] + "padding: 0px 4px;")
        else:
            val.setStyleSheet("")
            val.setToolTip("")

    def actualizar_avisos(self, condiciones) -> None:
        VarianteE.actualizar_avisos(self, condiciones)

    def ubicar(self, g: QGridLayout, columna: QVBoxLayout) -> None:
        """Recorrido arriba a la derecha, al lado de Energía."""
        g.addWidget(self.t["vuelo"], 0, 0, 2, 1)
        g.addWidget(self.t["energia"], 0, 1)
        g.addWidget(self.t["recorrido"], 0, 2)
        g.addWidget(self.t["acel"], 1, 1)
        g.addWidget(self.t["rot"], 1, 2)
        g.setColumnStretch(0, 4)
        g.setColumnStretch(1, 3)
        g.setColumnStretch(2, 3)
        columna.addStretch(1)


class VarianteG2(VarianteG):
    """Ronda 3, Q2: el Recorrido baja a la columna de telecomandos."""

    nombre = "Round 3: ground track under telecommands"
    columnas_xyz = 0  # ronda 4: x, y, z en una línea, la unidad en el título

    def __init__(self, sim: Simulador) -> None:
        super().__init__(sim)
        for w in self.t["energia"].plots:  # ronda 4: la unidad ya está en el texto
            w.setTitle(None)

    def ubicar(self, g: QGridLayout, columna: QVBoxLayout) -> None:
        g.addWidget(self.t["vuelo"], 0, 0, 2, 1)
        g.addWidget(self.t["energia"], 0, 1, 1, 2)
        g.addWidget(self.t["acel"], 1, 1)
        g.addWidget(self.t["rot"], 1, 2)
        g.setColumnStretch(0, 4)
        g.setColumnStretch(1, 3)
        g.setColumnStretch(2, 3)
        columna.addWidget(self.t["recorrido"], 1)


class VarianteG3(VarianteG):
    """Ronda 3, Q2: Vuelo y GPS deja de ser alta y el Recorrido va debajo."""

    nombre = "Round 3: ground track under flight and GPS"

    def ubicar(self, g: QGridLayout, columna: QVBoxLayout) -> None:
        g.addWidget(self.t["vuelo"], 0, 0)
        g.addWidget(self.t["energia"], 0, 1, 1, 2)
        g.addWidget(self.t["recorrido"], 1, 0)
        g.addWidget(self.t["acel"], 1, 1)
        g.addWidget(self.t["rot"], 1, 2)
        g.setColumnStretch(0, 4)
        g.setColumnStretch(1, 3)
        g.setColumnStretch(2, 3)
        g.setRowStretch(0, 3)
        g.setRowStretch(1, 2)
        columna.addStretch(1)


# --- ronda 5 (#23): el bloque de energía ----------------------------------

TENSIONES = ["tension_bateria", "tension_3v3"]
CORRIENTES = ["corriente_bateria", "corriente_3v3"]
CANALES = [  # (tensión, corriente) de cada canal del INA3221
    ("tension_bateria", "corriente_bateria"),
    ("tension_3v3", "corriente_3v3"),
    ("tension_panel", "corriente_panel"),
]
COLOR_CANAL = {"bateria": COLORES["uno"], "3v3": COLORES["dos"], "panel": "#555"}


def canal(nombre: str) -> str:
    return nombre.rsplit("_", 1)[1]  # tension_bateria → bateria


def corto(nombre: str) -> str:
    return ETIQUETA[nombre].split("_")[0]  # BAT_VOLTAGE → BAT


def cabeza_canal(tension: str, **kw) -> QLabel:
    """La forma corta del canal (BAT), con las etiquetas enteras en el tooltip."""
    lb = label(corto(tension), **kw)
    corriente = tension.replace("tension_", "corriente_")
    lb.setToolTip(f"{con_unidad(tension)}, {con_unidad(corriente)}")
    return lb


def rendimiento(d: dict) -> float:
    """Potencia de la barra / potencia de la batería, en %, paquete por paquete.

    Más del 100 % se muestra tal cual: indica un problema de medición. Sin dato
    si falta alguno de los cuatro campos o la batería entrega menos de 0.1 W.
    """
    vb, ib = d.get("tension_bateria", NAN), d.get("corriente_bateria", NAN)
    v3, i3 = d.get("tension_3v3", NAN), d.get("corriente_3v3", NAN)
    if any(math.isnan(x) for x in (vb, ib, v3, i3)) or vb * ib < 0.1:
        return NAN
    return 100 * v3 * i3 / (vb * ib)


def valor_energia(nombre: str, d: dict) -> float:
    if nombre == "rendimiento":
        return rendimiento(d)
    if nombre.startswith("potencia_"):  # sólo G2C: V × A del canal
        c = canal(nombre)
        v, i = (d.get(n, NAN) for n in next(par for par in CANALES if canal(par[0]) == c))
        return v * i
    return d.get(nombre, NAN)


def fmt_energia(nombre: str, valor: float, mostrar_unidad: bool = True) -> str:
    """Tensiones con 2 decimales, corrientes y potencias con 3, % sin decimales."""
    if math.isnan(valor):
        return "—"
    tipo = nombre.split("_")[0]
    dec, unidad = {
        "tension": (2, "V"),
        "corriente": (3, "A"),
        "potencia": (2, "W"),
        "rendimiento": (0, "%"),
    }[tipo]
    texto = agrupar(f"{valor:.{dec}f}")
    return f"{texto} {unidad}" if mostrar_unidad else texto


def plot_energia(alto_minimo: int = 70) -> pg.PlotWidget:
    """Un gráfico sin título ni eje de tiempo rotulado, como los de G2."""
    w = pg.PlotWidget()
    fuente = QFont()
    fuente.setPointSize(PT)
    fuente.setBold(True)
    for lado in ("left", "bottom"):
        eje = w.getAxis(lado)
        eje.setPen(pg.mkPen("k", width=2))
        eje.setTextPen("k")
        eje.setStyle(tickFont=fuente)
    w.showGrid(x=True, y=True, alpha=0.25)
    w.setMouseEnabled(False, False)
    w.hideButtons()
    w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
    w.setMinimumHeight(alto_minimo)
    return w


def eje_derecho(w: pg.PlotWidget, color_izq: str, color_der: str) -> pg.ViewBox:
    """Segundo eje Y a la derecha, con su propia escala; cada eje, del color de
    su curva."""
    pi = w.plotItem
    vista = pg.ViewBox()
    pi.showAxis("right")
    pi.scene().addItem(vista)
    der = pi.getAxis("right")
    der.linkToView(vista)
    vista.setXLink(pi)
    fuente = QFont()
    fuente.setPointSize(PT)
    fuente.setBold(True)
    der.setPen(pg.mkPen("k", width=2))
    der.setStyle(tickFont=fuente)
    der.setTextPen(color_der)
    pi.getAxis("left").setTextPen(color_izq)
    vista.setMouseEnabled(False, False)

    def sincronizar() -> None:
        vista.setGeometry(pi.vb.sceneBoundingRect())
        vista.linkedViewChanged(pi.vb, vista.XAxis)

    pi.vb.sigResized.connect(sincronizar)
    sincronizar()
    return vista


class TarjetaEnergia(QFrame):
    """Lo común de las tres: título, ventana, valores y curvas. Cada variante
    arma su cuerpo en `armar`."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("tarjeta")
        self.setStyleSheet("#tarjeta { border: 2px solid #555; border-radius: 4px; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(6, 4, 6, 4)
        v.setSpacing(2)
        cab = QHBoxLayout()
        cab.addWidget(label("Power", negrita=True, pt=PT + 2))
        cab.addStretch(1)
        self.combo = combo_ventana()
        self.combo.currentIndexChanged.connect(lambda _: self.poner_modo(self.combo.currentData()))
        cab.addWidget(self.combo)
        v.addLayout(cab)
        self.curvas: dict = {}
        self.plots: list[pg.PlotWidget] = []
        self.vistas: list[pg.ViewBox] = []
        # nombre → (label, prefijo html, con unidad)
        self.valores: dict[str, tuple[QLabel, str, bool]] = {}
        self.armar(v)
        self.poner_modo(120)

    def armar(self, v: QVBoxLayout) -> None:
        raise NotImplementedError

    def valor(self, nombre: str, prefijo: str = "", mostrar_unidad: bool = True, **kw) -> QLabel:
        lb = label("—", negrita=True, **kw)
        lb.setToolTip(con_unidad(nombre))
        self.valores[nombre] = (lb, prefijo, mostrar_unidad)
        return lb

    def fila_abajo(self) -> QHBoxLayout:
        """Panel y rendimiento, sin gráfico: la escala del panel aplastaría las
        otras curvas."""
        h = QHBoxLayout()
        h.setSpacing(10)
        h.addWidget(cabeza_canal("tension_panel"))  # SOLAR, una sola vez
        h.addWidget(self.valor("tension_panel"))
        h.addWidget(self.valor("corriente_panel"))
        h.addStretch(1)
        h.addWidget(label("Buck efficiency"))
        h.addWidget(self.valor("rendimiento"))
        return h

    def poner_modo(self, modo) -> None:
        if modo in ("vivo", "historico"):
            modo = 120 if modo == "vivo" else None
        self.modo = modo
        self.combo.blockSignals(True)
        self.combo.setCurrentIndex([s for _, s in VENTANAS].index(modo))
        self.combo.blockSignals(False)
        for w in self.plots:
            w.setMouseEnabled(modo is None, modo is None)
            w.enableAutoRange()
        for vista in self.vistas:
            vista.enableAutoRange()

    def actualizar(self, sim: Simulador, datos: dict) -> None:
        for nombre, (lb, prefijo, mostrar_unidad) in self.valores.items():
            lb.setText(prefijo + fmt_energia(nombre, valor_energia(nombre, datos), mostrar_unidad))
        if self.modo is None and sim.t_lanzamiento is not None:
            inicio = sim.t_lanzamiento
        else:
            inicio = sim.tiempos[-1] - (self.modo or HISTORIA)
        refrescar_curvas(sim, self.curvas, inicio)


def marca(nombre: str, texto: str | None = None) -> str:
    """Texto del color de la curva de su canal: hace de leyenda."""
    color = COLOR_CANAL[canal(nombre)]
    return f"<span style='color:{color}'>{texto or ETIQUETA[nombre]}</span>"


class EnergiaPorMagnitud(TarjetaEnergia):
    """G2A: un gráfico de tensión y otro de corriente, batería y barra en cada
    uno, con los valores al lado. Lo que pide la #23."""

    def armar(self, v: QVBoxLayout) -> None:
        h = QHBoxLayout()
        h.setSpacing(6)
        for grupo in (TENSIONES, CORRIENTES):
            w = plot_energia()
            self.plots.append(w)
            col = QVBoxLayout()
            col.setSpacing(0)
            col.addStretch(1)
            for nombre in grupo:
                pen = pg.mkPen(COLOR_CANAL[canal(nombre)], width=TRAZO)
                self.curvas[nombre] = w.plot(pen=pen)
                col.addWidget(label(marca(nombre)))
                col.addWidget(self.valor(nombre, alinear=Qt.AlignmentFlag.AlignRight))
                col.addSpacing(6)
            col.addStretch(1)
            h.addWidget(w, 1)
            h.addLayout(col)
        v.addLayout(h, 1)
        v.addLayout(self.fila_abajo())


class EnergiaPorCanal(TarjetaEnergia):
    """G2B: una fila por canal; cada gráfico con la tensión en el eje izquierdo
    y la corriente en el derecho."""

    def armar(self, v: QVBoxLayout) -> None:
        cv, ca = COLORES["uno"], COLORES["dos"]
        for tension, corriente in CANALES[:2]:
            h = QHBoxLayout()
            h.setSpacing(6)
            col = QVBoxLayout()
            col.setSpacing(0)
            col.addWidget(cabeza_canal(tension, negrita=True, pt=PT + 2))
            col.addWidget(self.valor(tension, f"<span style='color:{cv}'>V</span>&nbsp;"))
            col.addWidget(self.valor(corriente, f"<span style='color:{ca}'>A</span>&nbsp;"))
            col.addStretch(1)
            caja = QWidget()
            caja.setLayout(col)
            caja.setFixedWidth(130)
            h.addWidget(caja)
            w = plot_energia(60)
            vista = eje_derecho(w, cv, ca)
            self.plots.append(w)
            self.vistas.append(vista)
            self.curvas[tension] = w.plot(pen=pg.mkPen(cv, width=TRAZO))
            curva = pg.PlotCurveItem(pen=pg.mkPen(ca, width=TRAZO))
            vista.addItem(curva)
            self.curvas[corriente] = curva
            h.addWidget(w, 1)
            v.addLayout(h, 1)
        v.addLayout(self.fila_abajo())

    def actualizar(self, sim: Simulador, datos: dict) -> None:
        super().actualizar(sim, datos)
        if self.modo is None:  # en Misión manda el zoom del usuario
            return
        for w, vista, (tension, corriente) in zip(self.plots, self.vistas, CANALES, strict=False):
            rango_minimo(w.plotItem.vb, self.curvas[tension], 0.2)
            rango_minimo(vista, self.curvas[corriente], 0.1)


def rango_minimo(vista: pg.ViewBox, curva, minimo: float) -> None:
    """Autoescala, pero sin bajar de `minimo`: si no, el ruido del INA3221
    (unos 0.01 V) se ve como un salto."""
    _, ys = curva.getData()
    datos = [y for y in (ys if ys is not None else []) if not math.isnan(y)]
    if not datos:
        return
    bajo, alto = min(datos), max(datos)
    if alto - bajo < minimo:
        centro = (bajo + alto) / 2
        vista.setYRange(centro - minimo / 2, centro + minimo / 2, padding=0)
    else:
        vista.enableAutoRange(axis=pg.ViewBox.YAxis)


class EnergiaNumeros(TarjetaEnergia):
    """G2C: los números mandan. Tabla canal × V, A, W, el rendimiento grande, y
    dos gráficos angostos de tensión y corriente al costado."""

    def armar(self, v: QVBoxLayout) -> None:
        h = QHBoxLayout()
        h.setSpacing(8)
        izq = QVBoxLayout()
        izq.setSpacing(2)
        tabla = QGridLayout()
        tabla.setHorizontalSpacing(14)
        tabla.setVerticalSpacing(0)
        for c, titulo in enumerate(("V", "A", "W"), start=1):
            tabla.addWidget(label(titulo, negrita=True, alinear=Qt.AlignmentFlag.AlignRight), 0, c)
        derecha = Qt.AlignmentFlag.AlignRight
        for f, (tension, corriente) in enumerate(CANALES, start=1):
            tabla.addWidget(label(marca(tension, corto(tension)), negrita=True), f, 0)
            potencia = f"potencia_{canal(tension)}"
            for c, nombre in enumerate((tension, corriente, potencia), start=1):
                tabla.addWidget(self.valor(nombre, mostrar_unidad=False, alinear=derecha), f, c)
        izq.addLayout(tabla)
        izq.addStretch(1)
        rend = QHBoxLayout()
        rend.addWidget(label("Buck efficiency"))
        rend.addStretch(1)
        rend.addWidget(self.valor("rendimiento", pt=PT + 8))
        izq.addLayout(rend)
        h.addLayout(izq)
        graficos = QVBoxLayout()
        graficos.setSpacing(2)
        for grupo in (TENSIONES, CORRIENTES):
            w = plot_energia(60)
            self.plots.append(w)
            for nombre in grupo:
                pen = pg.mkPen(COLOR_CANAL[canal(nombre)], width=TRAZO)
                self.curvas[nombre] = w.plot(pen=pen)
            graficos.addWidget(w, 1)
        h.addLayout(graficos, 1)
        v.addLayout(h, 1)


class VarianteG2A(VarianteG2):
    nombre = "Round 5 (#23): power by quantity"

    def tarjeta_energia(self) -> QFrame:
        return EnergiaPorMagnitud()


class VarianteG2B(VarianteG2):
    nombre = "Round 5 (#23): power by channel"

    def tarjeta_energia(self) -> QFrame:
        return EnergiaPorCanal()


class VarianteG2C(VarianteG2):
    nombre = "Round 5 (#23): power, numbers first"

    def tarjeta_energia(self) -> QFrame:
        return EnergiaNumeros()


# --- ronda 6 (#24): la sección de enlace RF -------------------------------

ANCHO_L3 = 260  # la columna derecha de L3: el Recorrido gana ancho
TX_POWER = con_unidad("potencia_tx")  # el único campo de la sección
ORDEN_ENLACE = [
    "RSSI",
    "SNR",
    "Noise floor (est.)",
    "PER",
    TX_POWER,
    "Received",
    "Transmitted",
    "Lost",
    "Discarded",
    "Foreign",
]
EN_ROJO = ("Lost", "Discarded")  # en rojo si no son cero, como en la franja
MAS_ANCHO = {  # el valor más ancho de cada uno: así la franja no salta
    "RSSI": "-120 dBm",
    "SNR": "-20.0 dB",
    "Noise floor (est.)": "-120 dBm",
    "PER": "99.9 %",
    TX_POWER: "22",
}


def estado_enlace(sim: Simulador) -> tuple[str, str]:
    """(texto, nivel): NO LINK antes del primer recibido (Q3), después LINK OK
    o LINK LOST con los segundos desde el último recibido."""
    if sim.recibidos == 0:
        return "NO LINK", "nada"
    sin_rx = sim.reloj - sim.ultimo_rx
    if sin_rx > LOST_TRAS:
        return f"LINK LOST {fmt('', sin_rx)} s", "error"
    return "LINK OK", "ok"


def noise_floor(rssi: float, snr: float) -> float:
    """En potencia, para que valga también con la SNR negativa (#24, Q1):
    el RSSI mide señal + ruido, así que N = RSSI - 10·log10(1 + 10^(SNR/10))."""
    return rssi - 10 * math.log10(1 + 10 ** (snr / 10))


def valores_enlace(sim: Simulador) -> dict[str, str]:
    """Los diez valores de la sección, ya con formato (#24, Q6). El RSSI y el SNR
    son los del último recibido (Q2); sin recibidos, "—" (Q3)."""
    hay = sim.recibidos > 0
    transmitidos = sim.recibidos + sim.perdidos
    potencia = sim.ultimo.get("potencia_tx") if hay else None
    return {
        "RSSI": f"{sim.rssi:.0f} dBm" if hay else "—",
        "SNR": f"{sim.snr:.1f} dB" if hay else "—",
        "Noise floor (est.)": f"{noise_floor(sim.rssi, sim.snr):.0f} dBm" if hay else "—",
        "PER": f"{100 * sim.perdidos / transmitidos:.1f} %" if hay else "—",
        TX_POWER: str(potencia) if potencia is not None else "—",
        "Received": fmt("", sim.recibidos),
        "Transmitted": fmt("", transmitidos) if hay else "—",
        "Lost": fmt("", sim.perdidos),
        "Discarded": fmt("", sim.descartados),
        "Foreign": fmt("", sim.ajenos),
    }


class TarjetaEnlace(QFrame):
    """La sección de enlace, toda en números. `forma`:

    columna  una fila por valor (para los 230 px de la columna derecha)
    grilla   dos columnas de pares (una celda de la grilla)
    linea    una sola fila, sin título (una franja a lo ancho)
    """

    def __init__(self, forma: str) -> None:
        super().__init__()
        self.setObjectName("tarjeta")
        self.setStyleSheet("#tarjeta { border: 2px solid #555; border-radius: 4px; }")
        self.estado = label("NO LINK", negrita=True, alinear=Qt.AlignmentFlag.AlignCenter)
        self.valores: dict[str, QLabel] = {}
        derecha = Qt.AlignmentFlag.AlignRight
        if forma == "linea":
            h = QHBoxLayout(self)
            h.setContentsMargins(6, 2, 6, 2)
            h.setSpacing(4)
            self.estado.setMinimumWidth(150)
            h.addWidget(self.estado)
            for nombre in ORDEN_ENLACE:
                corto = "Noise (est.)" if nombre.startswith("Noise") else nombre
                lb = label(corto)
                lb.setToolTip(nombre)
                h.addWidget(lb)
                val = label("—", negrita=True)
                if nombre in MAS_ANCHO:  # los conteos crecen de a poco: sin fijar
                    val.setFixedWidth(val.fontMetrics().horizontalAdvance(MAS_ANCHO[nombre]) + 2)
                self.valores[nombre] = val
                h.addWidget(val)
                h.addStretch(1)
            return
        v = QVBoxLayout(self)
        v.setContentsMargins(6, 4, 6, 4)
        v.setSpacing(2)
        cab = QHBoxLayout()
        cab.addWidget(label("RF link", negrita=True, pt=PT + 2))
        cab.addStretch(1)
        cab.addWidget(self.estado)
        v.addLayout(cab)
        grilla = QGridLayout()
        grilla.setHorizontalSpacing(10)
        grilla.setVerticalSpacing(0)
        por_col = len(ORDEN_ENLACE) if forma == "columna" else 5
        for i, nombre in enumerate(ORDEN_ENLACE):
            f, c = i % por_col, (i // por_col) * 2
            # En los 230 px de la columna no entra el nombre entero.
            corto = "Noise (est.)" if forma == "columna" and nombre.startswith("Noise") else nombre
            lb = label(corto)
            lb.setToolTip(nombre)
            grilla.addWidget(lb, f, c)
            self.valores[nombre] = label("—", negrita=True, alinear=derecha)
            grilla.addWidget(self.valores[nombre], f, c + 1)
        v.addLayout(grilla)
        v.addStretch(1)

    def poner_modo(self, modo) -> None:
        pass  # sin gráfico: no tiene ventana

    def actualizar(self, sim: Simulador, datos: dict | None = None) -> None:
        texto, nivel = estado_enlace(sim)
        self.estado.setText(texto)
        self.estado.setStyleSheet(NIVEL[nivel] + "padding: 0px 8px;")
        for nombre, texto in valores_enlace(sim).items():
            lb = self.valores[nombre]
            lb.setText(texto)
            rojo = nombre in EN_ROJO and texto not in ("0", "—")
            lb.setStyleSheet("color: #b03a2e" if rojo else "")


class FranjaSinConteos(Franja):
    """La franja sin recibidos, perdidos ni descartados: pasan a la sección de
    enlace (cada dato una vez, ronda 2)."""

    CLAVES = [c for c in Franja.CLAVES if c not in ("recibidos", "perdidos", "descartados")]

    def actualizar(self, datos: dict) -> None:
        for clave, valor in self.ind.items():
            valor.setText(fmt(clave, datos[clave]) if datos[clave] != "" else "—")


def dialogo_confirmar(padre: QWidget, texto: str) -> QMessageBox:
    """El diálogo de un comando con confirmación; también sale en la captura."""
    botones = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    return QMessageBox(QMessageBox.Icon.Question, "Confirm", f"Send {texto}?", botones, padre)


class SpinMiles(QSpinBox):
    """Un QSpinBox con los miles como en el resto de la pantalla: U+202F desde
    4 dígitos (gcs-decisiones, Números en pantalla), no el separador del locale."""

    def textFromValue(self, valor: int) -> str:  # noqa: N802 (nombre que impone Qt)
        return agrupar(str(valor))

    def valueFromText(self, texto: str) -> int:  # noqa: N802
        limpio = texto.removesuffix(self.suffix()).replace(MILES, "")
        try:
            return int(limpio)
        except ValueError:
            return self.value()

    def validate(self, texto: str, pos: int):
        limpio = texto.removesuffix(self.suffix()).replace(MILES, "")
        if limpio in ("", "-"):  # a medio escribir
            return QValidator.State.Intermediate, texto, pos
        if not limpio.removeprefix("-").isdigit():
            return QValidator.State.Invalid, texto, pos
        # Como el QSpinBox de Qt: lo que se pasó del máximo no se deja tipear;
        # lo que no llega al mínimo puede estar a medio escribir (el 1 de 12).
        valor = int(limpio)
        if valor > self.maximum():
            return QValidator.State.Invalid, texto, pos
        if valor < self.minimum():
            return QValidator.State.Intermediate, texto, pos
        return QValidator.State.Acceptable, texto, pos


COLOR_ESTADO = {"PENDING": "#8a5a0b", "ACK": "#145a32", "REJECTED": "#b03a2e", "NO ACK": "#b03a2e"}
INT32 = (-(2**31), 2**31 - 1)  # el parámetro, cuando el .toml no da el rango


class PanelComandosCombo(QWidget):
    """#21: combobox con los telecomandos del .toml, el parámetro que pide cada
    uno, Send y los últimos envíos con su estado. La cola y los reintentos
    están en `sim.cola`: el panel sólo encola y muestra."""

    FILAS = 3  # las que entran en la columna de 260 px de L3 sin pedir alto

    def __init__(self, sim: Simulador) -> None:
        super().__init__()
        self.sim = sim
        v = QVBoxLayout(self)
        v.setContentsMargins(4, 4, 4, 4)
        v.setSpacing(4)
        self.combo = QComboBox()
        self.combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo.addItems(list(COMANDOS))
        self.combo.currentTextChanged.connect(self.cambiar)
        v.addWidget(self.combo)
        # El parámetro cambia con el comando: lista, número con su unidad o nada.
        fila = QHBoxLayout()
        self.pila = QStackedWidget()
        self.valores = QComboBox()
        self.valores.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.entero = SpinMiles()
        self.entero.setKeyboardTracking(False)
        self.nada = label("")
        self.nada.setStyleSheet("color: #555;")
        for w in (self.valores, self.entero, self.nada):
            # Sin esto, el QSpinBox pide el ancho de «-2147483648 Pa».
            w.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            self.pila.addWidget(w)
        self.pila.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        fila.addWidget(self.pila, 1)
        enviar = QPushButton("Send")
        enviar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        enviar.clicked.connect(self.mandar)
        fila.addWidget(enviar)
        v.addLayout(fila)
        self.filas: list[tuple[QLabel, QLabel]] = []
        for _ in range(self.FILAS):
            h = QHBoxLayout()
            izq, der = label("—"), label("", negrita=True)
            izq.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            h.addWidget(izq, 1)
            h.addWidget(der)
            v.addLayout(h)
            self.filas.append((izq, der))
        self.cambiar(self.combo.currentText())

    def cambiar(self, nombre: str) -> None:
        d = COMANDOS[nombre]
        if "valores" in d:
            self.valores.clear()
            self.valores.addItems(d["valores"])
            self.pila.setCurrentWidget(self.valores)
        elif nombre == "TIME_SET":
            self.nada.setText("Notebook clock")
            self.pila.setCurrentWidget(self.nada)
        elif "unidad" in d:
            minimo, maximo = d.get("minimo", INT32[0]), d.get("maximo", INT32[1])
            self.entero.setRange(minimo, maximo)
            self.entero.setValue(max(minimo, min(0, maximo)))
            self.entero.setSuffix(f" {d['unidad']}")
            self.pila.setCurrentWidget(self.entero)
        else:
            self.nada.setText("No parameter")
            self.pila.setCurrentWidget(self.nada)

    def parametro(self, nombre: str) -> str | int | None:
        d = COMANDOS[nombre]
        if "valores" in d:
            return self.valores.currentText()
        if nombre == "TIME_SET":
            return int(self.sim.hora().timestamp())
        if "unidad" in d:
            self.entero.interpretText()  # lo tipeado, aunque no se haya dado Enter
            return self.entero.value()
        return None

    def mandar(self) -> None:
        nombre = self.combo.currentText()
        parametro = self.parametro(nombre)
        if pide_confirmacion(nombre, parametro):
            caja = dialogo_confirmar(self, texto_envio(nombre, parametro))
            caja.exec()
            if caja.standardButton(caja.clickedButton()) != QMessageBox.StandardButton.Yes:
                return
        self.sim.cola.encolar(nombre, parametro)
        self.actualizar()

    def actualizar(self) -> None:
        envios = self.sim.cola.historia[: self.FILAS]
        for (izq, der), e in zip(self.filas, envios + [None] * self.FILAS, strict=False):
            if e is None:
                izq.setText("—")
                izq.setToolTip("")
                der.setText("")
                continue
            corto = f"#{e.numero} {e.nombre}"
            texto = f"#{e.numero} {texto_envio(e.nombre, e.parametro)}"
            # En 260 px no siempre entra todo: primero se cae el parámetro, y
            # sólo después se corta el nombre. El texto entero, en el tooltip.
            m, ancho = izq.fontMetrics(), max(izq.width(), 40)
            visible = texto if m.horizontalAdvance(texto) <= ancho else corto
            izq.setText(m.elidedText(visible, Qt.TextElideMode.ElideRight, ancho))
            izq.setToolTip(texto)
            der.setText(e.estado)
            der.setStyleSheet(f"color: {COLOR_ESTADO[e.estado]};")


class VarianteEnlace(VarianteG2B):
    """Lo común de la ronda 6: G2B con el panel de comandos de la #21, la
    sección de enlace y el pie que sólo avisa LINK LOST (#24, Q5)."""

    clase_franja = FranjaSinConteos
    sin_paquetes = True  # se dibuja aunque no haya llegado nada (NO LINK)

    def panel_comandos(self, sim: Simulador) -> QWidget:
        return PanelComandosCombo(sim)

    def actualizar(self) -> None:
        if not self.sim.ultimo:  # arranque en frío: el enlace, el pie y los telecomandos
            self.t["enlace"].actualizar(self.sim)
            self.comandos.actualizar()  # sin paquetes, un envío también llega a NO ACK
            self.actualizar_avisos(estado_gcs(self.sim, self))
            return
        super().actualizar()

    def actualizar_avisos(self, condiciones) -> None:
        texto, nivel = estado_enlace(self.sim)
        condiciones = list(condiciones)
        condiciones[0] = ("Link", texto, "error") if nivel == "error" else None
        colores = {"ok": "#145a32", "aviso": "#8a5a0b", "error": "#b03a2e"}
        for lb, cond in zip(self.pie, condiciones, strict=True):
            if cond is None:  # el enlace sano no se repite en el pie
                lb.setText("")
                lb.setStyleSheet("")
                continue
            titulo, texto, nivel = cond
            marca = "●" if nivel == "ok" else "▲"
            lb.setText(
                f"<span style='color:{colores[nivel]}'>{marca}</span> {titulo}: <b>{texto}</b>"
            )
            lb.setStyleSheet(
                "background: #b03a2e; color: white;" if nivel == "error" else "color: black;"
            )


class VarianteL1(VarianteEnlace):
    nombre = "Round 6 (#24): link in the right column"

    def ubicar(self, g: QGridLayout, columna: QVBoxLayout) -> None:
        self.t["enlace"] = TarjetaEnlace("columna")
        super().ubicar(g, columna)  # G2: el Recorrido al fondo de la columna
        columna.insertWidget(1, self.t["enlace"])
        self.t["recorrido"].plot.setMinimumHeight(40)  # lo que queda, para el mapa


class VarianteL2(VarianteEnlace):
    nombre = "Round 6 (#24): link as a strip"

    def __init__(self, sim: Simulador) -> None:
        super().__init__(sim)
        self.layout().insertWidget(1, self.t["enlace"])

    def ubicar(self, g: QGridLayout, columna: QVBoxLayout) -> None:
        self.t["enlace"] = TarjetaEnlace("linea")
        super().ubicar(g, columna)


class VarianteL3(VarianteEnlace):
    nombre = "Round 6 (#24): link under flight and GPS"
    ancho_comandos = ANCHO_L3

    def ubicar(self, g: QGridLayout, columna: QVBoxLayout) -> None:
        # El enlace abajo, con el alto justo de sus números; Vuelo y GPS se queda
        # con el resto. Energía, aceleración y rotación, como en G2.
        self.t["enlace"] = TarjetaEnlace("grilla")
        self.t["enlace"].setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        izq = QVBoxLayout()
        izq.setSpacing(4)
        izq.addWidget(self.t["vuelo"], 1)
        izq.addWidget(self.t["enlace"])
        g.addLayout(izq, 0, 0, 2, 1)
        g.addWidget(self.t["energia"], 0, 1, 1, 2)
        g.addWidget(self.t["acel"], 1, 1)
        g.addWidget(self.t["rot"], 1, 2)
        g.setColumnStretch(0, 4)
        g.setColumnStretch(1, 3)
        g.setColumnStretch(2, 3)
        columna.addWidget(self.t["recorrido"], 1)


# --- ronda 7 (#22): la consola de depuración ------------------------------

# Una línea del puente son 150 hex más el RSSI y el SNR: a 14 pt (G12) entran
# unos 120 caracteres a lo ancho, así que cada paquete ocupa dos líneas.
ETIQUETA_CONSOLA = {
    "rx": ("RX", "#145a32"),
    "crc": ("BAD CRC", "#b03a2e"),
    "lost": ("LOST", "#b03a2e"),
    "foreign": ("FOREIGN", "#8a5a0b"),
    "tx": ("TX", "#1f4e9c"),
    "heltec": ("HELTEC", "#666"),
}


def html_linea(hora: str, tipo: str, texto: str) -> str:
    """Una entrada: hora, qué es y la línea tal cual; en un paquete, la cabecera
    CCSDS en azul y el CRC en ocre, para que se vea cómo baja el binario."""
    etiqueta, color = ETIQUETA_CONSOLA[tipo]
    if tipo in ("rx", "crc") and "," in texto:
        hexa, resto = texto.split(",", 1)
        cuerpo = (
            f"<span style='color:#1f4e9c'>{hexa[:12]}</span>"
            f"<span style='color:#666'>{hexa[12:14]}</span>"
            f"{hexa[14:-4]}"
            f"<span style='color:#b9770e; font-weight:bold'>{hexa[-4:]}</span>"
            f"<span style='color:#666'>,{resto}</span>"
        )
    elif tipo == "foreign":
        cuerpo = f"<span style='color:#666'>{texto}</span>"
    else:
        cuerpo = texto
    marca = f"<b style='color:{color}'>{etiqueta.ljust(7).replace(' ', '&nbsp;')}</b>"
    return (
        f"<p style='margin:0'><span style='color:#555'>{hora}</span>&nbsp;{marca}&nbsp;{cuerpo}</p>"
    )


class Consola(QTextEdit):
    """Abajo de todo, fina: las líneas del puente en hex y el texto de la Heltec."""

    def __init__(self, lineas: int) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        fuente = QFont("Consolas")
        fuente.setStyleHint(QFont.StyleHint.Monospace)
        fuente.setPointSize(PT)
        self.setFont(fuente)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.document().setDocumentMargin(2)
        self.setStyleSheet("QTextEdit { border: 2px solid #999; background: #fafafa; }")
        alto = lineas * QFontMetrics(fuente).lineSpacing() + 4 + 2 * self.frameWidth()
        self.setFixedHeight(alto)
        self.visto = None

    def actualizar(self, sim: Simulador) -> None:
        ultimo = sim.consola[-1] if sim.consola else None
        if ultimo is self.visto:
            return
        self.visto = ultimo
        self.setHtml("".join(html_linea(*e) for e in list(sim.consola)[-30:]))
        barra = self.verticalScrollBar()
        barra.setValue(barra.maximum())


class VarianteConsola(VarianteL3):
    """L3 con la consola entre la grilla y el pie; arranca oculta."""

    lineas = 6
    boton_en = "pie"

    def __init__(self, sim: Simulador) -> None:
        super().__init__(sim)
        self.consola = Consola(self.lineas)
        self.consola.hide()
        raiz = self.layout()
        raiz.insertWidget(raiz.count() - 1, self.consola)
        if self.lineas > 3:  # 6 líneas no entran en 768 px con los 140 px de mínimo
            for t in self.t.values():
                for w in getattr(t, "plots", []):
                    w.setMinimumHeight(100)
            self.t["recorrido"].plot.setMinimumHeight(100)
        self.boton = QPushButton()
        self.boton.setCheckable(True)
        self.boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.boton.toggled.connect(self.mostrar_consola)
        self.mostrar_consola(False)
        if self.boton_en == "pie":
            self.boton.setStyleSheet("padding: 0px 8px;")
            self.pie[0].parentWidget().layout().addWidget(self.boton)
        else:  # en la franja, al lado de la ventana de los gráficos
            self.boton.setMinimumHeight(48)
            fila = self.franja.layout()
            fila.insertWidget(fila.count() - 1, self.boton)

    def mostrar_consola(self, visible: bool) -> None:
        self.consola.setVisible(visible)
        self.boton.setText("Console ▼" if visible else "Console ▲")
        if visible:
            self.consola.visto = None
            self.consola.actualizar(self.sim)

    def actualizar(self) -> None:
        super().actualizar()
        if self.consola.isVisible():
            self.consola.actualizar(self.sim)


class VarianteK3(VarianteConsola):
    nombre = "Round 7 (#22): console, 3 lines, button in the footer"
    lineas = 3


class VarianteK6(VarianteConsola):
    nombre = "Round 7 (#22): console, 6 lines, button in the footer"


class VarianteK6F(VarianteConsola):
    nombre = "Round 7 (#22): console, 6 lines, button in the top strip"
    boton_en = "franja"


# --- ventana y selector de variante ---------------------------------------

VARIANTES = {
    "A": VarianteA,
    "B": VarianteB,
    "C": VarianteC,
    "D": VarianteD,
    "E": VarianteE,
    "F": VarianteF,
    "G": VarianteG,
    "G2": VarianteG2,
    "G3": VarianteG3,
    "G2A": VarianteG2A,
    "G2B": VarianteG2B,
    "G2C": VarianteG2C,
    "L1": VarianteL1,
    "L2": VarianteL2,
    "L3": VarianteL3,
    "K3": VarianteK3,
    "K6": VarianteK6,
    "K6F": VarianteK6F,
}


class Selector(QFrame):
    """Pastilla flotante, abajo al centro: no es parte del diseño."""

    def __init__(self, ventana: Ventana) -> None:
        super().__init__(ventana)
        self.setStyleSheet(
            "QFrame { background: #222; border-radius: 16px; }"
            "QLabel, QPushButton { color: white; background: transparent; border: none; }"
        )
        h = QHBoxLayout(self)
        h.setContentsMargins(10, 2, 10, 2)
        izq, der = QPushButton("◀"), QPushButton("▶")
        izq.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        der.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        izq.clicked.connect(lambda: ventana.ciclar(-1))
        der.clicked.connect(lambda: ventana.ciclar(1))
        self.texto = QLabel()
        h.addWidget(izq)
        h.addWidget(self.texto)
        h.addWidget(der)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)


def escribiendo() -> bool:
    """Si el foco está en un campo de texto o numérico: las teclas sueltas
    (Espacio, 1 a 5, ← y →) son de ese campo, no de la simulación."""
    return isinstance(QApplication.focusWidget(), (QLineEdit, QAbstractSpinBox))


class Ventana(QMainWindow):
    def __init__(self, inicial: str, demo: bool = False) -> None:
        super().__init__()
        nota = "Simulated data" + ("; provisional format" if FORMATO.get("provisorio") else "")
        self.setWindowTitle(f"Avutardo GCS — PROTOTYPE — {nota}")
        self.demo = demo
        self.sim = Simulador(demo=demo)
        self.claves = list(VARIANTES)
        self.actual = inicial
        self.selector = Selector(self)
        self.poner(inicial)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

        QShortcut(QKeySequence(Qt.Key.Key_F11), self, self.alternar_completa)
        QShortcut(QKeySequence(Qt.Key.Key_F12), self, self.capturar)
        QShortcut(QKeySequence(Qt.Key.Key_F6), self, lambda: self.simular("pendrive"))
        QShortcut(QKeySequence(Qt.Key.Key_F7), self, lambda: self.simular("enlace"))
        QShortcut(QKeySequence(Qt.Key.Key_F8), self, self.adelantar)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, lambda: self.flecha(-1))
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, lambda: self.flecha(1))

        # Controles para probar la simulación (ver el encabezado).
        self.velocidad = 1
        self.pausado = False
        teclas = {
            Qt.Key.Key_F5: self.reiniciar,
            Qt.Key.Key_Space: self.pausar,
            Qt.Key.Key_F9: self.acelerar,
            Qt.Key.Key_F1: lambda: self.falla("rafaga"),
            Qt.Key.Key_F2: lambda: self.falla("crc"),
            Qt.Key.Key_F3: lambda: self.falla("gps"),
            Qt.Key.Key_F4: lambda: self.falla("bateria"),
            "Shift+F4": lambda: self.falla("ina"),
            "Shift+F2": lambda: self.falla("ajeno"),
            "Shift+F7": lambda: self.falla("debil"),
            "Shift+F5": self.arranque_en_frio,
            Qt.Key.Key_F10: lambda: self.falla("reinicio"),
        }
        for i, fase in enumerate(FASES):
            teclas[Qt.Key(Qt.Key.Key_1.value + i)] = lambda f=fase: self.saltar(f)
        for tecla, accion in teclas.items():
            QShortcut(QKeySequence(tecla), self, accion)
        self.actualizar_titulo()

    def actualizar_titulo(self) -> None:
        nota = "Simulated data" + ("; provisional format" if FORMATO.get("provisorio") else "")
        marcha = "PAUSED" if self.pausado else f"×{self.velocidad}"
        self.setWindowTitle(f"Avutardo GCS — PROTOTYPE — {nota} — {marcha}")

    def avisar(self, texto: str) -> None:
        self.statusBar().showMessage(texto, 3000)

    def arranque_en_frio(self) -> None:
        """Shift+F5: la estación abre sin paquetes y la FSW tarda 10 s (#24, Q3)."""
        self.sim = Simulador(precarga=False)
        self.sim.reinicio = 10
        self.poner(self.actual)
        self.avisar("Cold start: 10 s without packets")

    def refrescar(self) -> None:
        """Las variantes viejas necesitan un paquete; las de la ronda 6, no."""
        if self.sim.ultimo or getattr(self.vista, "sin_paquetes", False):
            self.vista.actualizar()

    def reiniciar(self) -> None:
        """F5: un vuelo nuevo desde STANDBY, en la misma variante."""
        self.sim = Simulador(demo=self.demo)
        self.poner(self.actual)
        self.avisar("Flight restarted")

    def pausar(self) -> None:
        if escribiendo():
            return
        self.pausado = not self.pausado
        self.actualizar_titulo()
        self.avisar("Paused" if self.pausado else "Running")

    def acelerar(self) -> None:
        self.velocidad = {1: 5, 5: 10, 10: 1}[self.velocidad]
        self.actualizar_titulo()
        self.avisar(f"Speed ×{self.velocidad}")

    def saltar(self, fase: str) -> None:
        """1 a 5: hacia adelante corre el vuelo; hacia atrás, lo reinicia antes."""
        if escribiendo():
            return
        actual = FASES.index(self.sim._perfil(self.sim.t - self.sim.despegue)[1])
        if FASES.index(fase) < actual or self.sim.cortado:
            self.sim = Simulador(demo=self.demo)
            self.poner(self.actual)
        self.sim.saltar(fase)
        self.refrescar()
        self.avisar(f"Jump to {fase}")

    def falla(self, que: str) -> None:
        s = self.sim
        if que == "rafaga":
            s.rafaga = 5
            texto = "Burst: the next 5 packets are lost"
        elif que == "crc":
            s.crc_roto = 1
            texto = "The next packet arrives with a bad CRC"
        elif que == "gps":
            s.sin_fix = not s.sin_fix
            texto = "GPS without fix" if s.sin_fix else "GPS with fix"
        elif que == "bateria":
            s.bateria_baja = not s.bateria_baja
            texto = "Low battery" if s.bateria_baja else "Battery normal"
        elif que == "ina":
            s.ina_sin_dato = not s.ina_sin_dato
            texto = "BAT_CURRENT with no data" if s.ina_sin_dato else "BAT_CURRENT with data"
        elif que == "ajeno":
            s.ajeno()
            texto = "A packet from another team arrived (Foreign)"
        elif que == "debil":
            s.senal_debil = not s.senal_debil
            texto = "Weak signal (negative SNR)" if s.senal_debil else "Normal signal"
        else:
            s.reinicio = 3
            texto = "FSW reset: 3 s without transmitting"
        self.avisar(texto)

    def poner(self, clave: str) -> None:
        self.actual = clave
        self.vista = VARIANTES[clave](self.sim)
        self.setCentralWidget(self.vista)
        self.refrescar()
        self.selector.texto.setText(f"{clave} ({self.vista.nombre})")
        self.selector.adjustSize()
        self.selector.raise_()
        self.ubicar_selector()

    def ciclar(self, paso: int) -> None:
        i = (self.claves.index(self.actual) + paso) % len(self.claves)
        self.poner(self.claves[i])

    def flecha(self, paso: int) -> None:
        if escribiendo():
            return
        self.ciclar(paso)

    def simular(self, que: str) -> None:
        if que == "pendrive":
            self.sim.pendrive = not self.sim.pendrive
        else:
            self.sim.enlace_caido = not self.sim.enlace_caido
        self.refrescar()

    def adelantar(self) -> None:
        """F8: 30 s de vuelo de golpe, para llegar al aterrizaje sin esperar."""
        for _ in range(30):
            self.sim.paso()
        self.refrescar()

    def tick(self) -> None:
        if self.pausado:
            return
        for _ in range(self.velocidad):
            self.sim.paso()
        self.refrescar()

    def alternar_completa(self) -> None:
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def capturar(self) -> None:
        CAPTURAS.mkdir(exist_ok=True)
        self.selector.hide()
        imagen = self.grab().toImage()
        if imagen.devicePixelRatio() < 2:
            imagen = imagen.scaled(
                imagen.width() * 2 // round(imagen.devicePixelRatio()),
                imagen.height() * 2 // round(imagen.devicePixelRatio()),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self.selector.show()
        destino = CAPTURAS / f"variante-{self.actual}.png"
        imagen.save(str(destino))
        self.statusBar().showMessage(f"Screenshot: {destino}", 3000)

    def ubicar_selector(self) -> None:
        s = self.selector
        s.move((self.width() - s.width()) // 2, self.height() - s.height() - 6)

    def resizeEvent(self, e) -> None:  # noqa: N802 (nombre que impone Qt)
        super().resizeEvent(e)
        self.ubicar_selector()


ESTILO = (
    "QWidget { background: white; color: black; }"
    "QTableWidget, QHeaderView, QPushButton, QLineEdit, QSpinBox { font-size: 14pt; }"
    "QTableWidget::item { padding: 0px 4px; }"
    "QPushButton { border: 2px solid #555; padding: 4px 10px; }"
    "QHeaderView::section { font-weight: bold; background: #eee; }"
)


# --- capturas de la diap. 77 ----------------------------------------------

ESCALA = 2  # 1366×768 lógicos con el doble de píxeles: 2732×1536 (#4, Q6)


def preparar_captura() -> None:
    """Antes de crear la QApplication: pantalla fuera de pantalla de 1366×768
    con escala 2, y las fuentes del sistema (sin ellas, el texto sale en cajas).

    Qt separa las opciones de la plataforma con «:», así que la ruta del JSON
    va relativa y sin letra de unidad."""
    config = Path(__file__).with_name("pantalla-captura.json")
    try:
        relativa = os.path.relpath(config).replace(os.sep, "/")
    except ValueError:
        sys.exit("--captura must run from the same drive as the repository")
    os.environ["QT_QPA_PLATFORM"] = f"offscreen:configfile={relativa}"
    fuentes = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    if fuentes.is_dir():
        os.environ.setdefault("QT_QPA_FONTDIR", str(fuentes))


def imagen(widget: QWidget) -> QImage:
    """El widget dibujado al doble de píxeles (no escalado después)."""
    img = QImage(widget.size() * ESCALA, QImage.Format.Format_ARGB32)
    img.setDevicePixelRatio(ESCALA)
    img.fill(QColor("white"))
    widget.render(img)
    return img


def avanzar(v: Ventana, instante: str) -> None:
    """Corre el vuelo de demostración hasta el instante, refrescando la vista
    en cada paso: el panel de telecomandos sólo anota un eco cuando lo ve."""
    for _ in range(1000):
        if llego(v.sim, instante):
            return
        v.sim.paso()
        v.refrescar()
    sys.exit(f"The demo flight never reached {instante!r}")


def capturar_demo(app: QApplication, v: Ventana, instante: str, destino: Path) -> None:
    """Graba la pantalla entera en el instante; en `standby`, además, los
    recortes del diálogo de altitud cero, los telecomandos y Vuelo y GPS."""
    if instante == "aterrizado" and pixmap_qr("x", 10) is None:
        sys.exit("The landed capture needs segno: uv run --with segno python ...")
    v.timer.stop()
    v.resize(1366, 768)
    v.show()
    if instante == "consola":
        if not isinstance(v.vista, VarianteConsola):
            sys.exit("--hasta consola needs a console variant (K3, K6 or K6F)")
        v.vista.boton.setChecked(True)
    app.processEvents()
    avanzar(v, instante)
    v.selector.hide()
    app.processEvents()
    destino.parent.mkdir(parents=True, exist_ok=True)
    entera = imagen(v)
    esperado = (1366 * ESCALA, 768 * ESCALA)
    assert (entera.width(), entera.height()) == esperado, (entera.size(), esperado)
    entera.save(str(destino))
    grabadas = [destino]
    if instante == "standby":
        dialogo = dialogo_confirmar(v, "CAL_ALT")
        dialogo.show()
        app.processEvents()
        recortes = {
            "confirmacion": dialogo,
            "telecomandos": v.vista.caja_comandos,
            "vuelo": v.vista.t["vuelo"],
        }
        for nombre, widget in recortes.items():
            ruta = destino.with_name(f"{destino.stem}-{nombre}{destino.suffix}")
            imagen(widget).save(str(ruta))
            grabadas.append(ruta)
        dialogo.close()
    if instante == "consola":
        ruta = destino.with_name(f"{destino.stem}-recorte{destino.suffix}")
        imagen(v.vista.consola).save(str(ruta))
        grabadas.append(ruta)
    for ruta in grabadas:
        print(f"Saved {ruta}")


def argumentos() -> argparse.Namespace:
    a = argparse.ArgumentParser(description="Avutardo GCS screen prototype (simulated data).")
    a.add_argument("variante", nargs="?", default=None, help="layout variant (default: G2B)")
    a.add_argument("--simular", choices=["demo"], help="run the fixed demo flight")
    a.add_argument("--hasta", choices=INSTANTES, help="advance the demo flight to this instant")
    a.add_argument(
        "--captura",
        type=Path,
        metavar="PNG",
        help="save a 2732x1536 screenshot offscreen and exit (implies --simular demo; "
        "needs --hasta; default variant: L3)",
    )
    args = a.parse_args()
    if args.captura and not args.hasta:
        a.error("--captura needs --hasta")
    if args.hasta and not args.captura and args.simular != "demo":
        a.error("--hasta needs --simular demo")
    return args


def main() -> None:
    args = argumentos()
    if args.captura:
        preparar_captura()
    por_defecto = "L3" if args.captura else "G2B"
    if args.hasta == "consola":
        por_defecto = "K6"
    inicial = (args.variante or por_defecto).upper()
    app = QApplication(sys.argv[:1])
    f = app.font()
    if args.captura:
        f.setFamily("Segoe UI")  # la de la ventana real en Windows
    f.setPointSize(PT)
    app.setFont(f)
    app.setStyleSheet(ESTILO)
    configurar_pyqtgraph()
    demo = bool(args.captura) or args.simular == "demo"
    v = Ventana(inicial if inicial in VARIANTES else por_defecto, demo=demo)
    if args.captura:
        capturar_demo(app, v, args.hasta, args.captura)
        return
    if args.hasta:
        avanzar(v, args.hasta)
        v.pausado = True  # en el instante, quieto: Espacio lo sigue
        v.actualizar_titulo()
    v.resize(1366, 768)  # el mínimo de #4, en píxeles lógicos
    v.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
