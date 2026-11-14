---
status: accepted
---

# El eco de la telemetría hace de ACK

El CanSat no transmite un ACK aparte por cada telecomando. Cada paquete de
telemetría lleva el **eco**: el número y el código del último telecomando que
llegó, y si se aceptó o se rechazó. El eco se repite en cada paquete hasta el
telecomando siguiente. La estación terrena manda de a un telecomando por vez,
justo después de recibir un paquete; si a los 3 s no lo ve en el eco, lo
reintenta con el mismo número, y después de tres intentos lo marca sin eco. A
bordo, un telecomando con el mismo número que el último se vuelve a confirmar
sin ejecutarlo. Se decidió el 2026-11-14 (issue #11), después de la reunión
del 2026-11-13, donde se acordó que cada telecomando se confirma al llegar, no
al ejecutarse, y se reintenta si no se confirma.

## Por qué

- **Una confirmación perdida no provoca un reintento.** Un ACK aparte que se
  pierde obliga a reintentar, y el reintento hace que el CanSat reciba dos
  veces la misma orden: una altitud cero o un movimiento del servo repetidos
  en vuelo. El eco viaja en cada paquete, así que perderlo una vez no pasa de
  un segundo de demora.
- **Entra en el segundo con margen.** A SF9, con BW 125 kHz, CR 4/5 y
  preámbulo 12, el paquete de 75 B tarda 447 ms y un telecomando de 14 B,
  181 ms: quedan unos 340 ms para el USB, el puente, la notebook y la UART
  entre la Heltec y la Pico. Un ACK de 12 B sumaría otros 161 ms y dejaría
  unos 160 ms.
- **Un solo tipo de paquete baja.** Lo pide la ADR 0002, y la estación
  terrena trata cualquier otro largo como ajeno.
- **La prueba queda en el CSV.** Cada fila lleva el eco y el resultado: el
  jurado lee qué telecomando llegó, sin el log de la estación (G15).

## Opciones consideradas

- **Un ACK aparte**, `ACK,TEAM_ID,CMD_ID,RECEIVED` (la propuesta de la
  planilla de infraestructura). Confirma en unos 200 ms en lugar de menos de
  1 s, pero suma una tercera transmisión al segundo, un segundo tipo de
  paquete, y un reintento por cada ACK perdido.
- **Sólo el número en el eco, sin el código.** Ahorra 1 B que no cambia el
  tiempo en el aire, porque LoRa cuenta en bloques de símbolos, y deja el CSV
  ilegible sin el log de la estación.

## Consecuencias

- El eco guarda un solo telecomando: la estación no puede tener dos en vuelo
  al mismo tiempo. Los demás esperan en una cola.
- La Pico guarda el último número de telecomando en memoria no volátil, y la
  estación sigue su numeración desde el registro: un reinicio de cualquiera de
  los dos no repite ni reejecuta una orden.
- Un telecomando rechazado no se reintenta. Que uno aceptado hizo lo que debía
  se verifica por su efecto en la telemetría.
