# protocolo

El formato de telemetría y el de los telecomandos son compartidos por la Pico,
la Heltec y la estación terrena, y cada uno vive en un solo lugar:
**`telemetria.toml`** y **`telecomandos.toml`**.

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
| Telecomandos | eco (número, código y resultado) y el par extra, la respuesta a la última consulta |

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

## Telecomandos, versión 1 (#11)

Un telecomando binario de 14 B, big-endian, con la misma cabecera que la
telemetría y el tipo TC. A SF9 tarda 181 ms en el aire.

| Bytes | Qué lleva |
|---|---|
| 0–5 | Cabecera primaria CCSDS 133.0-B-2: APID 106, tipo TC y el número de telecomando en el contador de 14 bits |
| 6 | Versión del formato de telecomandos (independiente de la de telemetría) |
| 7 | Código del comando: su posición en el `.toml`, desde 0 |
| 8–11 | Parámetro, int32: un código de `valores`, un número en su unidad, o 0 |
| 12–13 | CRC-16/CCITT-FALSE sobre los bytes 0–11 |

Son 19 comandos en ocho grupos: comunicaciones (`CX`, `TX_POWER`), hora
(`TIME_SET`, `TIME_SYNC`), calibración (`CAL_ALT`, `CAL_IMU`), simulación
(`SIM`, `SIMP`), descenso (`SERVO`, `DESCENT2`), cámaras (`CAM1`, `CAM2`),
consultas y misión (`RESET_MISSION`).

No hay ACK aparte: el eco de cada paquete de telemetría (`eco_id`,
`eco_codigo`, `resultado_comando`) confirma el último telecomando que llegó
(ADR 0003). El `.toml` dice, para cada comando, en qué estados o modos se
acepta, el rango de su parámetro y si es un comando con confirmación.

Las **consultas** (`CAM_STATUS`, `GET_SENSORS`, `TIME_STATUS`, `GET_P0`,
`GET_RESETS`, `GET_BAT`) responden por el **par extra** de la telemetría:
`extra_id` lleva el código de la consulta y `extra_valor` la respuesta, que se
repite en cada paquete hasta la consulta siguiente. El `.toml` fija la forma de
cada respuesta: un número, un mapa de bits, una lista de valores o dos mitades
de 16 bits.

Los tests de `gcs/tests/test_telecomandos_toml.py` controlan que el archivo
esté bien formado, que coincida con la tabla acordada y que sus estados y
modos existan en `telemetria.toml`.
