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

Correr, desde `gcs/`:

    uv run python prototipos/pantalla.py        # arranca en G2B, la elegida
    uv run python prototipos/pantalla.py A      # arranca en A
    uv run python prototipos/pantalla.py G2A    # la ronda 5 (#23)

Teclas: ← y → cambian de variante, F11 alterna pantalla completa, F12 guarda
una captura al doble de píxeles en `prototipos/capturas/` (como pide #4, Q6).
Para ver los avisos: F6 saca y pone el pendrive, F7 corta y repone el enlace.
F8 adelanta 30 s de vuelo (para llegar al aterrizaje y ver el QR de G).

Para probar la simulación:

    F5        reinicia el vuelo desde STANDBY
    Espacio   pausa y reanuda
    F9        velocidad ×1 → ×5 → ×10
    1 a 5     salta a STANDBY, ASCENT, DESCENT_1, DESCENT_2 o LANDED
    F1        ráfaga de 5 paquetes perdidos
    F2        el próximo paquete llega con el CRC roto (descartado y perdido)
    F3        GPS sin fix (0 satélites, posición sin dato) / con fix
    F4        batería baja (1.5 V menos) / normal
    Shift+F4  BAT_CURRENT sin dato / con dato (hueco en la curva, "—" en el
              número y en el rendimiento)
    F10       reinicio de la FSW: 3 s sin transmitir, un paquete en BOOT y
              sigue en su estado; el contador y el tiempo de misión siguen
              (F1, F2, F5)

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
TOML_TC = RAIZ / "protocolo" / "telecomandos.toml"
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
with TOML_TC.open("rb") as f:
    COMANDOS = {c["nombre"]: c for c in tomllib.load(f)["comando"]}


def fmt(nombre: str, valor) -> str:
    """Punto decimal y espacio fino de miles, como la norma del equipo."""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, float) and math.isnan(valor):
        return "—"  # sin dato
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
        # Eco y par extra (ADR 0003): sin telecomandos todavía, en blanco.
        self.eco_id = 0
        self.eco_codigo = ""
        self.resultado_comando = ""
        self.extra_id = ""
        self.extra_valor = 0
        self.cortado = False
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
        self.rssi = -70.0
        self.snr = 9.0
        self.ultimo: dict = {}
        self.registro: deque[str] = deque(maxlen=200)
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
            return alt, "DESCENT_1"
        t2 = 12 + (673 - 0.8 * 673) / 15
        alt = 0.8 * 673 - 3.5 * (tv - t2)
        return (alt, "DESCENT_2") if alt > 0 else (0.0, "LANDED")

    def paso(self) -> None:
        self.reloj += 1
        if self.cortado:
            return
        if self.reinicio > 0:
            # La FSW está reiniciando: no transmite, pero el tiempo de misión
            # sigue (F2) y el contador no salta (F1), así que no hay perdidos.
            self.reinicio -= 1
            self.t += 1
            self.boot = self.reinicio == 0
            return
        self.t += 1
        self.contador += 1
        tv = self.t - 45
        alt, estado = self._perfil(tv)
        rot_z = random.gauss(0, 3) + (90 if 12 <= tv < 60 else 0)
        energia = self._energia(estado, rot_z)
        if self.boot:  # el primer paquete después del reinicio
            estado = "BOOT"
            self.boot = False
        if estado not in ("STANDBY", "LANDED"):
            self.deriva += 1
        if self.ultimo and estado != self.ultimo["estado_fsw"]:
            self.t_cambio = self.t
        alt += random.gauss(0, 0.4)
        r = random.gauss
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
            "modo": "FLIGHT",
            "hora": datetime.now(UTC).strftime("%H:%M:%S"),
            "tiempo_mision": self.t,
            # Ambiental
            "presion": 101325 * (1 - 2.25577e-5 * alt) ** 5.25588 + r(0, 3),
            "altitud": alt - self.offset_alt,
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
        if self.rafaga > 0:
            self.rafaga -= 1
            return
        if self.crc_roto > 0:  # llega, pero no se decodifica: descartado y hueco
            self.crc_roto -= 1
            self.descartados += 1
            return
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

    def _energia(self, estado: str, rot_z: float) -> dict:
        """Los seis campos del INA3221 (#23). Corriente positiva = consumo.

        La barra de 3.3 V sale de la tabla de consumos de la planilla (punto 65
        de la PDR), con la Heltec al 57 % de TX: cierra con 4.64 Wh en 120 min.
        Cada corriente es el promedio del segundo, no una muestra de la TX.
        """
        r = random.gauss
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

    def saltar(self, estado: str) -> None:
        """Corre el vuelo hasta que el perfil llegue a `estado` (sólo hacia adelante)."""
        for _ in range(1000):
            if self.cortado or self._perfil(self.t - 45)[1] == estado:
                return
            self.paso()

    def telecomando(self, nombre: str, argumento: str = "") -> None:
        """Llega un telecomando: vuelve como eco (número, código y resultado).

        `nombre` es el de `telecomandos.toml` (CAL_ALT, CX…). De juguete: sólo
        se rechaza un código desconocido o uno fuera de `solo_en_estado`.
        """
        nombre = nombre.upper()
        comando = COMANDOS.get(nombre)
        estado = self.ultimo.get("estado_fsw", "STANDBY")
        aceptado = comando is not None and estado in comando.get("solo_en_estado", [estado])
        self.eco_id += 1
        self.eco_codigo = nombre if comando else f"?{nombre}"
        self.resultado_comando = "ACCEPTED" if aceptado else "REJECTED"
        if not aceptado:
            return
        if nombre == "CAL_ALT":
            self.offset_alt += self.ultimo.get("altitud", 0.0)
        if nombre == "GET_SENSORS":  # F4: responde por el par extra
            self.extra_id, self.extra_valor = nombre, 0b11111  # los cinco sensores
        if nombre == "CX" and argumento.upper() == "OFF":
            self.paso()  # el eco sale en un último paquete
            self.cortado = True


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
            ("Altitud cero", "CAL_ALT", True),
            ("Hora UTC", "TIME_SET", False),
            ("Datos extra", "GET_SENSORS", False),
            ("Cortar la telemetría", "CX OFF", True),
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
        self.sim.telecomando(*nombre.split())

    def mandar_linea(self) -> None:
        if partes := self.linea.text().split():
            self.sim.telecomando(*partes[:2])
            self.linea.clear()

    def actualizar(self) -> None:
        self.eco.setText(f"Eco: {texto_eco(self.sim.ultimo)}")


