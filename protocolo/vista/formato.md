# El formato, sin codificar y codificado

Generado por `uv run protocolo/vista_formato.py` desde `telemetria.toml`
(versión 2) y `telecomandos.toml` (versión 1).
No se edita a mano: si cambia un `.toml`, se vuelve a generar.

## Telemetría: un paquete de 75 B

Big-endian, campo por campo. Los campos son enteros: valor físico = entero /
divisor. Las partes entre paréntesis no son campos del `.toml`.

| Bytes | Etiqueta | Unidad | Tipo | Largo [B] | Requisito |
|---|---|---|---|---|---|
| 0–5 | (cabecera CCSDS) |  | CCSDS | 6 | X2 F1 |
| 6 | (versión) |  | uint8 | 1 |  |
| 7 | STATE |  | uint8 | 1 | G8 |
| 8 | MODE |  | uint8 | 1 |  |
| 9–12 | RTC_DATETIME | s | uint32 | 4 | F3 |
| 13–14 | MISSION_TIME | s | uint16 | 2 | G3 F2 |
| 15–18 | PRESSURE | Pa | uint32 | 4 | X5 |
| 19–20 | ALT_BARO | m | int16 | 2 | X5 SN1 |
| 21–22 | TEMPERATURE | °C | int16 | 2 | X5 SN2 |
| 23 | HUMIDITY | % | uint8 | 1 |  |
| 24–25 | BAT_VOLTAGE | V | uint16 | 2 | SN3 G7 |
| 26–27 | BAT_CURRENT | A | int16 | 2 | SN8 G7 |
| 28–29 | BUS33_VOLTAGE | V | uint16 | 2 |  |
| 30–31 | BUS33_CURRENT | A | int16 | 2 |  |
| 32–33 | SOLAR_VOLTAGE | V | uint16 | 2 | X6 |
| 34–35 | SOLAR_CURRENT | A | int16 | 2 | X6 |
| 36–39 | GPS_LATITUDE | ° | int32 | 4 | X5 SN4 |
| 40–43 | GPS_LONGITUDE | ° | int32 | 4 | X5 SN4 |
| 44–47 | GPS_ALTITUDE | m | int32 | 4 | X5 SN4 |
| 48 | GPS_SATS |  | uint8 | 1 | X5 SN4 |
| 49–50 | ACCEL_X | m/s² | int16 | 2 | X5 SN5 |
| 51–52 | ACCEL_Y | m/s² | int16 | 2 | X5 SN5 |
| 53–54 | ACCEL_Z | m/s² | int16 | 2 | X5 SN5 |
| 55–56 | GYRO_X | °/s | int16 | 2 | X5 SN5 |
| 57–58 | GYRO_Y | °/s | int16 | 2 | X5 SN5 |
| 59–60 | GYRO_Z | °/s | int16 | 2 | X5 SN5 |
| 61 | DESCENT2_STATUS |  | uint8 | 1 | C4 |
| 62 | SERVO_CMD | ° | uint8 | 1 | C4 |
| 63 | TX_POWER | dBm | uint8 | 1 |  |
| 64–65 | CMD_ECHO_ID |  | uint16 | 2 | G15 |
| 66 | CMD_ECHO |  | uint8 | 1 | G15 |
| 67 | CMD_RESULT |  | uint8 | 1 | G15 |
| 68 | EXTRA_ID |  | uint8 | 1 | F4 |
| 69–72 | EXTRA_VALUE |  | int32 | 4 | F4 |
| 73–74 | (CRC-16) |  | uint16 | 2 |  |

## Telecomandos: 14 B

| Bytes | Etiqueta | Unidad | Tipo | Largo [B] | Requisito |
|---|---|---|---|---|---|
| 0–5 | (cabecera CCSDS) |  | CCSDS | 6 | X2 |
| 6 | (versión) |  | uint8 | 1 |  |
| 7 | (código) |  | uint8 | 1 | G15 |
| 8–11 | (parámetro) |  | int32 | 4 |  |
| 12–13 | (CRC-16) |  | uint16 | 2 |  |

El código del comando es su posición en `telecomandos.toml`, desde 0. El
parámetro es el código de uno de sus valores, un número en su unidad o 0.

| Código | Nombre | Parámetro | Unidad | Requisito |
|---|---|---|---|---|
| 0 | CX | ON / OFF |  |  |
| 1 | TX_POWER | 2 a 28 | dBm |  |
| 2 | TIME_SET | entero | s | F3 |
| 3 | TIME_SYNC | — |  |  |
| 4 | CAL_ALT | — |  | G1 |
| 5 | CAL_IMU | — |  |  |
| 6 | SIM | OFF / PRESSURE / FULL |  |  |
| 7 | SIMP | entero | Pa |  |
| 8 | SERVO | MIN / CENTER / MAX |  |  |
| 9 | DESCENT2 | ARM / DISARM |  | C4 |
| 10 | CAM1 | START / STOP / RESTART |  |  |
| 11 | CAM2 | START / STOP / RESTART |  |  |
| 12 | CAM_STATUS | — |  | F4 |
| 13 | GET_SENSORS | — |  | F4 |
| 14 | TIME_STATUS | — |  | F4 |
| 15 | GET_P0 | — |  | F4 |
| 16 | GET_RESETS | — |  | F4 |
| 17 | GET_BAT | — |  | X6 F4 |
| 18 | RESET_MISSION | — |  |  |

## Ejemplo: el mismo paquete, sin codificar y codificado

Sin codificar, al estilo de la planilla de infraestructura: el APID (`0106`),
el contador de secuencia y los campos en el orden del `.toml`, separados por
comas; `NA` es sin dato. Codificado, el mismo paquete en binario, con la
versión del formato y el CRC-16, que la línea ASCII no lleva. Tiempos en el
aire a SF9, BW 125 kHz, CR 4/5 y preámbulo de 12 símbolos.

| Paquete | Codificación | Largo [B] | Tiempo en el aire [ms] |
|---|---|---|---|
| telemetría | ASCII | 209 | 1 062 |
| telemetría | binario | 75 | 447 |
| telecomando | ASCII | 24 | 222 |
| telecomando | binario | 14 | 181 |

### Telemetría en ASCII (209 B, 1 062 ms)

```text
0106,156,DESCENT_1,FLIGHT,2026-11-12T13:14:03Z,155,94532,125.4,18.70,52,7.820,0.650,3.310,0.180,5.200,0.420,-54.8012000,-67.6921000,130.5,10,0.12,-0.08,9.72,1.2,-0.8,0.1,ARMED,90,22,17,17,ACCEPTED,17,512496720
```

### Telemetría en binario (75 B, 447 ms)

```text
00 6A C0 9C 00 44 02 03 00 6A F5 BB 9B 00 9B 00 01 71 44 04 E6 07 4E 34 1E
8C 02 8A 0C EE 00 B4 14 50 01 A4 DF 56 00 20 D7 A7 01 58 00 00 05 19 0A 00
0C FF F8 03 CC 00 0C FF F8 00 01 01 5A 16 00 11 11 00 11 1E 8C 14 50 8B D6
```

### Telecomando en ASCII (24 B, 222 ms)

```text
CMD,0106,0017,GET_BAT,NA
```

### Telecomando en binario (14 B, 181 ms)

```text
10 6A C0 11 00 07 01 11 00 00 00 00 83 27
```

El eco y el par extra de la telemetría responden a este telecomando: `GET_BAT`
devuelve la tensión de la batería y la del panel en las dos mitades de
`EXTRA_VALUE`.
