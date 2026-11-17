# CCSDS Space Packet: la cabecera según la norma y las bibliotecas de referencia

Investigación de la issue #17. Consultado el 2026-11-16.

## Resumen

1. La cabecera primaria de 6 B que usa el formato coincide, campo por campo,
   con el CCSDS 133.0-B-2. Para el paquete de 75 B el largo vale 68 (`0x0044`),
   y para el telecomando de 14 B vale 7. El repo ya pone esos valores.
2. **A bordo:** conviene escribir la cabecera a mano. Son tres palabras de
   16 bit con shifts. Ninguna biblioteca C/C++ madura sirve sin traer un
   framework (cFE, F´) o una dependencia joven (CCSDSPack).
3. **En tierra:** conviene escribirla a mano en el decodificador, que es el
   único módulo que conoce el formato. Se testea contra `spacepackets` (o
   `ccsdspy`) como dependencia de desarrollo.
4. Para que los dos lados no se separen, sirven vectores de prueba en hexa
   compartidos: `006A C000 0044`, `006A C001 0044`, `006A FFFF 0044`.
5. Hay matices de redacción para corregir (ver "Discrepancias con el repo"),
   pero ningún error en los bytes.

## La cabecera según la norma

Fuente: CCSDS 133.0-B-2, *Space Packet Protocol*, Blue Book, Issue 2 (junio
de 2020), con los Editorial Change 1 (octubre de 2020) y 2 (septiembre de
2024), <https://ccsds.org/Pubs/133x0b2e2.pdf>. El enlace de siempre,
`public.ccsds.org/Pubs/133x0b2e2.pdf`, redirige ahí. Las secciones citadas
abajo son de ese PDF.

### Estructura y orden de bits y bytes

- **Bit 0 = el primero transmitido = el más significativo** (§1.6.3,
  figura 1-1): "the Most Significant Bit (MSB) shall be the first transmitted
  bit of the field, that is, 'Bit 0'".
- Los octetos se numeran desde 0 (§1.6.3). Como cada campo se transmite con
  el MSB primero y los octetos van en orden, un campo de 16 bit queda en
  **big-endian**. Es lo que hace `struct.pack('>H', …)`.
- Un Space Packet es la cabecera primaria (6 octetos, obligatoria) seguida
  del campo de datos (de 1 a 65 536 octetos, obligatorio) (§4.1.2.1 y
  figura 4-1). En total, entre 7 y 65 542 octetos (§4.1.2.2).
- La cabecera primaria tiene cuatro campos contiguos: versión (3 bit),
  identificación (13 bit), control de secuencia (16 bit) y largo de datos
  (16 bit) (§4.1.3.1 y figura 4-2).

### Campo por campo

| Bits | Campo (norma) | Ancho | Lo que dice la norma | Valor nuestro |
|---|---|---|---|---|
| 0–2 | Packet Version Number | 3 | Vale `000` (§4.1.3.2.2). Según la nota, es el "Version 1 CCSDS Packet". | `000` |
| 3 | Packet Type | 1 | `0` = telemetría, `1` = telecomando (§4.1.3.3.2.3). | `0` (TM) y `1` (TC) |
| 4 | Secondary Header Flag | 1 | `1` si hay cabecera secundaria, `0` si no hay (§4.1.3.3.3.2). Es fija para un APID durante una fase de misión (§4.1.3.3.3.3). | `0` |
| 5–15 | APID | 11 | Valores de 0 a 2047. El idle es `11111111111` (2047) (§4.1.3.3.4.4). Es el único reservado: "There are no restrictions on the selection of APIDs except for the APID for Idle Packets" (nota 1 de §4.1.3.3.4). | 106 |
| 16–17 | Sequence Flags | 2 | `00` continuación, `01` primer segmento, `10` último y `11` sin segmentar (§4.1.3.4.2.2). | `11` |
| 18–31 | Packet Sequence Count o Packet Name | 14 | En TM es el Packet Sequence Count (§4.1.3.4.3.2). Es "continuous (modulo-16384)": después de 16 383 vuelve a 0, y no se reinicia antes "unless it is unavoidable" (§4.1.3.4.3.4). En TC puede ser el contador o un Packet Name, "any 14-bit binary pattern" (§4.1.3.4.3.2 y nota 4). | contador de secuencia (TM) y número de telecomando (TC) |
| 32–47 | Packet Data Length | 16 | C = (octetos del campo de datos) − 1 (§4.1.3.5.2 y §4.1.3.5.3). | 68 (TM) y 7 (TC) |