GRAFICOS_G7 = [
    ("Altitud", "m", ["altitud"]),
    ("Tensión", "V", ["tension_bateria"]),
    ("Corriente", "A", ["corriente_bateria"]),
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
            f"{fmt('gps_latitud', p['gps_latitud'])}  {fmt('gps_longitud', p['gps_longitud'])}"
            f"  ({p['gps_satelites']} sat.)"
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
                "Vuelo",
                ["altitud", "presion", "temperatura"],
                ("Altitud", "m", ["altitud"]),
            ),
            Tarjeta(
                "Energía",
                ["tension_bateria", "corriente_bateria"],
                ("Tensión", "V", ["tension_bateria"]),
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
                ["gps_latitud", "gps_longitud", "gps_altitud", "gps_satelites"],
            ),
        ]
        # La corriente también tiene que graficarse (G7): segunda curva en Energía.
        energia = self.tarjetas[2]
        w = energia.findChild(pg.PlotWidget)
        energia.curvas["corriente_bateria"] = w.plot(pen=pg.mkPen(COLORES["dos"], width=TRAZO))
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
        extra = {
            "recibidos": self.sim.recibidos,
            "perdidos": self.sim.perdidos,
            "descartados": self.sim.descartados,
        }
        for t in self.tarjetas:
            t.actualizar(self.sim, extra)
        self.comandos.actualizar()


# --- variantes D, E y F: híbridos A + C (ronda 2 de la #7) ----------------

