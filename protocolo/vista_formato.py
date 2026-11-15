# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Vista "sin codificar" del formato, para la PDR (#16)."""

import csv
import io
import math
import tomllib
from datetime import UTC, datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent

# Bytes y signo de cada tipo del .toml.
TIPOS = {
    "uint8": (1, False),
    "int16": (2, True),
    "uint16": (2, False),
    "int32": (4, True),
    "uint32": (4, False),
}
TM, TC = 0, 1  # bit de tipo de la cabecera CCSDS

# Un paquete de ejemplo, en valores físicos y en las unidades del .toml.
# None = sin dato (va el centinela). Sigue los valores de la línea de
# ejemplo de la planilla de infraestructura; el eco y el par extra responden
# al telecomando de ejemplo (GET_BAT): extra_valor = 7820 << 16 | 5200.
EJEMPLO_TELEMETRIA = {
    "estado_fsw": "DESCENT_1",
    "modo": "FLIGHT",
    "hora": "2026-11-12T13:14:03Z",
    "tiempo_mision": 155,
    "presion": 94532,
    "altitud": 125.4,
    "temperatura": 18.70,
    "humedad": 52,
    "tension_bateria": 7.820,
    "corriente_bateria": 0.650,
    "tension_3v3": 3.310,
    "corriente_3v3": 0.180,
    "tension_panel": 5.200,
    "corriente_panel": 0.420,
    "gps_latitud": -54.8012000,
    "gps_longitud": -67.6921000,
    "gps_altitud": 130.5,
    "gps_satelites": 10,
    "acel_x": 0.12,
    "acel_y": -0.08,
    "acel_z": 9.72,
    "rot_x": 1.2,
    "rot_y": -0.8,
    "rot_z": 0.1,
    "estado_descenso2": "ARMED",
    "servo": 90,
    "potencia_tx": 22,
    "eco_id": 17,
    "eco_codigo": 17,
    "resultado_comando": "ACCEPTED",
    "extra_id": 17,
    "extra_valor": 7820 << 16 | 5200,
}


def leer_formatos() -> tuple[dict, dict]:
    """Lee `telemetria.toml` y `telecomandos.toml`."""
    with (AQUI / "telemetria.toml").open("rb") as f:
        telemetria = tomllib.load(f)
    with (AQUI / "telecomandos.toml").open("rb") as f:
        telecomandos = tomllib.load(f)
    return telemetria, telecomandos


def crc16(datos: bytes) -> int:
    """CRC-16/CCITT-FALSE: polinomio 0x1021, valor inicial 0xFFFF, sin reflejar."""
    crc = 0xFFFF
    for byte in datos:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return crc


def centinela(tipo: str) -> int:
    """Sin dato: el mínimo del tipo si es con signo, el máximo si es sin signo."""
    largo, con_signo = TIPOS[tipo]
    bits = 8 * largo
    return -(2 ** (bits - 1)) if con_signo else 2**bits - 1


def entero(campo: dict, valor) -> int:
    """El entero que viaja en el paquete por un valor físico del campo."""
    if valor is None:
        return centinela(campo["tipo"])
    if "valores" in campo:
        return campo["valores"].index(valor)
    if campo.get("mostrar") == "hora_utc":
        return int(datetime.fromisoformat(valor).timestamp())
    return round(valor * campo.get("divisor", 1))


def cabecera_ccsds(tipo: int, apid: int, contador: int, largo_paquete: int) -> bytes:
    """Cabecera primaria CCSDS 133.0-B-2: versión 0, sin secundaria, flags 11."""
    if not (0 <= apid < 2**11 and 0 <= contador < 2**14):
        raise ValueError(f"APID {apid} o contador {contador} fuera de sus 11 y 14 bits")
    identificacion = tipo << 12 | apid
    secuencia = 0b11 << 14 | contador
    largo_datos = largo_paquete - 6 - 1  # octetos del campo de datos, menos 1
    return b"".join(x.to_bytes(2) for x in (identificacion, secuencia, largo_datos))


def con_crc(sin_crc: bytes) -> bytes:
    return sin_crc + crc16(sin_crc).to_bytes(2)


def codificar_telemetria(telemetria: dict, contador: int, valores: dict) -> bytes:
    """El paquete binario, big-endian, con cabecera, versión, campos y CRC."""
    campos = b"".join(
        binario(c["tipo"], entero(c, valores[c["nombre"]])) for c in telemetria["campo"]
    )
    largo = 6 + 1 + len(campos) + 2
    cabecera = cabecera_ccsds(TM, telemetria["cabecera"]["apid"], contador, largo)
    return con_crc(cabecera + bytes([telemetria["version"]]) + campos)


