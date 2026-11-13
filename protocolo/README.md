# protocolo

El formato de telemetría es compartido por la Pico, la Heltec y la estación
terrena, y vive en un solo lugar: **`telemetria.toml`**.

- La estación terrena lo lee al arrancar: el decodificador es el único módulo
  que conoce el formato.
- Cuando arranque la FSW, un script va a generar desde acá el `telemetria.h`
  de la Pico.
- Para cambiar un campo, se cambia acá, sin tocar código. Los campos nuevos van
  siempre al final y la `version` sube en 1.

## Versión 1 (#10)

Un paquete binario de 61 B por segundo, big-endian:

| Bytes | Qué lleva |
|---|---|
| 0–5 | Cabecera primaria CCSDS 133.0-B-2: APID 106, tipo TM y el contador de secuencia de 14 bits (F1) |
| 6 | Versión del formato |
| 7–58 | Los 21 campos, en el orden del `.toml`: enteros con un `divisor` |
| 59–60 | CRC-16/CCITT-FALSE sobre los bytes 0–58 |

Un campo sin dato lleva el centinela de su tipo: el máximo si es sin signo, el
mínimo si es con signo. La Heltec de a bordo transmite el paquete sin
interpretarlo; la de tierra lo pasa a la notebook como una línea
`<hex>,<rssi>,<snr>`.

Los tests de `gcs/tests/test_telemetria_toml.py` controlan que el archivo esté
bien formado y que coincida con la tabla acordada.

## Pendiente

- **Formato de los telecomandos** y contenido del campo `eco_comando`: #11.