### Campo de datos y cabecera secundaria

- **Al menos 1 octeto:** "The Packet Data Field shall contain at least one
  octet" (§4.1.4.1.2). Por eso el campo de largo nunca representa un campo
  de datos vacío: C = 0 equivale a 1 octeto.
- **Se puede ir sin cabecera secundaria si hay datos de usuario.** La
  cabecera secundaria "shall be mandatory if no User Data Field is present in
  the Packet; otherwise, it is optional" (§4.1.4.2.1.2). El campo de datos de
  usuario es obligatorio cuando no hay cabecera secundaria (§4.1.4.3.2) y,
  si el paquete no es idle, lleva los datos de la aplicación (§4.1.4.3.4).
  Nuestro caso (flag `0`, APID 106, datos de usuario) es válido.
- El registro de APID que cita la norma (referencia [4], §1.7) es el de SANA:
  <https://sanaregistry.org/r/space_packet_protocol_application_process_id>.
  Según la nota 2 de §4.1.3.3.4, el único valor reservado ahí es el idle.

### El largo para nuestros paquetes

```text
C = octetos del campo de datos − 1 = (largo total − 6) − 1

telemetría:    C = (75 − 6) − 1 = 68 = 0x0044
telecomando:   C = (14 − 6) − 1 =  7 = 0x0007
```

La suma de los tamaños de `protocolo/telemetria.toml` da 6 + 1 + 66 + 2 = 75
(32 campos y 66 B de campos, leídos con `tomllib`). Coincide con el
encabezado del `.toml` y con `docs/gcs-decisiones.md`.

### Los 6 bytes, con nuestros valores

```text
palabra 1 = versión<<13 | tipo<<12 | sec<<11 | APID   = 0<<13 | 0<<12 | 0<<11 | 106 = 0x006A
palabra 2 = flags<<14 | contador                      = 0b11<<14 | N           = 0xC000 | N
palabra 3 = largo del campo de datos − 1              = 68                     = 0x0044
```

| Paquete | Bytes 0–5 en hexa |
|---|---|
| TM, N = 0 | `00 6A C0 00 00 44` |
| TM, N = 1 | `00 6A C0 01 00 44` |
| TM, N = 16 383 (antes de volver a 0) | `00 6A FF FF 00 44` |
| TC, número 8 (como en el test del repo) | `10 6A C0 08 00 07` |

Los cuatro valores salieron igual por tres caminos:

- a mano, con `struct.pack('>HHH', tipo << 12 | apid, 0b11 << 14 | n, largo - 7)`;
- con `cabecera_ccsds()` de [`protocolo/vista_formato.py`](../../protocolo/vista_formato.py);
- con `spacepackets` 0.32.0 (`SpacePacketHeader(...).pack()`).

Además, `SpacePacketHeader.unpack`, `ccsdspy.FixedLength.load(...,
include_primary_header=True)` y el `ccsds_generator` de `space_packet_parser`
decodificaron los mismos bytes como versión 0, TM, sin secundaria, APID 106,
flags 3 y largo 68. Todo corrió en Python 3.13.11. `spacepackets` rechaza un
contador de 16 384 con `ValueError`.

