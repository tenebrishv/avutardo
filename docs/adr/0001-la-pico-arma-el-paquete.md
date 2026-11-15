---
status: accepted
---

# La Pico arma el paquete de telemetría y la Heltec de a bordo no conoce el formato

La Pico 2 arma el paquete de telemetría completo (cabecera CCSDS, campos y
CRC) y se lo pasa por la UART a la Heltec de a bordo, que lo transmite sin
tocarlo. En sentido contrario, la Heltec le reenvía a la Pico, también sin
interpretarlo, todo lo que recibe por radio. La Heltec de a bordo queda tan
transparente como el puente de tierra: ningún firmware de la Heltec depende de
`protocolo/telemetria.toml`. Se decidió el 2026-11-07, en el grilling del
formato de telemetría (issue #10).

## Por qué

El GPS tiene que llegar a la Pico igual, lo arme quien lo arme:

- **F3**: la calibración pone en hora el DS3231 con el GPS, y el DS3231
  cuelga de la Pico.
- Pasar el GPS a una lectura cada 10 s por debajo de 6.4 V lo decide quien
  mide la batería, y el INA3221 (antes figuraba como INA226) está en la Pico.
- **F1 y F2**: el contador de secuencia y el tiempo de misión se guardan en
  la flash de la Pico, así que la cabecera también es suya.

Con eso, que la Heltec "le sume el GPS" a lo que arma la Pico no ahorra
ningún viaje por la UART. El GPS iría a la Pico por F3 y además la Heltec lo
insertaría en el paquete: dos caminos para el mismo dato.

## Opciones consideradas

- **La Heltec le suma el GPS al paquete** (lo que decía la biblioteca). Se
  descartó porque la Heltec tendría que conocer el formato: la escala y la
  posición de cada campo del GPS, y el CRC, que lo calcularía un procesador
  sobre datos que armó otro. Serían dos firmwares atados al `.toml` y la Pico
  tendría que mandarle a la Heltec la orden de bajar el GPS. No tiene ninguna
  ventaja a cambio.
- **La Pico arma todo** (la elegida). Hay una sola fuente del paquete a bordo
  y la Heltec queda como un módem.

## Consecuencias

- Por dónde le llega el GPS a la Pico es una cuestión del pinout, no del
  formato. La propuesta es cablear el módulo GPS (L76K) directo a una UART de
  la Pico, así cada UART lleva una sola cosa. Si el pinout no da, la Heltec le
  reenvía el NMEA crudo por la UART que comparten.
- La biblioteca dice que la Heltec "recibe los datos de la Pico por UART,
  les suma el GPS y transmite". Hay que corregirlo desde la biblioteca.