def binario(tipo: str, valor: int) -> bytes:
    """El entero en big-endian, con el largo y el signo de su tipo."""
    largo, con_signo = TIPOS[tipo]
    return valor.to_bytes(largo, "big", signed=con_signo)


def comando(telecomandos: dict, nombre: str) -> tuple[int, dict]:
    """El código (la posición en el .toml, desde 0) y la definición del comando."""
    for codigo, c in enumerate(telecomandos["comando"]):
        if c["nombre"] == nombre:
            return codigo, c
    raise KeyError(nombre)


def parametro_entero(definicion: dict, parametro) -> int:
    """El int32 del parámetro: el código de un valor, un número, o 0 si no lleva."""
    if parametro is None:
        return 0
    if "valores" in definicion:
        return definicion["valores"].index(parametro)
    return parametro


def codificar_telecomando(
    telemetria: dict, telecomandos: dict, numero: int, nombre: str, parametro
) -> bytes:
    """El telecomando binario: cabecera TC, versión, código, parámetro y CRC."""
    codigo, definicion = comando(telecomandos, nombre)
    cuerpo = bytes([telecomandos["version"], codigo]) + binario(
        "int32", parametro_entero(definicion, parametro)
    )
    largo = 6 + len(cuerpo) + 2
    cabecera = cabecera_ccsds(TC, telemetria["cabecera"]["apid"], numero, largo)
    return con_crc(cabecera + cuerpo)


def tiempo_en_el_aire_ms(largo: int) -> float:
    """Tiempo en el aire LoRa (fórmula de Semtech, AN1200.13) de `largo` bytes.

    SF9, BW 125 kHz, CR 4/5, preámbulo de 12 símbolos, cabecera explícita, CRC
    de la radio activo y sin optimización de baja tasa (no hace falta a SF9).
    """
    sf, bw, cr, preambulo = 9, 125_000, 1, 12
    simbolo = 2**sf / bw
    numerador = 8 * largo - 4 * sf + 28 + 16  # + 16: CRC; cabecera explícita
    simbolos = 8 + max(math.ceil(numerador / (4 * sf)) * (cr + 4), 0)
    return 1000 * (preambulo + 4.25 + simbolos) * simbolo


