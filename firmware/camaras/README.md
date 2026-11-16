# firmware/camaras

Firmware de las dos ESP32-S3-CAM N16R8 con OV5640 (cenit y nadir): el mismo
programa en las dos. Graban a la microSD cuando la Pico se lo indica, por una
UART que la Pico arma con sus PIO, una por cámara (pines en
[`../pico/README.md`](../pico/README.md#pines)). El WiFi y el Bluetooth van
apagados.

Todavía no hay código.
