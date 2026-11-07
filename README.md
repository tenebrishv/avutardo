# Avutardo

Código del CanSat **Proyecto Avutardo**, del equipo de la UTN Facultad Regional
Tierra del Fuego en el Certamen CanSat Universitario 2026-2027 (CONAE y ACEMA).

| Carpeta | Qué es | Estado |
|---|---|---|
| [`gcs/`](gcs/) | Estación terrena: Python, PySide6 y pyqtgraph | Esqueleto |
| [`protocolo/`](protocolo/) | Formato de telemetría, compartido por todo lo demás | **Provisorio** |
| [`firmware/pico/`](firmware/pico/) | Software de vuelo de la Raspberry Pi Pico 2 | Sin código |
| [`firmware/heltec/`](firmware/heltec/) | Enlace LoRa (Heltec LoRa 32 V4), a bordo y en tierra | Sin código |
| [`firmware/camaras/`](firmware/camaras/) | Cámaras ESP32-S3-CAM | Sin código |
| [`docs/`](docs/) | Decisiones de diseño | |

## Estación terrena

Hace falta [uv](https://docs.astral.sh/uv/). Instala solo la versión de Python
y las dependencias exactas del `uv.lock`.

```bash
cd gcs
uv sync              # una vez, o cuando cambie el uv.lock
uv run avutardo-gcs  # abre la estación terrena
uv run pytest        # tests
uv run ruff check .  # lint
```

## Cómo se trabaja

Un issue por tema, una rama corta por issue y un PR a `main`. A `main` sólo
entra lo que pasa el CI (lint y tests).

## Licencia

[MIT](LICENSE).
