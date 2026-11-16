"""PROTOTIPO: el video de demostración de la GCS para la PDR.

Corre el vuelo de demostración de `pantalla.py` (variante M4) fuera de
pantalla, graba un cuadro por cada segundo de vuelo y los junta con ffmpeg a
×2: 1920×1080 de pantalla más una franja de subtítulos en castellano abajo.
El diálogo de CAL_ALT se superpone (en el vuelo de demostración ese comando lo
manda el guion) y la consola se abre cuando llega el paquete con el CRC roto.

    uv run --with segno python prototipos/video.py salida.mp4
    uv run --with segno python prototipos/video.py salida.mp4 --tema "high contrast"

Necesita ffmpeg en el PATH.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pantalla as p  # noqa: E402
from PySide6.QtCore import QRect, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

ANCHO, ALTO_PANTALLA, ALTO_FRANJA = 1920, 1080, 96
VELOCIDAD = 2  # segundos de vuelo por segundo de video
FIN = 198  # segundos de la notebook: 10 s después de LANDED, y 1:39 de video
DIALOGO = range(12, 15)  # el diálogo de CAL_ALT, antes de que salga a los 15 s
CONSOLA = range(56, 72)  # el CRC roto llega a los 60 s (30 desde el despegue)

# Segundo de la notebook desde el que se muestra cada subtítulo. El vuelo de
# demostración es siempre el mismo: despegue a los 30 s, eyección a los 42 s,
# DESCENT_2 a los 51 s y LANDED a los 176 s.
SUBTITULOS = {
    0: "Arranque: la estación recibe un paquete por segundo desde la Heltec de tierra.",
    4: "STANDBY: GET_SENSORS pregunta qué sensores responden (F4). "
    "La respuesta llega en EXTRA_ID y EXTRA_VALUE.",
    12: "CAL_ALT pide confirmación antes de salir: pone la altitud en cero.",
    16: "Cada envío queda con su estado: PENDING, ACK, REJECTED o NO ACK.",
    32: "Despegue: la barra de fases pasa a ASCENT y arranca MISSION_TIME.",
    36: "Un hueco de 2 paquetes: Lost lo cuenta por el número de secuencia.",
    44: "Eyección a 673 m: DESCENT_1. Foreign cuenta los paquetes de otro equipo, que se filtran.",
    56: "La consola muestra cada paquete crudo: acá llega uno con el CRC roto (Discarded).",
    72: "DESCENT_2: DESCENT2_STATUS pasa a TRIGGERED y la velocidad de bajada se compara con C4.",
    100: "El enlace: RSSI, SNR, piso de ruido estimado y PER, todo calculado en la notebook.",
    140: "Tema light por defecto (G12). En la prueba al sol del 2026-11-16 "
    "se leyó mejor high contrast: se elige desde el pie.",
    176: "LANDED: el QR lleva la última posición a Google Maps para ir a buscarlo.",
}


def subtitulo(reloj: int) -> str:
    return SUBTITULOS[max(s for s in SUBTITULOS if s <= reloj)]


def cuadro(v: p.Ventana, texto: str, dialogo: QImage | None) -> QImage:
    """La pantalla a 1920×1080, con el diálogo encima si hay, y la franja."""
    pantalla = p.imagen(v)
    pantalla.setDevicePixelRatio(1)
    pantalla = pantalla.scaled(
        ANCHO,
        ALTO_PANTALLA,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    img = QImage(ANCHO, ALTO_PANTALLA + ALTO_FRANJA, QImage.Format.Format_RGB32)
    img.fill(QColor("#1c2a44"))
    pintor = QPainter(img)
    pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    pintor.drawImage(0, 0, pantalla)
    if dialogo is not None:
        pintor.fillRect(0, 0, ANCHO, ALTO_PANTALLA, QColor(128, 128, 128, 110))
        escala = ANCHO / (1366 * p.ESCALA)
        dialogo.setDevicePixelRatio(1)  # si no, se dibuja a la mitad
        d = dialogo.scaled(
            round(dialogo.width() * escala),
            round(dialogo.height() * escala),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        pintor.drawImage((ANCHO - d.width()) // 2, (ALTO_PANTALLA - d.height()) // 2, d)
    fuente = QFont("Segoe UI")
    fuente.setPixelSize(30)
    pintor.setFont(fuente)
    pintor.setPen(QColor("white"))
    franja = QRect(24, ALTO_PANTALLA, ANCHO - 48, ALTO_FRANJA)
    pintor.drawText(franja, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, texto)
    pintor.end()
    return img


def main() -> None:
    a = argparse.ArgumentParser(description="Avutardo GCS demo video (simulated data).")
    a.add_argument("salida", type=Path, help="the .mp4 to write")
    a.add_argument("--tema", choices=list(p.TEMAS), default="light")
    args = a.parse_args()
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg is not in the PATH")
    p.preparar_captura()
    app = QApplication(sys.argv[:1])
    f = app.font()
    f.setFamily("Segoe UI")
    f.setPointSize(p.PT)
    app.setFont(f)
    p.aplicar_tema(args.tema)
    if p.pixmap_qr("x", 10) is None:
        sys.exit("The video needs segno: uv run --with segno python ...")
    v = p.Ventana("M4", demo=True, tema=args.tema)
    v.timer.stop()
    v.resize(1366, 768)
    v.show()
    v.selector.hide()
    app.processEvents()
    dialogo = p.dialogo_confirmar(v, "CAL_ALT")
    dialogo.show()
    app.processEvents()
    img_dialogo = p.imagen(dialogo)
    dialogo.close()
    with tempfile.TemporaryDirectory() as carpeta:
        n = 0
        while v.sim.reloj < FIN:
            consola = v.sim.reloj in CONSOLA
            if v.vista.boton.isChecked() != consola:
                v.vista.boton.setChecked(consola)
            app.processEvents()
            esperado = (1366 * p.ESCALA, 768 * p.ESCALA)
            entera = p.imagen(v)
            assert (entera.width(), entera.height()) == esperado, entera.size()
            con_dialogo = img_dialogo if v.sim.reloj in DIALOGO else None
            cuadro(v, subtitulo(v.sim.reloj), con_dialogo).save(f"{carpeta}/c{n:04d}.png")
            n += 1
            v.sim.paso()
            v.refrescar()
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-framerate", str(VELOCIDAD), "-i", f"{carpeta}/c%04d.png",
                "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                "-movflags", "+faststart", str(args.salida),
            ],
            check=True,
        )  # fmt: skip
    print(f"Saved {args.salida} ({n} frames, {n / VELOCIDAD:.0f} s)")


if __name__ == "__main__":
    main()
