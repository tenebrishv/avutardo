# Avutardo

El CanSat del Proyecto Avutardo y su estación terrena: lo que viaja entre los
dos y cómo se cuenta.

## Enlace

**Paquete de telemetría**:
Lo que el CanSat transmite una vez por segundo: la lectura de todos sus campos,
con una cabecera CCSDS y un CRC.
_Evitar_: trama, mensaje, línea

**Telecomando**:
Una orden que la estación terrena le manda al CanSat; usa la misma cabecera
que el paquete de telemetría, con el tipo TC.
_Evitar_: comando de tierra, mensaje de subida

**Eco**:
El último telecomando que el CanSat recibió y ejecutó, devuelto en la
telemetría para verificarlo en tierra (G15).
_Evitar_: acuse, ACK, confirmación

**Comando con confirmación**:
Un telecomando que la estación terrena pide confirmar antes de mandarlo, porque
mandado por error en vuelo arruina datos o deja a la estación sin telemetría.
_Evitar_: comando irreversible, comando crítico

**APID**:
El identificador CCSDS que dice de quién es un paquete; es la dirección que
pide X2 y separa nuestros paquetes de los de otros equipos.
_Evitar_: ID de equipo, dirección, dirección de destino

**Versión del formato**:
El número que identifica qué edición de `protocolo/telemetria.toml` armó un
paquete; no es la versión CCSDS de la cabecera.
_Evitar_: versión del protocolo

**Puente**:
La Heltec de tierra: reenvía cada paquete a la notebook sin interpretarlo y le
agrega el RSSI y el SNR.
_Evitar_: receptor, módem, gateway

## Conteos

**Contador de secuencia**:
El número que el CanSat pone en cada paquete que transmite y que sobrevive a
los reinicios (F1).
_Evitar_: contador de paquetes, contador de transmitidos, número de paquete

**Recibidos**:
Los paquetes que la estación terrena aceptó: APID nuestro y CRC válido (G14).
_Evitar_: paquetes contados, contador de paquetes

**Perdidos**:
Los paquetes que faltan según los saltos del contador de secuencia entre dos
recibidos (G8).
_Evitar_: descartados, fallidos

## Software de vuelo

**Software de vuelo (FSW)**:
El programa que corre a bordo del CanSat, en la Pico 2.
_Evitar_: firmware de vuelo, código de a bordo

**Estado de la FSW**:
La fase de la misión en la que el software de vuelo dice estar; viaja en cada
paquete de telemetría (G8). Son siete: BOOT, STANDBY, ASCENT, DESCENT 1,
DESCENT 2, LANDED y POWER OFF.
_Evitar_: modo, fase de vuelo, estado del CanSat
