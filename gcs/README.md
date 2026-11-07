# gcs — estación terrena

El flujo va en un solo sentido:

```
Fuente (serie o simulador) → Decodificador → Estado de misión → GUI
                                                   └──────────→ Registro (CSV + log crudo)
```

- **Fuente:** `QSerialPort` con la señal `readyRead`, sin hilos; o el simulador,
  un `QTimer` que arma un paquete por segundo. Las dos emiten la misma señal.
- **Decodificador:** bytes → `Muestra`. Es el único módulo que conoce el
  formato, y lo lee de `../protocolo/telemetria.toml`.
- **Estado de misión:** contadores, último valor, historial y eco de comandos.
  Python puro, sin Qt, y testeado con pytest.
- **Registro:** CSV por paquete en el disco y en el pendrive `AVUTARDO`, más un
  log crudo con cada línea tal cual llegó.

Las decisiones y sus porqués están en [`../docs/gcs-decisiones.md`](../docs/gcs-decisiones.md).
