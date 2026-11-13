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

Correr, desde `gcs/`:

    uv run python prototipos/pantalla.py        # arranca en D
    uv run python prototipos/pantalla.py A      # arranca en A

Teclas: ← y → cambian de variante, F11 alterna pantalla completa, F12 guarda
una captura al doble de píxeles en `prototipos/capturas/` (como pide #4, Q6).
Para ver los avisos: F6 saca y pone el pendrive, F7 corta y repone el enlace.
F8 adelanta 30 s de vuelo (para llegar al aterrizaje y ver el QR de G).

El QR de G necesita `segno`, que no es dependencia de la GCS: correr con
`uv run --with segno python prototipos/pantalla.py G`.
"""

from __future__ import annotations

import bisect
import math
import random
import sys
import tomllib
from collections import deque
from datetime import UTC, datetime
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
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
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

RAIZ = Path(__file__).resolve().parents[2]
TOML = RAIZ / "protocolo" / "telemetria.toml"
CAPTURAS = Path(__file__).resolve().parent / "capturas"

PT = 14  # G12: letra de 14 pt o más, en toda la pantalla
TRAZO = 3  # G12: trazos en negrita
HISTORIA = 120  # segundos que muestra cada gráfico

COLORES = {"x": "#c0392b", "y": "#1e8449", "z": "#1f4e9c", "uno": "#1f4e9c", "dos": "#b9770e"}

# --- formato --------------------------------------------------------------

with TOML.open("rb") as f:
    FORMATO = tomllib.load(f)
CAMPOS = FORMATO["campo"]
UNIDAD = {c["nombre"]: c["unidad"] for c in CAMPOS}


def fmt(nombre: str, valor) -> str:
    """Punto decimal y espacio fino de miles, como la norma del equipo."""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, int):
        return f"{valor:,}".replace(",", " ")
    dec = 6 if nombre.startswith("gps_l") else 2 if abs(valor) < 100 else 1
    return f"{valor:,.{dec}f}".replace(",", " ")


def etiqueta(nombre: str) -> str:
    return nombre.replace("_", " ").capitalize()


def con_unidad(nombre: str) -> str:
    u = UNIDAD.get(nombre, "")
    return f"{etiqueta(nombre)} [{u}]" if u else etiqueta(nombre)


# --- simulador de juguete -------------------------------------------------


class Simulador:
    """Un vuelo tipo Prometeo a 1 Hz, con algún paquete perdido."""

    def __init__(self) -> None:
        self.t = 0.0
        self.contador = 0
        self.recibidos = 0
        self.perdidos = 0
        self.ultimo_contador: int | None = None
        self.eco = ""
        self.cortado = False
        self.offset_alt = 0.0
        self.alt_max = 0.0
        # La misión entera: el modo "Histórico" la necesita (son ~10 min a 1 Hz).
        # El contador viene en la cabecera CCSDS (telemetria.toml v1), no en CAMPOS.
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
        self.rssi = -70.0
        self.snr = 9.0
        self.ultimo: dict = {}
        self.registro: deque[str] = deque(maxlen=200)
        # Arranca con 40 s en la rampa y el lanzamiento a los 45 s, para que los
        # gráficos no estén vacíos al abrir.
        for _ in range(40):
            self.paso()

    def _perfil(self, tv: float) -> tuple[float, str]:
        if tv < 0:
            return 0.0, "STANDBY"
        if tv < 12:
            return 673 * math.sin(tv / 12 * math.pi / 2), "ASCENT"
        alt = 673 - 15 * (tv - 12)
        if alt > 0.8 * 673:
            return alt, "DESCENT 1"
        t2 = 12 + (673 - 0.8 * 673) / 15
        alt = 0.8 * 673 - 3.5 * (tv - t2)
        return (alt, "DESCENT 2") if alt > 0 else (0.0, "LANDED")

    def paso(self) -> None:
        self.reloj += 1
        if self.cortado:
            return
        self.t += 1
        self.contador += 1
        tv = self.t - 45
        alt, estado = self._perfil(tv)
        if estado not in ("STANDBY", "LANDED"):
            self.deriva += 1
        if self.ultimo and estado != self.ultimo["estado_fsw"]:
            self.t_cambio = self.t
        alt += random.gauss(0, 0.4)
        r = random.gauss
        g = 9.81
        empuje = 60 if 0 <= tv < 2 else 0
        golpe = 80 if 12 <= tv < 13 else 0
        p = {
            "contador": self.contador,
            "tiempo_mision": self.t,
            "hora": datetime.now(UTC).strftime("%H:%M:%S"),
            "estado_fsw": estado,
            "altitud": alt - self.offset_alt,
            "presion": 101325 * (1 - 2.25577e-5 * alt) ** 5.25588 + r(0, 3),
            "temperatura": 18.0 - 0.0065 * alt + r(0, 0.1),
            "tension": 7.9 - 0.002 * self.t + r(0, 0.01),
            "corriente": (0.42 if estado in ("ASCENT", "DESCENT 1", "DESCENT 2") else 0.18)
            + r(0, 0.01),
            "panel": 5.5 + r(0, 0.05),  # de juguete, como el resto
            "acel_x": r(0, 0.3) + golpe * 0.3,
            "acel_y": r(0, 0.3),
            "acel_z": g + empuje + golpe + r(0, 0.3),
            "rot_x": r(0, 3) + (40 * math.sin(tv) if 12 <= tv < 60 else 0),
            "rot_y": r(0, 3),
            "rot_z": r(0, 3) + (90 if 12 <= tv < 60 else 0),
            "gps_hora": datetime.now(UTC).strftime("%H:%M:%S"),
            "gps_latitud": -53.7860 + 0.00002 * self.deriva + r(0, 0.000005),
            "gps_longitud": -67.7000 + 0.00003 * self.deriva + r(0, 0.000005),
            "gps_altitud": 30 + alt + r(0, 2),
            "gps_satelites": 9,
            "eco_comando": self.eco,
        }
        if self.enlace_caido or (random.random() < 0.04 and self.contador > 3):
            return  # paquete perdido en el aire
        if self.ultimo_contador is not None:
            self.perdidos += self.contador - self.ultimo_contador - 1
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
        self.rssi = -68 - alt / 25 + r(0, 1.5)
        self.snr = 10 - alt / 120 + r(0, 0.5)
        self.registro.append(",".join(fmt(c["nombre"], p[c["nombre"]]) for c in CAMPOS))

    def telecomando(self, nombre: str, argumento: str = "") -> None:
        if nombre == "altitud cero":
            self.offset_alt += self.ultimo.get("altitud", 0.0)
        if nombre == "cortar":
            self.eco = "cortar"
            self.paso()
            self.cortado = True
            return
        self.eco = f"{nombre} {argumento}".strip()


# --- piezas comunes -------------------------------------------------------


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
    w.setLabel("bottom", "Tiempo de misión [s]", **estilo)
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
            ("Altitud cero", "altitud cero", True),
            ("Hora UTC", "hora utc", False),
            ("Datos extra", "datos extra", False),
            ("Cortar la telemetría", "cortar", True),
        ]
        for texto, nombre, confirmar in botones:
            b = QPushButton(texto)
            b.setMinimumHeight(36)
            if confirmar:
                b.setStyleSheet("QPushButton { border: 2px solid #b03a2e; padding: 4px 10px; }")
            b.clicked.connect(lambda _=False, n=nombre, c=confirmar, t=texto: self.mandar(n, c, t))
            caja.addWidget(b)
        self.linea = QLineEdit()
        self.linea.setPlaceholderText("Telecomando…")
        self.linea.returnPressed.connect(self.mandar_linea)
        caja.addWidget(self.linea, 1)
        self.eco = label("Eco: —", negrita=True)
        caja.addWidget(self.eco)
        self.eco.setVisible(mostrar_eco)  # en los híbridos el eco va en la franja

    def mandar(self, nombre: str, confirmar: bool, texto: str) -> None:
        if confirmar:
            r = QMessageBox.question(self, "Confirmar", f"¿Mandar «{texto}»?")
            if r != QMessageBox.StandardButton.Yes:
                return
        arg = datetime.now(UTC).strftime("%H:%M:%S") if nombre == "hora utc" else ""
        self.sim.telecomando(nombre, arg)

    def mandar_linea(self) -> None:
        if self.linea.text().strip():
            self.sim.telecomando(self.linea.text().strip())
            self.linea.clear()

    def actualizar(self) -> None:
        self.eco.setText(f"Eco: {self.sim.ultimo.get('eco_comando') or '—'}")


GRAFICOS_G7 = [
    ("Altitud", "m", ["altitud"]),
    ("Tensión", "V", ["tension"]),
    ("Corriente", "A", ["corriente"]),
    ("Aceleración", "m/s²", ["acel_x", "acel_y", "acel_z"]),
    ("Velocidad de rotación", "°/s", ["rot_x", "rot_y", "rot_z"]),
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
        curva.setData(t[i:], sim.historia[nombre][i:])


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
    nombre = "Franja + tabla + grilla"

    def __init__(self, sim: Simulador) -> None:
        super().__init__()
        self.sim = sim
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(4, 4, 4, 4)
        raiz.setSpacing(4)

        franja = QHBoxLayout()
        self.ind = {}
        for clave, titulo in [
            ("estado_fsw", "Estado FSW"),
            ("tiempo_mision", "Tiempo de misión [s]"),
            ("recibidos", "Recibidos"),
            ("perdidos", "Perdidos"),
            ("hora", "Hora UTC"),
            ("alt_max", "Altitud máx. [m]"),
        ]:
            caja, valor = indicador(titulo)
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
        w, c = grafico("Temperatura", "°C", ["temperatura"])
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
    nombre = "Altitud protagonista"

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
        cabeza.addWidget(label("Altitud [m]", pt=PT))
        cabeza.addWidget(self.alt)
        izq.addLayout(cabeza)
        w, self.c_alt = grafico("Altitud", "m", ["altitud"])
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
        for i, (clave, titulo) in enumerate(
            [
                ("tiempo_mision", "Tiempo [s]"),
                ("hora", "Hora UTC"),
                ("recibidos", "Recibidos"),
                ("perdidos", "Perdidos"),
                ("temperatura", "Temp. [°C]"),
                ("gps", "GPS [°]"),
            ]
        ):
            caja, valor = indicador(titulo)
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
            f"{p['gps_latitud']:.5f}  {p['gps_longitud']:.5f}  ({p['gps_satelites']} sat.)"
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
    nombre = "Tablero por subsistema"

    def __init__(self, sim: Simulador) -> None:
        super().__init__()
        self.sim = sim
        g = QGridLayout(self)
        g.setContentsMargins(4, 4, 4, 4)
        g.setSpacing(4)
        self.tarjetas = [
            Tarjeta(
                "Misión",
                ["estado_fsw", "contador", "tiempo_mision", "hora", "recibidos", "perdidos"],
            ),
            Tarjeta(
                "Vuelo",
                ["altitud", "presion", "temperatura"],
                ("Altitud", "m", ["altitud"]),
            ),
            Tarjeta(
                "Energía",
                ["tension", "corriente"],
                ("Tensión", "V", ["tension"]),
            ),
            Tarjeta(
                "Aceleración",
                ["acel_x", "acel_y", "acel_z"],
                ("Aceleración", "m/s²", ["acel_x", "acel_y", "acel_z"]),
            ),
            Tarjeta(
                "Rotación",
                ["rot_x", "rot_y", "rot_z"],
                ("Rotación", "°/s", ["rot_x", "rot_y", "rot_z"]),
            ),
            Tarjeta(
                "GPS",
                ["gps_hora", "gps_latitud", "gps_longitud", "gps_altitud", "gps_satelites"],
            ),
        ]
        # La corriente también tiene que graficarse (G7): segunda curva en Energía.
        energia = self.tarjetas[2]
        w = energia.findChild(pg.PlotWidget)
        energia.curvas["corriente"] = w.plot(pen=pg.mkPen(COLORES["dos"], width=TRAZO))
        w.setTitle("<b>Tensión [V] y corriente [A]</b>", size=f"{PT}pt")

        g.addWidget(self.tarjetas[0], 0, 0)
        g.addWidget(self.tarjetas[1], 0, 1, 1, 2)
        g.addWidget(self.tarjetas[5], 1, 0)
        g.addWidget(self.tarjetas[2], 1, 1)
        g.addWidget(self.tarjetas[3], 1, 2)
        comandos = QFrame()
        comandos.setFrameShape(QFrame.Shape.StyledPanel)
        cv = QVBoxLayout(comandos)
        cv.setContentsMargins(4, 4, 4, 4)
        cv.addWidget(label("Telecomandos", negrita=True, pt=PT + 2))
        self.comandos = PanelComandos(sim, vertical=True)
        cv.addWidget(self.comandos)
        g.addWidget(comandos, 0, 3)
        g.addWidget(self.tarjetas[4], 1, 3)
        for col, estirar in enumerate([2, 3, 3, 3]):
            g.setColumnStretch(col, estirar)
        g.setRowStretch(0, 1)
        g.setRowStretch(1, 1)

    def actualizar(self) -> None:
        extra = {"recibidos": self.sim.recibidos, "perdidos": self.sim.perdidos}
        for t in self.tarjetas:
            t.actualizar(self.sim, extra)
        self.comandos.actualizar()


# --- variantes D, E y F: híbridos A + C (ronda 2 de la #7) ----------------

ETIQUETA_GCS = {
    "vel_vertical": "Vel. vertical [m/s]",
    **{f"acel_{e}": f"{e} [m/s²]" for e in "xyz"},
    **{f"rot_{e}": f"{e} [°/s]" for e in "xyz"},
}
FASES = ["STANDBY", "ASCENT", "DESCENT 1", "DESCENT 2", "LANDED"]
BANDA = {"DESCENT 1": (15, 3, "C3"), "DESCENT 2": (5, 3, "C4")}  # bajada [m/s]
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
        enlace = ("Enlace", f"CORTADO hace {sin_rx} s", "error")
    else:
        enlace = ("Enlace", f"{sim.rssi:.0f} dBm · {sim.snr:.1f} dB", "ok")
    if sim.pendrive:
        pendrive = ("Pendrive", "AVUTARDO", "ok")
    else:
        pendrive = ("Pendrive", "SIN PENDRIVE", "error")
    if FORMATO.get("provisorio"):
        formato = ("Formato", "PROVISORIO", "aviso")
    else:
        formato = ("Formato", f"v{FORMATO.get('version', '?')}", "ok")
    geo = widget.screen().availableGeometry()
    ancho, alto = geo.width(), geo.height()
    if ancho >= 1366 and alto >= 768:
        pantalla = ("Pantalla", f"{ancho}×{alto}", "ok")
    else:
        pantalla = ("Pantalla", f"BAJA {ancho}×{alto}", "aviso")
    return [enlace, pendrive, formato, pantalla]


def texto_banda(sim: Simulador) -> tuple[str, str]:
    """La nota de la velocidad vertical: calculada en la GCS, contra C3 o C4."""
    estado = sim.ultimo["estado_fsw"]
    if estado not in BANDA:
        return "Vel. vertical calculada en la GCS (no es un campo del formato)", "nada"
    objetivo, tol, req = BANDA[estado]
    bajada = -sim.vel_vertical
    nivel = "ok" if abs(bajada - objetivo) <= tol else "error"
    marca = "dentro" if nivel == "ok" else "FUERA"
    return (
        f"Bajada {bajada:.1f} m/s · esperada {objetivo} ± {tol} ({req}): {marca}"
        " · calculada en la GCS",
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
                self.valores[nombre] = val
                grilla.addWidget(val, 0, i)
                grilla.setColumnStretch(i, 1)
                continue
            f, c = i % por_col, (i // por_col) * 2
            grilla.addWidget(label(ETIQUETA_GCS.get(nombre) or con_unidad(nombre)), f, c)
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
            self.boton.setText(
                f"En vivo ({HISTORIA} s)" if modo == "vivo" else "Histórico (misión)"
            )
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

    CLAVES = [
        ("estado_fsw", "Estado FSW"),
        ("tiempo_mision", "Tiempo de misión [s]"),
        ("hora", "Hora UTC"),
        ("recibidos", "Recibidos"),
        ("perdidos", "Perdidos"),
        ("eco_comando", "Eco del comando"),
    ]

    def __init__(self, con_estado: bool = True) -> None:
        super().__init__()
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        self.ind = {}
        for clave, titulo in self.CLAVES:
            if clave == "estado_fsw" and not con_estado:
                continue
            caja, valor = indicador(titulo)
            self.ind[clave] = valor
            h.addWidget(caja, 1)
        self.toggle = QPushButton("Todos: En vivo")
        self.toggle.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.toggle.setMinimumHeight(48)
        h.addWidget(self.toggle)

    def actualizar(self, datos: dict) -> None:
        for clave, valor in self.ind.items():
            valor.setText(fmt(clave, datos[clave]) if datos[clave] != "" else "—")
        self.ind["perdidos"].setStyleSheet("color: #b03a2e" if datos["perdidos"] else "")


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
    columnas_xyz = 3

    def __init__(self, sim: Simulador) -> None:
        super().__init__()
        self.sim = sim
        self.franja = Franja(self.con_estado)
        self.modo_global = "vivo"
        self.franja.toggle.clicked.connect(self.alternar_global)
        gps = ["gps_latitud", "gps_longitud", "gps_altitud", "gps_satelites", "gps_hora"]
        vuelo = ["altitud", "vel_vertical", "presion", "temperatura"]
        self.t = {
            "vuelo": self.clase_tarjeta(
                "Vuelo y GPS" if self.gps_en_vuelo else "Vuelo",
                vuelo + (gps if self.gps_en_vuelo else []),
                [("Altitud", "m", ["altitud"])],
                columnas=2,
            ),
            "energia": self.clase_tarjeta(
                "Energía",
                ["tension", "corriente"],
                [("Tensión", "V", ["tension"]), ("Corriente", "A", ["corriente"])],
                columnas=2,
            ),
            "acel": self.clase_tarjeta(
                "Aceleración",
                ["acel_x", "acel_y", "acel_z"],
                [("Aceleración", "m/s²", ["acel_x", "acel_y", "acel_z"])],
                columnas=self.columnas_xyz,
            ),
            "rot": self.clase_tarjeta(
                "Rotación",
                ["rot_x", "rot_y", "rot_z"],
                [("Velocidad de rotación", "°/s", ["rot_x", "rot_y", "rot_z"])],
                columnas=self.columnas_xyz,
            ),
        }
        if not self.gps_en_vuelo:
            self.t["gps"] = self.clase_tarjeta("GPS", gps)
        self.t["vuelo"].nota.show()

    def alternar_global(self) -> None:
        self.modo_global = "historico" if self.modo_global == "vivo" else "vivo"
        for t in self.t.values():
            t.poner_modo(self.modo_global)
        texto = "En vivo" if self.modo_global == "vivo" else "Histórico"
        self.franja.toggle.setText(f"Todos: {texto}")

    def actualizar(self) -> None:
        s = self.sim
        datos = {
            **s.ultimo,
            "recibidos": s.recibidos,
            "perdidos": s.perdidos,
            "vel_vertical": s.vel_vertical,
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
    nombre = "Híbrido: chips de estado"

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
    nombre = "Híbrido: fases + pie de estado"
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
        cv.addWidget(label("Telecomandos", negrita=True, pt=PT + 2))
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
        actual = FASES.index(self.sim.ultimo["estado_fsw"])
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
    nombre = "Híbrido: línea de avisos"
    gps_en_vuelo = True

    def __init__(self, sim: Simulador) -> None:
        super().__init__(sim)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(4, 4, 4, 4)
        raiz.setSpacing(4)
        raiz.addWidget(self.franja)
        self.linea = label("Sin avisos", negrita=True)
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
            self.linea.setText("Sin avisos")
            nivel = "nada"
        else:
            self.linea.setText("   ▲   ".join(f"{t}: {x}" for t, x, _ in malos))
            nivel = "error" if any(n == "error" for *_, n in malos) else "aviso"
        self.linea.setStyleSheet(NIVEL[nivel] + "padding: 2px 8px;")


# --- variante G: lo elegido en la ronda 2 de la #7 ------------------------

VENTANAS = [("30 s", 30), ("60 s", 60), ("120 s", 120), ("Misión", None)]
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
        self.titulo = label("Recorrido", negrita=True, pt=PT + 2)
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
        for lado, texto in (("left", "Norte [m]"), ("bottom", "Este [m]")):
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
        self.boton.setText("Mapa" if ver_qr else "QR")

    def poner_modo(self, modo) -> None:
        pass  # el recorrido es siempre la misión entera

    def actualizar(self, sim: Simulador, datos: dict) -> None:
        if sim.t_lanzamiento is None:
            return
        i = bisect.bisect_left(sim.tiempos, sim.t_lanzamiento)
        lats, lons = sim.historia["gps_latitud"][i:], sim.historia["gps_longitud"][i:]
        lat0, lon0 = lats[0], lons[0]
        k = 111_320.0
        xs = [(lo - lon0) * k * math.cos(math.radians(lat0)) for lo in lons]
        ys = [(la - lat0) * k for la in lats]
        self.traza.setData(xs, ys)
        self.base.setData([0], [0])
        self.punto.setData(xs[-1:], ys[-1:])
        if datos["estado_fsw"] == "LANDED":
            lat, lon = datos["gps_latitud"], datos["gps_longitud"]
            texto = f"https://maps.google.com/?q={lat:.6f},{lon:.6f}"
            if texto != self.ultimo_qr:
                self.ultimo_qr = texto
                lado = max(80, min(self.pila.width(), self.pila.height() - 30))
                px = pixmap_qr(texto, lado)
                if px is None:
                    self.qr.setText("(falta segno:\nuv run --with segno ...)")
                else:
                    self.qr.setPixmap(px)
            self.coords.setText(f"{lat:.6f}\n{lon:.6f}")
            if not self.vio_aterrizaje:  # al aterrizar pasa solo al QR, una vez
                self.vio_aterrizaje = True
                self.boton.show()
                self.alternar()


class VarianteG(Hibrido):
    nombre = "Ronda 2: fases + pie, Vuelo y GPS, recorrido"
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
        self.global_ = combo_ventana("Todos: ")
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
        cv.addWidget(label("Telecomandos", negrita=True, pt=PT + 2))
        self.comandos = PanelComandos(sim, vertical=True, mostrar_eco=False)
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

    def actualizar(self) -> None:
        super().actualizar()
        s = self.sim
        actual = FASES.index(s.ultimo["estado_fsw"])
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
            val.setToolTip(f"Esperada {objetivo} ± {tol} m/s de bajada ({req})")
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

    nombre = "Ronda 3: Recorrido bajo los telecomandos"
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

    nombre = "Ronda 3: Recorrido bajo Vuelo y GPS"

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


class Ventana(QMainWindow):
    def __init__(self, inicial: str) -> None:
        super().__init__()
        nota = "Datos simulados" + ("; formato provisorio" if FORMATO.get("provisorio") else "")
        self.setWindowTitle(f"Avutardo GCS — PROTOTIPO — {nota}")
        self.sim = Simulador()
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

    def poner(self, clave: str) -> None:
        self.actual = clave
        self.vista = VARIANTES[clave](self.sim)
        self.setCentralWidget(self.vista)
        self.vista.actualizar()
        self.selector.texto.setText(f"{clave} ({self.vista.nombre})")
        self.selector.adjustSize()
        self.selector.raise_()
        self.ubicar_selector()

    def ciclar(self, paso: int) -> None:
        i = (self.claves.index(self.actual) + paso) % len(self.claves)
        self.poner(self.claves[i])

    def flecha(self, paso: int) -> None:
        if isinstance(QApplication.focusWidget(), QLineEdit):
            return
        self.ciclar(paso)

    def simular(self, que: str) -> None:
        if que == "pendrive":
            self.sim.pendrive = not self.sim.pendrive
        else:
            self.sim.enlace_caido = not self.sim.enlace_caido
        self.vista.actualizar()

    def adelantar(self) -> None:
        """F8: 30 s de vuelo de golpe, para llegar al aterrizaje sin esperar."""
        for _ in range(30):
            self.sim.paso()
        self.vista.actualizar()

    def tick(self) -> None:
        self.sim.paso()
        self.vista.actualizar()

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
        self.statusBar().showMessage(f"Captura: {destino}", 3000)

    def ubicar_selector(self) -> None:
        s = self.selector
        s.move((self.width() - s.width()) // 2, self.height() - s.height() - 6)

    def resizeEvent(self, e) -> None:  # noqa: N802 (nombre que impone Qt)
        super().resizeEvent(e)
        self.ubicar_selector()


ESTILO = (
    "QWidget { background: white; color: black; }"
    "QTableWidget, QHeaderView, QPushButton, QLineEdit { font-size: 14pt; }"
    "QTableWidget::item { padding: 0px 4px; }"
    "QPushButton { border: 2px solid #555; padding: 4px 10px; }"
    "QHeaderView::section { font-weight: bold; background: #eee; }"
)


def main() -> None:
    inicial = (sys.argv[1] if len(sys.argv) > 1 else "D").upper()
    app = QApplication(sys.argv)
    f = app.font()
    f.setPointSize(PT)
    app.setFont(f)
    app.setStyleSheet(ESTILO)
    configurar_pyqtgraph()
    v = Ventana(inicial if inicial in VARIANTES else "D")
    v.resize(1366, 768)  # el mínimo de #4, en píxeles lógicos
    v.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