El repo ya fija estos bytes en
[`gcs/tests/test_vista_formato.py`](../../gcs/tests/test_vista_formato.py):
`006A C09C 0044` (TM, contador 156) y `106A C008 0007` (TC, número 8).

## Bibliotecas en C/C++

Para cada repo, la licencia sale del archivo LICENSE. El "último push" es el
`pushed_at` de la API de GitHub al 2026-11-16, y la fecha de release se da
aparte.

| Biblioteca | Licencia | Estado | Depende de | Qué trae aparte de la cabecera | ¿Sirve en una MCU sin SO? |
|---|---|---|---|---|---|
| **NASA cFE**, módulo `msg` ([nasa/cFE](https://github.com/nasa/cFE), [`modules/msg/fsw/src/cfe_msg_ccsdspri.c`](https://github.com/nasa/cFE/blob/dev/modules/msg/fsw/src/cfe_msg_ccsdspri.c)) | Apache-2.0 ([LICENSE](https://github.com/nasa/cFE/blob/dev/LICENSE)) | Activo. Último push 2026-10-29; última release v7.0.2-rc1 (2026-10-22), anterior estable v7.0.1 (2026-05-14). | Se compila dentro del árbol de cFS: CMake de misión ([`modules/msg/CMakeLists.txt`](https://github.com/nasa/cFE/blob/dev/modules/msg/CMakeLists.txt)) y cabeceras `cfe_msg.h` y `cfe_error.h`. Según el [README de cFS](https://github.com/nasa/cFS), una distribución de vuelo es "cFE, OSAL, PSP" y sus objetivos de compilación son Linux y RTEMS. | Los mensajes del software bus de cFS: getters y setters por campo, cabecera extendida opcional y cabeceras secundarias propias (6 B de tiempo en TLM; código de función y checksum en CMD, en [`default_cfe_msg_sechdr.h`](https://github.com/nasa/cFE/blob/dev/modules/msg/option_inc/default_cfe_msg_sechdr.h)). | No es razonable usarla como biblioteca suelta. Sirve como **referencia de lectura**: las máscaras (`0xE000`, `0x1000`, `0x0800`, `0x07FF`, `0xC000`, `0x3FFF`) y `CFE_MSG_SIZE_OFFSET 7` son las mismas cuentas que las nuestras. |
| **NASA F´ (F Prime)** ([nasa/fprime](https://github.com/nasa/fprime), [`Svc/Ccsds`](https://github.com/nasa/fprime/tree/devel/Svc/Ccsds)) | Apache-2.0 ([LICENSE.txt](https://github.com/nasa/fprime/blob/devel/LICENSE.txt)) | Muy activo. Último push 2026-11-16; última release v4.4.2 (2026-11-04). En `devel` ya no hay `Svc/FramingProtocol`. Lo de CCSDS está en `Svc/Ccsds` (`SpacePacketFramer`, `SpacePacketDeframer`, `TmFramer`, `TcDeframer`, `AosFramer`, `ApidManager`, SDLS…). | El framework F´ completo: componentes, puertos, FPP y su CMake. En MCU corre con [`fprime-baremetal`](https://github.com/fprime-community/fprime-baremetal) y [`fprime-arduino`](https://github.com/fprime-community/fprime-arduino) (Apache-2.0, últimos push 2026-10-14 y 2026-11-01). `fprime-arduino` trae toolchains `rpipico2.cmake` y `esp32.cmake` en [`cmake/toolchain`](https://github.com/fprime-community/fprime-arduino/tree/main/cmake/toolchain), o sea que **depende del core de Arduino**. | La pila de enlace entera: tramas TM/TC/AOS, SDLS, CFDP y gestión de APID. La cabecera es un `struct SpacePacketHeader` de tres `U16` en [`Svc/Ccsds/Types/Types.fpp`](https://github.com/nasa/fprime/blob/devel/Svc/Ccsds/Types/Types.fpp). | Sólo si se adopta F´ como arquitectura de la FSW. Para 6 B, no. |
| **libcsp** ([libcsp/libcsp](https://github.com/libcsp/libcsp)) | MIT ([LICENSE](https://github.com/libcsp/libcsp/blob/develop/LICENSE)) | Activo. Último push 2026-10-17; última release v2.1 (2025-10-11). | Según el README, "ported to run on FreeRTOS, Zephyr and Linux (POSIX)". | **No es CCSDS.** Es el *Cubesat Space Protocol*, una pila al estilo TCP/IP con cabecera propia, router y sockets ([README](https://github.com/libcsp/libcsp/blob/develop/README.md)). No implementa el Space Packet. | No aplica: no arma la cabecera CCSDS. |
| **CCSDSPack** ([ExoSpaceLabs/CCSDSPack](https://github.com/ExoSpaceLabs/CCSDSPack)) | Apache-2.0 ([LICENSE](https://github.com/ExoSpaceLabs/CCSDSPack/blob/main/LICENSE)) | Joven y activo. Creado el 2024-10-25, último push 2026-11-13, release v2.1.0 (2026-10-25). Tiene 12 estrellas. | Núcleo C11, con API C++17 opcional. El README dice que `CCSDSPACK_BUILD_MCU=ON` produce bibliotecas *bare-metal*, que se puede compilar con `-fno-exceptions -fno-rtti` y que "the library as a whole is not described as heap-free". No nombra RP2350 ni ESP32-S3. | Validación, segmentación y reensamblado, PUS-A/PUS-C, tiempo CUC, *framing* de flujo y herramientas de host. | Técnicamente sí, según su README. Pero es mucho más de lo que hace falta, y el proyecto es joven y con pocos usuarios. No lo probé en ninguna de las dos placas. |
| **PacketLib** ([ASTRO-BO/PacketLib](https://github.com/ASTRO-BO/PacketLib)) | GPL-2.0 (según la API de GitHub; no leí el archivo) | Sin mantenimiento: último push 2019-09-10. | C++ en Unix, según la descripción del repo. | Codificación y decodificación de flujos de telemetría. | No. |

**ESA:** no encontré ninguna biblioteca C de Space Packet publicada por la
ESA (ni en GitHub ni en `gitlab.esa.int`) con una búsqueda dirigida. No
significa que no exista, sólo que no la ubiqué.

## Bibliotecas en Python

Los datos salen de la API JSON de PyPI (`https://pypi.org/pypi/<paquete>/json`),
y la licencia del archivo LICENSE del repo. "Probado en 3.13" quiere decir que
la instalé con `uv pip install` en un entorno de Python 3.13.11 (Windows) y
corrí los ejemplos de arriba.

| Paquete | Repo | Licencia | Última versión | Python declarado | Dependencias | Qué hace |
|---|---|---|---|---|---|---|
| [`spacepackets`](https://pypi.org/project/spacepackets/) | PyPI apunta a `github.com/us-irs/spacepackets-py`; la API de GitHub lo resuelve a [ustgt-irs/spacepackets-py](https://github.com/ustgt-irs/spacepackets-py) (último push 2026-10-20). | Apache-2.0 ([LICENSE](https://github.com/ustgt-irs/spacepackets-py/blob/main/LICENSE)) | 0.32.0 (2026-05-03) | `>=3.9`. Los clasificadores sólo listan 3.8 y 3.9, pero lo probé en 3.13. | `fastcrc~=0.3.0` (compilada; hay *wheels* `cp313` para `manylinux` x86_64, que es lo que usa el CI en `ubuntu-latest`), `deprecation~=2.1` | Cabecera Space Packet (armar y desarmar), PUS de ECSS, CFDP, USLP y tramas TM. Es la que mejor sirve como **oráculo de la cabecera**. |
| [`ccsdspy`](https://pypi.org/project/ccsdspy/) | [CCSDSPy/ccsdspy](https://github.com/CCSDSPy/ccsdspy) (último push 2026-10-28). `nasa/ccsdspy` no existe: la API da 404. | BSD-3-Clause ([LICENSE.rst](https://github.com/CCSDSPy/ccsdspy/blob/main/LICENSE.rst)) | 2.1.0 (2026-10-28) | `>=3.10`. Los clasificadores incluyen 3.13, y lo probé ahí. | `numpy`, `bitstruct`, `pyyaml`, `appdirs` | Decodifica archivos o flujos de paquetes en arrays de numpy. Los campos se declaran en Python (`FixedLength`, `PacketField`) y da también los campos de la cabecera primaria. Está pensada para lotes, no para un paquete por vez en vivo. |
| [`space_packet_parser`](https://pypi.org/project/space_packet_parser/) | [lasp/space_packet_parser](https://github.com/lasp/space_packet_parser) (último push 2026-11-04) | BSD-3 ([LICENSE.txt](https://github.com/lasp/space_packet_parser/blob/main/LICENSE.txt); GitHub lo marca `NOASSERTION`, PyPI dice `BSD-3-Clause`) | 6.2.0 (2026-09-13) | `>=3.10`, sin clasificadores de versión. Lo probé en 3.13. | `click`, `lxml`, `rich` | Decodifica campos definidos en **XTCE**. Sin XTCE, `ccsds_generator` separa paquetes y lee la cabecera. Usarlo para los campos obligaría a mantener un XTCE al lado de `telemetria.toml`, o sea, una segunda fuente del formato. |
| [`minspp`](https://pypi.org/project/minspp/) | [nunorc/minspp](https://github.com/nunorc/minspp) (último push 2026-07-29, 0 estrellas) | GPL-3.0 ([LICENSE.txt](https://github.com/nunorc/minspp/blob/master/LICENSE.txt)); PyPI no declara licencia | 0.0.7 (2026-07-29) | `>=3.10`, sin clasificadores. No lo probé. | ninguna declarada | Según su resumen en PyPI, "minimalistic implementation of the Space Packet specification". Es muy nuevo y la GPL-3.0 condiciona cómo se distribuye. |

Hay otros dos paquetes que no aportan para este caso.
[`tmtccmd`](https://pypi.org/project/tmtccmd/) 8.2.0 es un comandero TMTC
completo que depende de `spacepackets~=0.28.0` y de pyserial, y opcionalmente
de PyQt6. [`ccsds`](https://pypi.org/project/ccsds/) 0.1.0b20 es un *binding*
de [bmflynn/ccsds-rs](https://github.com/bmflynn/ccsds-rs), sigue en beta y
PyPI no declara su licencia.

## Recomendación

### A bordo (Pico 2 arma, Heltec transmite)

**Escribirla a mano.** Son tres palabras de 16 bit en big-endian:

```c
/* Bosquejo ilustrativo, no es código del repo. */
static void armar_cabecera(uint8_t *p, uint8_t tipo, uint16_t apid,
                           uint16_t contador, uint16_t largo_paquete)
{
    uint16_t identificacion = (uint16_t)(tipo << 12 | (apid & 0x07FF));
    uint16_t secuencia      = (uint16_t)(0xC000 | (contador & 0x3FFF));
    uint16_t largo_datos    = (uint16_t)(largo_paquete - 6 - 1);
    p[0] = identificacion >> 8; p[1] = identificacion;
    p[2] = secuencia >> 8;      p[3] = secuencia;
    p[4] = largo_datos >> 8;    p[5] = largo_datos;
}
```

Por qué:

- Las alternativas serias (cFE y F´) son frameworks enteros. F´ en estas
  placas pasa por el core de Arduino (`fprime-arduino` tiene toolchains
  `rpipico2` y `esp32`). Adoptarlo sería elegir la herramienta del firmware,
  y eso **lo decide el equipo**. libcsp no es CCSDS.
- CCSDSPack es la única liviana, pero es joven, trae mucho más de lo
  necesario y no está probada en estas placas.
- Escribir los bytes a mano con shifts no depende del *endianness* de la CPU
  (el RP2350 y el ESP32-S3 son *little-endian*). Un `struct` con *bit-fields*
  sí depende del compilador: conviene evitarlo.

Para verificarla sin depender de la herramienta que elija el equipo, el test
del firmware compara contra los mismos vectores en hexa que usa la GCS:
`006A C000 0044` (N = 0), `006A C001 0044` (N = 1), `006A FFFF 0044`
(N = 16 383) y `106A C008 0007` (TC número 8).

### En tierra (GCS, Python 3.13)

**Escribirla a mano en el decodificador y testearla contra una biblioteca
de referencia.**

- El decodificador todavía no existe en `gcs/src/`. Lo que hay hoy es
  `cabecera_ccsds()` en `protocolo/vista_formato.py`, con tests que fijan los
  bytes literales. La regla del repo es que el decodificador sea el único
  módulo que conoce el formato y que `telemetria.toml` sea la única fuente.
  Meter una biblioteca en producción sumaría una dependencia, compilada en el
  caso de `fastcrc`, para hacer dos `struct.unpack('>HHH', …)`.
- `spacepackets` como dependencia de desarrollo (`uv add --dev spacepackets`)
  sirve de oráculo. Un test arma la cabecera con nuestro código y la compara
  con `SpacePacketHeader(...).pack()`, y desarma con `SpacePacketHeader.unpack`
  para verificar APID, tipo, contador y `packet_len == 75`. Corre en CI: hay
  *wheels* de `fastcrc` para `cp313` y `manylinux` x86_64.
- **No** usar `space_packet_parser` para los campos: exigiría un XTCE, una
  segunda fuente del formato. `ccsdspy` sirve para analizar vuelos grabados
  en lote, pero no hace falta para la cabecera.
- De paso, `fastcrc.crc16.ibm_3740` (que trae `spacepackets`) da `0x29B1`
  sobre `b"123456789"`, igual que `crc16()` de `vista_formato.py`, y coincide
  con ella sobre 73 B al azar. Puede servir de oráculo también para el
  CRC-16/CCITT-FALSE. No verifiqué en una fuente primaria que "IBM-3740" sea
  otro nombre de CCITT-FALSE; sólo que dan lo mismo.

## Discrepancias con el repo

Ninguna afecta los bytes. El repo pone `0x0044` y `0x0007`, y eso es lo que
pide la norma.

1. **La issue #17 dice "largo del paquete menos 1".** La norma dice
   "octetos del **campo de datos** menos 1" (§4.1.3.5.2). Con "largo del
   paquete menos 1" saldría 74, no 68. El código
   (`largo_paquete - 6 - 1`) y los tests están bien; lo que está flojo es la
   redacción de la issue.
2. **"Versión 0".** El comentario de `test_vista_formato.py` dice "Versión
   0". El valor binario es `000`, pero la norma lo llama "Version 1 CCSDS
   Packet" (nota de §4.1.3.2.2). Es un matiz de nombre, no un error. Si se
   documenta, conviene "versión `000`".
3. **El número de telecomando es un Packet Name, no un Packet Sequence
   Count.** `telecomandos.toml` dice "su contador de 14 bits es el número de
   telecomando", y un reintento repite el número. La norma exige que el
   Packet Sequence Count sea continuo y módulo 16 384 (§4.1.3.4.3.4), así
   que un número que se repite no lo es. Pero en TC el campo puede ser un
   Packet Name, "any 14-bit binary pattern" (§4.1.3.4.3.2 y nota 4), y así
   el uso es válido. Habría que llamarlo Packet Name en el `.toml` y no
   "contador". Coincide con el glosario, que ya separa "número de
   telecomando" de "contador de secuencia".
4. **`cabecera_ccsds()` acepta el APID 2047 (idle).** Valida
   `0 <= apid < 2**11`, así que `cabecera_ccsds(TM, 2047, 0, 75)` devuelve
   `07FF C000 0044`. El test del `.toml` (`test_apid_106_en_11_bits`) ya
   exige `apid < 0x7FF`, así que en la práctica no pasa. Si esa función pasa
   al decodificador, conviene que también rechace el 2047. Tampoco valida que
   `tipo` sea 0 o 1.
5. **El ADR 0002 todavía dice "61 B" en el primer párrafo.** La nota del
   2026-11-14 ya aclara que en la versión 2 son 75 B. No es un error, pero la
   cifra del cuerpo es la de la versión 1.

## Preguntas abiertas

- **Mismo APID para TM y TC.** La norma dice que el Packet Sequence Count es
  "unique and independent per each user application as identified by the
  APID" (§4.1.3.4.3.3). Si el TC usa Packet Name (discrepancia 3), no choca
  con el contador de la TM. ¿El equipo lo documenta así? No bloquea nada.
- **El reinicio del contador.** La norma permite reiniciarlo sólo si es
  inevitable (§4.1.3.4.3.4). F1 pide que sobreviva a los reinicios, así que
  el diseño ya cumple más de lo que pide la norma.
- **Cuál biblioteca va de oráculo en los tests de la GCS** (`spacepackets` u
  otra), y si se suma ahora o cuando exista el decodificador. Lo decide el
  equipo.
- **El oráculo del firmware.** Depende de la herramienta que elija el equipo.
  Los vectores en hexa de arriba sirven con cualquiera.
- **No verificado:** que CCSDSPack compile para RP2350 o ESP32-S3, y que el
  ejemplo C de arriba compile. No lo probé.

## Fuentes

- CCSDS 133.0-B-2, *Space Packet Protocol*, Blue Book, Issue 2, EC 2 (2024):
  <https://ccsds.org/Pubs/133x0b2e2.pdf> (§1.6.3, §4.1.2, §4.1.3, §4.1.4;
  figuras 1-1, 4-1 y 4-2).
- Registro SANA de APID:
  <https://sanaregistry.org/r/space_packet_protocol_application_process_id>.
- Repo: [`protocolo/telemetria.toml`](../../protocolo/telemetria.toml),
  [`protocolo/telecomandos.toml`](../../protocolo/telecomandos.toml),
  [`protocolo/vista_formato.py`](../../protocolo/vista_formato.py),
  [`gcs/tests/test_vista_formato.py`](../../gcs/tests/test_vista_formato.py),
  [`gcs/tests/test_telemetria_toml.py`](../../gcs/tests/test_telemetria_toml.py),
  [`docs/adr/0002-paquete-binario-con-cabecera-ccsds.md`](../adr/0002-paquete-binario-con-cabecera-ccsds.md),
  [`GLOSSARY.md`](../../GLOSSARY.md), [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).
- C/C++: <https://github.com/nasa/cFE>, <https://github.com/nasa/cFS>,
  <https://github.com/nasa/fprime>,
  <https://github.com/fprime-community/fprime-arduino>,
  <https://github.com/fprime-community/fprime-baremetal>,
  <https://github.com/libcsp/libcsp>,
  <https://github.com/ExoSpaceLabs/CCSDSPack>,
  <https://github.com/ASTRO-BO/PacketLib>.
- Python: <https://pypi.org/project/spacepackets/>,
  <https://pypi.org/project/ccsdspy/>,
  <https://pypi.org/project/space_packet_parser/>,
  <https://pypi.org/project/minspp/>, <https://pypi.org/project/tmtccmd/>,
  <https://pypi.org/project/ccsds/>, <https://pypi.org/project/fastcrc/>, y sus
  repos enlazados en las tablas.
