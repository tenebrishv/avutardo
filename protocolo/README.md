# protocolo

El formato de telemetría es compartido por la Pico, la Heltec y la estación
terrena, y vive en un solo lugar: **`telemetria.toml`**.

- La estación terrena lo lee al arrancar: el decodificador es el único módulo
  que conoce el formato.
- Cuando arranque la FSW, un script va a generar desde acá el `telemetria.h`
  de la Pico.
- Para cambiar un campo, se cambia acá, sin tocar código.

> **El `telemetria.toml` actual es PROVISORIO.** El equipo todavía no definió
> el formato; los campos salen de lo que pide el Anexo A v2 para que el
> simulador funcione. El campo `eco_comando` es una propuesta para llevar a esa
> definición.

## Pendiente

- **Formato de los telecomandos:** lo define el equipo.
- **Envoltorio del puente:** la Heltec de tierra es un puente transparente que
  le agrega a cada paquete el RSSI (y el SNR). Su forma la define quien escriba
  el firmware de la Heltec.
