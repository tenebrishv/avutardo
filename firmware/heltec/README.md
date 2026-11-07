# firmware/heltec

Firmware de las Heltec LoRa 32 V4 (915–928 MHz, X1).

- **A bordo:** recibe los paquetes de la Pico por UART, les suma el GPS y los transmite.
- **En tierra:** puente transparente al USB serie; le agrega a cada paquete el RSSI
  y el SNR, y muestra en el OLED el RSSI del último paquete y cuántos llegaron.

Todavía no hay código. Pendiente: un firmware para las dos, con el rol por configuración, o dos.
