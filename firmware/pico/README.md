# firmware/pico

Software de vuelo de la Raspberry Pi Pico 2: el núcleo del CanSat.
Lee los sensores y el GPS, maneja las cámaras y el servo del segundo descenso,
arma los paquetes de telemetría y se los pasa a la Heltec por UART
([ADR 0001](../../docs/adr/0001-la-pico-arma-el-paquete.md)).

Todavía no hay código. El formato de los paquetes sale de `../../protocolo/telemetria.toml`.

## Pines

Asignación del pinout del equipo (2026-11-13). Todo va a la barra de 3.3 V.

| GPIO | Pin | Función | Dispositivo | Uso |
|---|---|---|---|---|
| GP0 | 1 | UART0 TX | Heltec LoRa 32 V4 (GPIO44, U0RXD) | Paquetes hacia la radio |
| GP1 | 2 | UART0 RX | Heltec LoRa 32 V4 (GPIO43, U0TXD) | Lo que llega por radio |
| GP4 | 6 | I2C0 SDA | INA3221 y LSM6DSO32 | Datos del I2C0 |
| GP5 | 7 | I2C0 SCL | INA3221 y LSM6DSO32 | Reloj del I2C0 |
| GP8 | 11 | UART1 TX | GPS L76K (RX) | Comandos al GPS |
| GP9 | 12 | UART1 RX | GPS L76K (TX) | NMEA del GPS |
| GP10 | 14 | Entrada | INA3221 (WAR) | Alerta de advertencia |
| GP11 | 15 | Entrada | INA3221 (CRI) | Alerta crítica |
| GP12 | 16 | Salida | GPS L76K (RST) | Reinicio del GPS |
| GP13 | 17 | Salida | GPS L76K (WAKEUP) | Reposo del GPS |
| GP14 | 19 | Salida | Heltec LoRa 32 V4 (RST) | Reinicio de la Heltec |
| GP16 | 21 | Interrupción | LSM6DSO32 (INT2) | FIFO del IMU al umbral |
| GP17 | 22 | Interrupción | LSM6DSO32 (INT1) | Dato nuevo del IMU |
| GP18 | 24 | I2C1 SDA | BME280 y DS3231 | Datos del I2C1 |
| GP19 | 25 | I2C1 SCL | BME280 y DS3231 | Reloj del I2C1 |
| GP20 | 26 | Interrupción | DS3231 (SQW) | Pulso de 1 Hz |
| GP21 | 27 | UART por PIO, RX | Cámara 1 (TX) | Respuestas de la cámara 1 |
| GP22 | 29 | UART por PIO, TX | Cámara 1 (RX) | Órdenes a la cámara 1 |
| GP26 | 31 | UART por PIO, TX | Cámara 2 (RX) | Órdenes a la cámara 2 |
| GP27 | 32 | UART por PIO, RX | Cámara 2 (TX) | Respuestas de la cámara 2 |

Libres: GP2, GP3, GP6, GP7, GP15 y GP28 (ADC2). Pendiente (#49): el PWM del
servo SG92R del segundo descenso, propuesto en GP3, y qué pines de la
ESP32-S3-CAM usa la UART de cada cámara.
