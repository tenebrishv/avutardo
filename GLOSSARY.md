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
Los paquetes que la estación terrena aceptó y decodificó: forma y largo
correctos, CRC válido, APID nuestro con el tipo TM y versión del formato
conocida (G14). Un contador de secuencia repetido con datos nuevos también
cuenta.
_Evitar_: paquetes contados, contador de paquetes

**Perdidos**:
Los paquetes que faltan según los saltos del contador de secuencia entre dos
recibidos, contando la vuelta de 16 383 a 0 (G8). Un descartado también deja
un hueco, así que suma acá.
_Evitar_: fallidos

**Descartados**:
Lo que llegó del puente y no se pudo decodificar: línea mal formada, CRC
inválido o versión del formato desconocida. Va al log crudo. Un paquete de
otro largo, de otro APID o con el tipo TC no es descartado sino ajeno: va
sólo al log.
_Evitar_: corruptos, rechazados, perdidos

## Software de vuelo

**Software de vuelo (FSW)**:
El programa que corre a bordo del CanSat, en la Pico 2.
_Evitar_: firmware de vuelo, código de a bordo

**Estado de la FSW**:
La fase de la misión en la que el software de vuelo dice estar; viaja en cada
paquete de telemetría (G8). Son siete: BOOT, STANDBY, ASCENT, DESCENT 1,
DESCENT 2, LANDED y POWER OFF. En el paquete viajan como un número del 0 al 5
en ese orden; POWER OFF no tiene código porque no transmite, y 255 es "sin
dato".
_Evitar_: modo, fase de vuelo, estado del CanSat

## Simulación

**Vuelo de demostración**:
Un vuelo simulado fijo, idéntico en cada corrida, con instantes con nombre
(`standby`, `descenso`, `aterrizado`) de los que salen las capturas de la PDR.
_Evitar_: escenario, demo, vuelo de prueba
