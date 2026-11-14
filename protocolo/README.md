# protocolo

El formato de telemetría es compartido por la Pico, la Heltec y la estación
terrena, y vive en un solo lugar: **`telemetria.toml`**.

- La estación terrena lo lee al arrancar: el decodificador es el único módulo
  que conoce el formato.
- Cuando arranque la FSW, un script va a generar desde acá el `telemetria.h`
  de la Pico.
- Para cambiar un campo, se cambia acá, sin tocar código. Los campos nuevos van
  siempre al final y la `version` sube en 1.

## Versión 2 (#10)

Un paquete binario de 75 B por segundo, big-endian. A SF9, BW 125 kHz, CR 4/5
y preámbulo 12, tarda 447 ms en el aire.

| Bytes | Qué lleva |
|---|---|
| 0–5 | Cabecera primaria CCSDS 133.0-B-2: APID 106, tipo TM y el contador de secuencia de 14 bits (F1) |
| 6 | Versión del formato |
| 7–72 | Los 32 campos, en el orden del `.toml`: enteros con un `divisor` |
| 73–74 | CRC-16/CCITT-FALSE sobre los bytes 0–72 |

Los campos van agrupados por bloque:

| Bloque | Campos |
|---|---|
| Operación | estado de la FSW, modo, hora UTC (DS3231) y tiempo de misión |
| Ambiental | presión, altitud, temperatura y humedad |
| Energía (INA3221) | tensión y corriente de la batería, de la barra de 3.3 V y del panel solar |
| Navegación | latitud, longitud, altitud y satélites del GPS |
| Inercial (LSM6DSO32) | aceleración y velocidad de rotación en 3 ejes |
| Descenso | estado del segundo descenso y ángulo ordenado al servo |
| Enlace | potencia de transmisión |
| Telecomandos | eco (número, código y resultado) y un par extra reservado |

Cada campo tiene un `nombre` en español y una `etiqueta` en inglés
(`BAT_VOLTAGE`), que usan el encabezado del CSV (`BAT_VOLTAGE [V]`) y la
pantalla. El identificador del equipo es el APID y el contador de paquetes es el
contador de secuencia de la cabecera: no son campos.

Un campo sin dato lleva el centinela de su tipo: el máximo si es sin signo, el
mínimo si es con signo. La Heltec de a bordo transmite el paquete sin
interpretarlo; la de tierra lo pasa a la notebook como una línea
`<hex>,<rssi>,<snr>`.

La versión 1 (61 B) nunca salió del simulador, así que la 2 reordena los
campos. Desde el primer paquete real, los campos nuevos van siempre al final.

Los tests de `gcs/tests/test_telemetria_toml.py` controlan que el archivo esté
bien formado y que coincida con la tabla acordada.

## Pendiente

- **Formato de los telecomandos**, con sus códigos (`eco_codigo`) y el
  significado del par extra (`extra_id`, `extra_valor`): #11.
