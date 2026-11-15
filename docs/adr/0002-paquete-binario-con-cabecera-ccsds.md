---
status: accepted
---

# El paquete de telemetría es binario, con cabecera CCSDS y CRC-16

El paquete de telemetría es binario y de largo fijo: 61 B en big-endian, campo
por campo. Lleva la cabecera primaria CCSDS 133.0-B-2 de 6 B, sin cabecera
secundaria, y su contador de 14 bits es el contador de secuencia (F1). Después
vienen 1 B con la versión del formato, los campos como enteros con un divisor
y un CRC-16/CCITT-FALSE sobre todo lo anterior. Un campo sin dato lleva el
centinela de su tipo. La forma exacta vive en `protocolo/telemetria.toml`. Se
decidió entre el 2026-11-07 y el 2026-11-09, en el grilling del formato de
telemetría (issue #10).

> **2026-11-14, versión 2 del formato:** el paquete pasa a 75 B (32 campos) y
> tarda 447 ms a SF9; la decisión no cambia. Las cifras de abajo son las de la
> versión 1. El margen con el telecomando está en la ADR 0003.

## Por qué

- **Tiempo en el aire.** El paquete y un telecomando tienen que entrar en el
  mismo segundo. A SF9, con BW 125 kHz, CR 4/5 y preámbulo 12, los 61 B tardan
  386 ms, y con un telecomando de 20 B sobran unos 385 ms. Una línea de texto
  con los mismos campos ronda los 147 B y tarda unos 775 ms: con el
  telecomando y las dos conmutaciones de la radio, se pasa del segundo.
- **X2.** El APID de la cabecera CCSDS es la dirección que pide el anexo, y es
  lo que separa nuestros paquetes de los de otros equipos en la misma
  frecuencia. El bit de tipo distingue la telemetría de los telecomandos con la
  misma cabecera.
- **El CRC cubre el camino completo.** La radio LoRa ya tiene su propio CRC,
  pero sólo protege el tramo de radio. El nuestro también cubre la UART, el
  puente, el USB y la conversión a hex, y es el que deja contar los
  descartados.

## Opciones consideradas

- **Una línea de texto ASCII separada por comas** (el formato provisorio). Se
  lee a simple vista y es fácil de depurar, pero no entra a SF9 junto con un
  telecomando y tiene largo variable. Lo que se pierde en legibilidad lo
  recupera la GCS: decodifica cada paquete y guarda el log crudo.
- **Una cabecera propia** (un byte de equipo y un contador). Ahorraría un par
  de bytes, pero habría que inventar y documentar lo que CCSDS ya define y
  ya está probado.
- **Una biblioteca de serialización** (MessagePack, Protocol Buffers…). Suma
  una dependencia a bordo y bytes de estructura, y el formato ya es de largo
  fijo y está descrito en el `.toml`.

## Consecuencias

- Los campos nuevos van siempre al final y la versión del formato sube: la GCS
  descarta lo que tenga una versión desconocida.
- Sin un decodificador no se puede leer un paquete. El log crudo guarda el hex
  tal como llegó, para rehacer el CSV.
- Los telecomandos usan la misma cabecera, con el tipo TC y el mismo APID
  (#11).