ETIQUETA_GCS = {
    "vel_vertical": "Vel. vertical [m/s]",
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
        ("descartados", "Descartados"),
        ("eco", "Eco del comando"),
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
    columnas_xyz = 3

    def __init__(self, sim: Simulador) -> None:
        super().__init__()
        self.sim = sim
        self.franja = Franja(self.con_estado)
        self.modo_global = "vivo"
        self.franja.toggle.clicked.connect(self.alternar_global)
        gps = ["gps_latitud", "gps_longitud", "gps_altitud", "gps_satelites"]
        vuelo = ["altitud", "vel_vertical", "presion", "temperatura"]
        self.t = {
            "vuelo": self.clase_tarjeta(
                "Vuelo y GPS" if self.gps_en_vuelo else "Vuelo",
                vuelo + (gps if self.gps_en_vuelo else []),
                [("Altitud", "m", ["altitud"])],
                columnas=2,
            ),
            "energia": self.tarjeta_energia(),
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

    def tarjeta_energia(self) -> QFrame:
        """La tarjeta de energía de las rondas 2 a 4; la ronda 5 la reemplaza."""
        return self.clase_tarjeta(
            "Energía",
            ["tension_bateria", "corriente_bateria"],
            [("Tensión", "V", ["tension_bateria"]), ("Corriente", "A", ["corriente_bateria"])],
            columnas=2,
        )

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


# --- ronda 5 (#23): el bloque de energía ----------------------------------

NAN = float("nan")
TENSIONES = ["tension_bateria", "tension_3v3"]
CORRIENTES = ["corriente_bateria", "corriente_3v3"]
CANALES = [  # (tensión, corriente) de cada canal del INA3221
    ("tension_bateria", "corriente_bateria"),
    ("tension_3v3", "corriente_3v3"),
    ("tension_panel", "corriente_panel"),
]
ETIQUETA = {c["nombre"]: c["etiqueta"] for c in CAMPOS}
ETIQUETA["rendimiento"] = "BUCK_EFFICIENCY"  # lo calcula la GCS: no es un campo
COLOR_CANAL = {"bateria": COLORES["uno"], "3v3": COLORES["dos"], "panel": "#555"}


def canal(nombre: str) -> str:
    return nombre.rsplit("_", 1)[1]  # tension_bateria → bateria


def corto(nombre: str) -> str:
    return ETIQUETA[nombre].split("_")[0]  # BAT_VOLTAGE → BAT


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


def fmt_energia(nombre: str, valor: float, con_unidad: bool = True) -> str:
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
    texto = f"{valor:.{dec}f}"
    return f"{texto} {unidad}" if con_unidad else texto


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
        cab.addWidget(label("Energía", negrita=True, pt=PT + 2))
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

    def valor(self, nombre: str, prefijo: str = "", con_unidad: bool = True, **kw) -> QLabel:
        lb = label("—", negrita=True, **kw)
        lb.setToolTip(ETIQUETA.get(nombre, nombre))
        self.valores[nombre] = (lb, prefijo, con_unidad)
        return lb

    def fila_abajo(self) -> QHBoxLayout:
        """Panel y rendimiento, sin gráfico: la escala del panel aplastaría las
        otras curvas."""
        h = QHBoxLayout()
        h.setSpacing(10)
        h.addWidget(label(corto("tension_panel")))  # SOLAR, una sola vez
        h.addWidget(self.valor("tension_panel"))
        h.addWidget(self.valor("corriente_panel"))
        h.addStretch(1)
        h.addWidget(label(ETIQUETA["rendimiento"]))
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
        for nombre, (lb, prefijo, con_unidad) in self.valores.items():
            lb.setText(prefijo + fmt_energia(nombre, valor_energia(nombre, datos), con_unidad))
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
            col.addWidget(label(corto(tension), negrita=True, pt=PT + 2))
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
                tabla.addWidget(self.valor(nombre, con_unidad=False, alinear=derecha), f, c)
        izq.addLayout(tabla)
        izq.addStretch(1)
        rend = QHBoxLayout()
        rend.addWidget(label(ETIQUETA["rendimiento"]))
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
    nombre = "Ronda 5 (#23): energía por magnitud"

    def tarjeta_energia(self) -> QFrame:
        return EnergiaPorMagnitud()


class VarianteG2B(VarianteG2):
    nombre = "Ronda 5 (#23): energía por canal"

    def tarjeta_energia(self) -> QFrame:
        return EnergiaPorCanal()


class VarianteG2C(VarianteG2):
    nombre = "Ronda 5 (#23): energía, números primero"

    def tarjeta_energia(self) -> QFrame:
        return EnergiaNumeros()


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
            Qt.Key.Key_F10: lambda: self.falla("reinicio"),
        }
        for i, fase in enumerate(FASES):
            teclas[Qt.Key(Qt.Key.Key_1.value + i)] = lambda f=fase: self.saltar(f)
        for tecla, accion in teclas.items():
            QShortcut(QKeySequence(tecla), self, accion)
        self.actualizar_titulo()

    def actualizar_titulo(self) -> None:
        nota = "Datos simulados" + ("; formato provisorio" if FORMATO.get("provisorio") else "")
        marcha = "EN PAUSA" if self.pausado else f"×{self.velocidad}"
        self.setWindowTitle(f"Avutardo GCS — PROTOTIPO — {nota} — {marcha}")

    def avisar(self, texto: str) -> None:
        self.statusBar().showMessage(texto, 3000)

    def reiniciar(self) -> None:
        """F5: un vuelo nuevo desde STANDBY, en la misma variante."""
        self.sim = Simulador()
        self.poner(self.actual)
        self.avisar("Vuelo reiniciado")

    def pausar(self) -> None:
        if isinstance(QApplication.focusWidget(), QLineEdit):
            return
        self.pausado = not self.pausado
        self.actualizar_titulo()
        self.avisar("En pausa" if self.pausado else "En marcha")

    def acelerar(self) -> None:
        self.velocidad = {1: 5, 5: 10, 10: 1}[self.velocidad]
        self.actualizar_titulo()
        self.avisar(f"Velocidad ×{self.velocidad}")

    def saltar(self, fase: str) -> None:
        """1 a 5: hacia adelante corre el vuelo; hacia atrás, lo reinicia antes."""
        if isinstance(QApplication.focusWidget(), QLineEdit):
            return
        actual = FASES.index(self.sim._perfil(self.sim.t - 45)[1])
        if FASES.index(fase) < actual or self.sim.cortado:
            self.sim = Simulador()
            self.poner(self.actual)
        self.sim.saltar(fase)
        self.vista.actualizar()
        self.avisar(f"Salto a {fase}")

    def falla(self, que: str) -> None:
        s = self.sim
        if que == "rafaga":
            s.rafaga = 5
            texto = "Ráfaga: se pierden los próximos 5 paquetes"
        elif que == "crc":
            s.crc_roto = 1
            texto = "El próximo paquete llega con el CRC roto"
        elif que == "gps":
            s.sin_fix = not s.sin_fix
            texto = "GPS sin fix" if s.sin_fix else "GPS con fix"
        elif que == "bateria":
            s.bateria_baja = not s.bateria_baja
            texto = "Batería baja" if s.bateria_baja else "Batería normal"
        elif que == "ina":
            s.ina_sin_dato = not s.ina_sin_dato
            texto = "BAT_CURRENT sin dato" if s.ina_sin_dato else "BAT_CURRENT con dato"
        else:
            s.reinicio = 3
            texto = "Reinicio de la FSW: 3 s sin transmitir"
        self.avisar(texto)

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
        if self.pausado:
            return
        for _ in range(self.velocidad):
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
    inicial = (sys.argv[1] if len(sys.argv) > 1 else "G2B").upper()
    app = QApplication(sys.argv)
    f = app.font()
    f.setPointSize(PT)
    app.setFont(f)
    app.setStyleSheet(ESTILO)
    configurar_pyqtgraph()
    v = Ventana(inicial if inicial in VARIANTES else "G2B")
    v.resize(1366, 768)  # el mínimo de #4, en píxeles lógicos
    v.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
