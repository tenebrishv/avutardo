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

**Número de telecomando**:
El número que la estación terrena pone en cada telecomando; un reintento
repite el mismo número, así el CanSat no ejecuta dos veces la misma orden.
_Evitar_: contador de secuencia (ése es el de la telemetría)

**Eco**:
El número y el código del último telecomando que llegó al CanSat, repetidos en
cada paquete de telemetría hasta el siguiente. Es la confirmación de que llegó
(el ACK), no de que se ejecutó: eso se verifica por el efecto.
_Evitar_: confirmación de ejecución, acuse aparte

**Rechazado**:
Un telecomando que llegó pero el CanSat no ejecuta: código desconocido,
parámetro fuera de rango o comando bloqueado en el modo o el estado actual.
Viaja junto con el eco; un rechazado no se reintenta.
_Evitar_: fallido, perdido

**Sin eco**:
Un telecomando que no apareció en el eco después de tres intentos; en
pantalla, *NO ACK*.
_Evitar_: sin confirmación (eso es otra cosa: ver comando con confirmación),
perdido, rechazado

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
otro largo, de otro APID o con el tipo TC no es descartado sino ajeno.
_Evitar_: corruptos, rechazados, perdidos

**Ajenos**:
Lo que llegó del puente y no es nuestro: otro largo, otro APID o el tipo TC.
Va al log crudo y tiene su propio conteo, que no se mezcla con recibidos,
perdidos ni descartados: muestra que la estación filtra a los otros equipos.
_Evitar_: descartados, extraños, ruido

**Transmitidos**:
Los paquetes que el CanSat transmitió desde el primero que recibió la
estación, según el contador de secuencia: los recibidos más los perdidos.
_Evitar_: enviados, contador de transmitidos

**Enlace perdido**:
La estación terrena lleva más de 3 s sin un recibido. Un perdido suelto no
alcanza: el enlace sigue activo.
_Evitar_: sin señal, desconectado

## Software de vuelo

**Software de vuelo (FSW)**:
El programa que corre a bordo del CanSat, en la Pico 2.
_Evitar_: firmware de vuelo, código de a bordo

**Estado de la FSW**:
La fase de la misión en la que el software de vuelo dice estar; viaja en cada
paquete de telemetría (G8). Son siete: BOOT, STANDBY, ASCENT, DESCENT_1,
DESCENT_2, LANDED y POWER OFF. En el paquete viajan como un número del 0 al 5
en ese orden; POWER OFF no tiene código porque no transmite, y 255 es "sin
dato".
_Evitar_: modo, fase de vuelo, estado del CanSat

**Comienzo de misión**:
El instante en que el CanSat se separa del cohete (X3); coincide con el paso
de ASCENT a DESCENT_1.
_Evitar_: despegue, lanzamiento, arranque

**Tiempo de misión**:
Los segundos transcurridos desde el comienzo de misión; sobrevive a reinicios
y cortes de energía (F2). Antes del comienzo de misión no hay tiempo de
misión.
_Evitar_: cronómetro, hora de misión

**Altitud**:
La altura respecto de la rampa, calculada a bordo a partir de la presión y de
la presión de referencia que fija la calibración de altitud cero (G1). Es la
misma que usa la FSW para decidir el segundo descenso (C4).
_Evitar_: altura, altitud GPS

**Segundo descenso**:
El sistema que la FSW libera al llegar al 80 % de la altitud máxima (C4), con
un servo. Tiene su propio estado: NOT_ARMED, ARMED o TRIGGERED. No es el
estado DESCENT_2 de la FSW: el CanSat puede estar en DESCENT_1 con el segundo
descenso ARMED.
_Evitar_: descenso 2 (a secas), paracaídas secundario

## Simulación

**Modo**:
De dónde salen los datos del CanSat; viaja en cada paquete. Son cuatro:
FLIGHT (vuelo real, todos los sensores), SIM_PRESSURE (la presión llega desde
tierra y el resto de los sensores son reales), SIM_FULL (todos los sensores
simulados) y MANUAL (prueba de banco; el firmware de vuelo nunca lo manda). No
es el estado de la FSW: todos los modos recorren los mismos estados.
_Evitar_: estado, modo de vuelo

**Vuelo de demostración**:
Un vuelo simulado fijo, idéntico en cada corrida, con instantes con nombre
(`standby`, `descenso`, `aterrizado`) de los que salen las capturas de la PDR.
_Evitar_: escenario, demo, vuelo de prueba
