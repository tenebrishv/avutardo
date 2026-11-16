# firmware/heltec

Firmware de las Heltec LoRa 32 V4 (915–928 MHz, X1).

- **A bordo:** sólo módem LoRa, en la UART0 de la Pico. Transmite sin tocarlos
  los paquetes que arma la Pico y le reenvía a la Pico lo que recibe, sin
  interpretarlo ([ADR 0001](../../docs/adr/0001-la-pico-arma-el-paquete.md)).
  No conoce el formato, y el GPS va directo a la Pico. La Pico puede
  reiniciarla por GP14.
- **En tierra:** puente transparente al USB serie; le agrega a cada paquete el RSSI
  y el SNR, y muestra en el OLED el RSSI del último paquete y cuántos llegaron.

Todavía no hay código. Pendiente: un firmware para las dos, con el rol por configuración, o dos.