def texto(campo: dict, crudo: int) -> str:
    """Cómo se lee un entero del paquete: NA, el nombre del código, la hora en
    ISO 8601 o el valor físico con los decimales que da el divisor."""
    if crudo == centinela(campo["tipo"]):
        return "NA"
    if "valores" in campo:
        valores = campo["valores"]
        return valores[crudo] if crudo < len(valores) else f"?{crudo}"
    if campo.get("mostrar") == "hora_utc":
        return datetime.fromtimestamp(crudo, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    divisor = campo.get("divisor", 1)
    decimales = len(str(divisor)) - 1  # los divisores son potencias de 10
    return f"{crudo / divisor:.{decimales}f}"


def linea_telemetria(telemetria: dict, contador: int, valores: dict) -> str:
    """El mismo paquete, sin codificar: APID, contador y los campos, en ASCII."""
    textos = [texto(c, entero(c, valores[c["nombre"]])) for c in telemetria["campo"]]
    return ",".join([f"{telemetria['cabecera']['apid']:04d}", str(contador), *textos])


def linea_telecomando(
    telemetria: dict, telecomandos: dict, numero: int, nombre: str, parametro
) -> str:
    """El mismo telecomando, sin codificar, al estilo de la planilla."""
    comando(telecomandos, nombre)  # que exista
    apid = telemetria["cabecera"]["apid"]
    param = "NA" if parametro is None else str(parametro)
    return f"CMD,{apid:04d},{numero:04d},{nombre},{param}"


# --- Tablas -------------------------------------------------------------------


def _parte(etiqueta: str, tipo: str, largo: int, requisito: str = "", unidad: str = "") -> dict:
    return dict(etiqueta=etiqueta, unidad=unidad, tipo=tipo, largo=largo, requisito=requisito)


def _numerar(partes: list[dict]) -> list[dict]:
    """Le pone a cada parte su posición en bytes, en el orden en que viajan."""
    inicio = 0
    for parte in partes:
        largo = parte["largo"]
        parte["bytes"] = str(inicio) if largo == 1 else f"{inicio}–{inicio + largo - 1}"
        inicio += largo
    return partes


def filas_telemetria(telemetria: dict) -> list[dict]:
    """El paquete de telemetría de punta a punta: cabecera, versión, campos y CRC.

    Las partes que no son campos del .toml van con la etiqueta entre paréntesis.
    """
    campos = [
        _parte(c["etiqueta"], c["tipo"], TIPOS[c["tipo"]][0], c["requisito"], c["unidad"])
        for c in telemetria["campo"]
    ]
    return _numerar(
        [
            _parte("(cabecera CCSDS)", "CCSDS", 6, "X2 F1"),
            _parte("(versión)", "uint8", 1),
            *campos,
            _parte("(CRC-16)", "uint16", 2),
        ]
    )


def filas_telecomando(telecomandos: dict) -> list[dict]:
    """El telecomando de punta a punta. Ninguna parte es un campo con etiqueta."""
    return _numerar(
        [
            _parte("(cabecera CCSDS)", "CCSDS", 6, "X2"),
            _parte("(versión)", "uint8", 1),
            _parte("(código)", "uint8", 1, "G15"),
            _parte("(parámetro)", "int32", 4),
            _parte("(CRC-16)", "uint16", 2),
        ]
    )


def _parametro(c: dict) -> str:
    if "valores" in c:
        return " / ".join(c["valores"])
    if "minimo" in c:
        return f"{c['minimo']} a {c['maximo']}"
    if "unidad" in c:
        return "entero"
    return "—"


def filas_codigos(telecomandos: dict) -> list[dict]:
    """Los comandos con su código, que es su posición en el .toml."""
    return [
        dict(
            codigo=codigo,
            nombre=c["nombre"],
            parametro=_parametro(c),
            unidad=c.get("unidad", ""),
            requisito=c["requisito"],
        )
        for codigo, c in enumerate(telecomandos["comando"])
    ]


# --- Salida -------------------------------------------------------------------

CONTADOR_EJEMPLO = 156
# El telecomando de ejemplo: el que responden el eco y el par extra de
# EJEMPLO_TELEMETRIA.
EJEMPLO_TELECOMANDO = (17, "GET_BAT", None)

COLUMNAS_PAQUETE = [
    ("bytes", "Bytes"),
    ("etiqueta", "Etiqueta"),
    ("unidad", "Unidad"),
    ("tipo", "Tipo"),
    ("largo", "Largo [B]"),
    ("requisito", "Requisito"),
]
COLUMNAS_CODIGOS = [
    ("codigo", "Código"),
    ("nombre", "Nombre"),
    ("parametro", "Parámetro"),
    ("unidad", "Unidad"),
    ("requisito", "Requisito"),
]
COLUMNAS_EJEMPLO = [
    ("paquete", "Paquete"),
    ("codificacion", "Codificación"),
    ("largo", "Largo [B]"),
    ("aire", "Tiempo en el aire [ms]"),
    ("contenido", "Contenido"),
]


def filas_ejemplo(telemetria: dict, telecomandos: dict) -> list[dict]:
    """El mismo paquete y el mismo telecomando, en ASCII y en binario (hex)."""
    tm_ascii = linea_telemetria(telemetria, CONTADOR_EJEMPLO, EJEMPLO_TELEMETRIA)
    tm_bin = codificar_telemetria(telemetria, CONTADOR_EJEMPLO, EJEMPLO_TELEMETRIA)
    tc_ascii = linea_telecomando(telemetria, telecomandos, *EJEMPLO_TELECOMANDO)
    tc_bin = codificar_telecomando(telemetria, telecomandos, *EJEMPLO_TELECOMANDO)
    filas = []
    for paquete, codificacion, datos in [
        ("telemetría", "ASCII", tm_ascii.encode("ascii")),
        ("telemetría", "binario", tm_bin),
        ("telecomando", "ASCII", tc_ascii.encode("ascii")),
        ("telecomando", "binario", tc_bin),
    ]:
        contenido = datos.decode("ascii") if codificacion == "ASCII" else datos.hex().upper()
        filas.append(
            dict(
                paquete=paquete,
                codificacion=codificacion,
                largo=len(datos),
                aire=round(tiempo_en_el_aire_ms(len(datos))),
                contenido=contenido,
            )
        )
    return filas


def _csv(columnas: list[tuple[str, str]], filas: list[dict]) -> str:
    salida = io.StringIO(newline="")
    escritor = csv.writer(salida, lineterminator="\n")
    escritor.writerow([titulo for _, titulo in columnas])
    for fila in filas:
        escritor.writerow([fila[clave] for clave, _ in columnas])
    return salida.getvalue()


def _num(valor) -> str:
    """Un entero de 4 cifras o más, agrupado de a 3 con espacio (norma SI)."""
    return f"{valor:,}".replace(",", " ") if isinstance(valor, int) else str(valor)


def _markdown(columnas: list[tuple[str, str]], filas: list[dict]) -> str:
    lineas = [
        "| " + " | ".join(titulo for _, titulo in columnas) + " |",
        "|" + "---|" * len(columnas),
    ]
    for fila in filas:
        lineas.append("| " + " | ".join(_num(fila[clave]) for clave, _ in columnas) + " |")
    return "\n".join(lineas) + "\n"


def _hex_en_renglones(hexa: str, por_renglon: int = 25) -> str:
    """El hex de a pares, `por_renglon` bytes por renglón, para que entre en una diapositiva."""
    pares = [hexa[i : i + 2] for i in range(0, len(hexa), 2)]
    return "\n".join(
        " ".join(pares[i : i + por_renglon]) for i in range(0, len(pares), por_renglon)
    )


def generar() -> dict[str, str]:
    """El contenido de cada archivo de `protocolo/vista/`, por nombre."""
    telemetria, telecomandos = leer_formatos()
    tm = filas_telemetria(telemetria)
    tc = filas_telecomando(telecomandos)
    codigos = filas_codigos(telecomandos)
    ejemplo = filas_ejemplo(telemetria, telecomandos)
    tm_ascii, tm_bin, tc_ascii, tc_bin = ejemplo

    md = f"""# El formato, sin codificar y codificado

Generado por `uv run protocolo/vista_formato.py` desde `telemetria.toml`
(versión {telemetria["version"]}) y `telecomandos.toml` (versión {telecomandos["version"]}).
No se edita a mano: si cambia un `.toml`, se vuelve a generar.

## Telemetría: un paquete de {tm_bin["largo"]} B

Big-endian, campo por campo. Los campos son enteros: valor físico = entero /
divisor. Las partes entre paréntesis no son campos del `.toml`.

{_markdown(COLUMNAS_PAQUETE, tm)}
## Telecomandos: {tc_bin["largo"]} B

{_markdown(COLUMNAS_PAQUETE, tc)}
El código del comando es su posición en `telecomandos.toml`, desde 0. El
parámetro es el código de uno de sus valores, un número en su unidad o 0.

{_markdown(COLUMNAS_CODIGOS, codigos)}
## Ejemplo: el mismo paquete, sin codificar y codificado

Sin codificar, al estilo de la planilla de infraestructura: el APID (`0106`),
el contador de secuencia y los campos en el orden del `.toml`, separados por
comas; `NA` es sin dato. Codificado, el mismo paquete en binario, con la
versión del formato y el CRC-16, que la línea ASCII no lleva. Tiempos en el
aire a SF9, BW 125 kHz, CR 4/5 y preámbulo de 12 símbolos.

{_markdown(COLUMNAS_EJEMPLO[:4], ejemplo)}
### Telemetría en ASCII ({tm_ascii["largo"]} B, {_num(tm_ascii["aire"])} ms)

```text
{tm_ascii["contenido"]}
```

### Telemetría en binario ({tm_bin["largo"]} B, {_num(tm_bin["aire"])} ms)

```text
{_hex_en_renglones(tm_bin["contenido"])}
```

### Telecomando en ASCII ({tc_ascii["largo"]} B, {_num(tc_ascii["aire"])} ms)

```text
{tc_ascii["contenido"]}
```

### Telecomando en binario ({tc_bin["largo"]} B, {_num(tc_bin["aire"])} ms)

```text
{_hex_en_renglones(tc_bin["contenido"])}
```

El eco y el par extra de la telemetría responden a este telecomando: `GET_BAT`
devuelve la tensión de la batería y la del panel en las dos mitades de
`EXTRA_VALUE`.
"""
    return {
        "formato.md": md,
        "telemetria-campos.csv": _csv(COLUMNAS_PAQUETE, tm),
        "telecomandos-campos.csv": _csv(COLUMNAS_PAQUETE, tc),
        "telecomandos-codigos.csv": _csv(COLUMNAS_CODIGOS, codigos),
        "ejemplo.csv": _csv(COLUMNAS_EJEMPLO, ejemplo),
    }


def main() -> None:
    destino = AQUI / "vista"
    destino.mkdir(exist_ok=True)
    for nombre, contenido in generar().items():
        (destino / nombre).write_text(contenido, encoding="utf-8", newline="\n")
        print(f"protocolo/vista/{nombre}")


if __name__ == "__main__":
    main()
