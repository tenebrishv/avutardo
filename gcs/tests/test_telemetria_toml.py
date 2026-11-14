"""El formato de telemetría está bien formado.

Es la única fuente del formato: si tiene un nombre repetido, un tipo
desconocido o una unidad que no es SI, todo lo que lo lee falla después.
"""

import re
import tomllib
from pathlib import Path

import pytest

TOML = Path(__file__).resolve().parents[2] / "protocolo" / "telemetria.toml"

# Bytes que ocupa cada tipo en el paquete (big-endian, campo por campo).
TAMANIO = {"uint8": 1, "int16": 2, "uint16": 2, "int32": 4, "uint32": 4}
TIPOS = set(TAMANIO)

# Partes fijas del paquete, fuera de los campos.
CABECERA_CCSDS = 6  # cabecera primaria CCSDS 133.0-B-2, sin secundaria
VERSION_FORMATO = 1
CRC = 2  # CRC-16/CCITT-FALSE
LARGO_PAQUETE = 75  # versión 2, acordada en la #10
# Unidades SI y las aceptadas para uso con el SI (°, °C). Vacía = sin unidad.
UNIDADES = {"", "s", "m", "Pa", "°C", "%", "V", "A", "W", "m/s", "m/s²", "°", "°/s", "dB", "dBm"}

OBLIGATORIAS = {"nombre", "etiqueta", "tipo", "unidad", "requisito", "descripcion"}
OPCIONALES = {"divisor", "valores", "mostrar", "reservado"}
# Un código del Anexo A v2: letras y número (G3, X5, SN1); varios, separados por
# espacio. Vacío: el anexo no lo pide y lo eligió el equipo.
REQUISITO = re.compile(r"([A-Z]+[0-9]+( [A-Z]+[0-9]+)*)?")
# La etiqueta es el nombre en inglés de la planilla de infraestructura: lo usan
# el encabezado del CSV (BAT_VOLTAGE [V]) y la pantalla.
ETIQUETA = re.compile(r"[A-Z][A-Z0-9]*(_[A-Z0-9]+)*")


@pytest.fixture(scope="module")
def formato() -> dict:
    with TOML.open("rb") as f:
        return tomllib.load(f)


@pytest.fixture(scope="module")
def campos(formato: dict) -> list[dict]:
    return formato["campo"]


def test_tiene_campos(campos):
    assert len(campos) > 0


def test_nombres_unicos(campos):
    nombres = [c["nombre"] for c in campos]
    repetidos = {n for n in nombres if nombres.count(n) > 1}
    assert not repetidos, f"nombres repetidos: {repetidos}"


def test_nombres_son_identificadores(campos):
    for c in campos:
        assert c["nombre"].isidentifier(), c["nombre"]


def test_cada_campo_tiene_lo_obligatorio(campos):
    for c in campos:
        faltan = OBLIGATORIAS - c.keys()
        assert not faltan, f"{c.get('nombre')}: faltan {faltan}"


def test_etiquetas_unicas_y_en_mayusculas(campos):
    etiquetas = [c["etiqueta"] for c in campos]
    repetidas = {e for e in etiquetas if etiquetas.count(e) > 1}
    assert not repetidas, f"etiquetas repetidas: {repetidas}"
    for c in campos:
        assert ETIQUETA.fullmatch(c["etiqueta"]), f"{c['nombre']}: {c['etiqueta']!r}"


def test_tipos_conocidos(campos):
    for c in campos:
        assert c["tipo"] in TIPOS, f"{c['nombre']}: tipo {c['tipo']!r}"


def test_unidades_si(campos):
    for c in campos:
        assert c["unidad"] in UNIDADES, f"{c['nombre']}: unidad {c['unidad']!r}"


def test_el_paquete_mide_75_bytes(campos):
    largo = CABECERA_CCSDS + VERSION_FORMATO + sum(TAMANIO[c["tipo"]] for c in campos) + CRC
    assert largo == LARGO_PAQUETE


# La tabla de la versión 2, acordada en la #10, copiada a mano:
# (nombre, etiqueta, tipo, divisor). Cambiar el formato obliga a cambiar esta
# tabla (y a subir la versión).
FORMATO_V2 = [
    ("estado_fsw", "STATE", "uint8", 1),
    ("modo", "MODE", "uint8", 1),
    ("hora", "RTC_DATETIME", "uint32", 1),
    ("tiempo_mision", "MISSION_TIME", "uint16", 1),
    ("presion", "PRESSURE", "uint32", 1),
    ("altitud", "ALT_BARO", "int16", 10),
    ("temperatura", "TEMPERATURE", "int16", 100),
    ("humedad", "HUMIDITY", "uint8", 1),
    ("tension_bateria", "BAT_VOLTAGE", "uint16", 1000),
    ("corriente_bateria", "BAT_CURRENT", "int16", 1000),
    ("tension_3v3", "BUS33_VOLTAGE", "uint16", 1000),
    ("corriente_3v3", "BUS33_CURRENT", "int16", 1000),
    ("tension_panel", "SOLAR_VOLTAGE", "uint16", 1000),
    ("corriente_panel", "SOLAR_CURRENT", "int16", 1000),
    ("gps_latitud", "GPS_LATITUDE", "int32", 10_000_000),
    ("gps_longitud", "GPS_LONGITUDE", "int32", 10_000_000),
    ("gps_altitud", "GPS_ALTITUDE", "int32", 10),
    ("gps_satelites", "GPS_SATS", "uint8", 1),
    ("acel_x", "ACCEL_X", "int16", 100),
    ("acel_y", "ACCEL_Y", "int16", 100),
    ("acel_z", "ACCEL_Z", "int16", 100),
    ("rot_x", "GYRO_X", "int16", 10),
    ("rot_y", "GYRO_Y", "int16", 10),
    ("rot_z", "GYRO_Z", "int16", 10),
    ("estado_descenso2", "DESCENT2_STATUS", "uint8", 1),
    ("servo", "SERVO_CMD", "uint8", 1),
    ("potencia_tx", "TX_POWER", "uint8", 1),
    ("eco_id", "CMD_ECHO_ID", "uint16", 1),
    ("eco_codigo", "CMD_ECHO", "uint8", 1),
    ("resultado_comando", "CMD_RESULT", "uint8", 1),
    ("extra_id", "EXTRA_ID", "uint8", 1),
    ("extra_valor", "EXTRA_VALUE", "int32", 1),
]


def test_campos_en_el_orden_y_con_el_tipo_acordados(campos):
    leidos = [(c["nombre"], c["etiqueta"], c["tipo"], c.get("divisor", 1)) for c in campos]
    assert leidos == FORMATO_V2


def test_sin_claves_desconocidas(campos):
    for c in campos:
        sobran = c.keys() - OBLIGATORIAS - OPCIONALES
        assert not sobran, f"{c['nombre']}: claves desconocidas {sobran}"


def test_divisor_entero_positivo(campos):
    for c in campos:
        divisor = c.get("divisor", 1)
        assert type(divisor) is int and divisor >= 1, f"{c['nombre']}: divisor {divisor!r}"


def test_requisito_es_un_codigo_del_anexo(campos):
    for c in campos:
        assert REQUISITO.fullmatch(c["requisito"]), f"{c['nombre']}: {c['requisito']!r}"


def test_valores_solo_en_uint8_sin_pisar_el_centinela(campos):
    for c in campos:
        if "valores" in c:
            assert c["tipo"] == "uint8", c["nombre"]
            # 255 es "sin dato": no puede ser el código de un valor.
            assert 0 < len(c["valores"]) < 255, c["nombre"]
            assert all(isinstance(v, str) and v for v in c["valores"]), c["nombre"]


def test_mostrar_hora_utc_solo_en_uint32_en_segundos(campos):
    for c in campos:
        if "mostrar" in c:
            assert c["mostrar"] == "hora_utc", c["nombre"]
            assert c["tipo"] == "uint32" and c["unidad"] == "s", c["nombre"]


def test_reservado_es_booleano(campos):
    for c in campos:
        if "reservado" in c:
            assert c["reservado"] is True, c["nombre"]


def test_valores_acordados(campos):
    con_valores = {c["nombre"]: c["valores"] for c in campos if "valores" in c}
    assert con_valores == {
        "estado_fsw": ["BOOT", "STANDBY", "ASCENT", "DESCENT_1", "DESCENT_2", "LANDED"],
        "modo": ["FLIGHT", "SIM_PRESSURE", "SIM_FULL", "MANUAL"],
        "estado_descenso2": ["NOT_ARMED", "ARMED", "TRIGGERED"],
        "resultado_comando": ["ACCEPTED", "REJECTED"],
    }


def test_mostrar_acordado(campos):
    con_mostrar = {c["nombre"]: c["mostrar"] for c in campos if "mostrar" in c}
    assert con_mostrar == {"hora": "hora_utc"}


def test_reservados_acordados(campos):
    # El par extra lo define la #11: hasta entonces no se muestra ni va al CSV.
    reservados = [c["nombre"] for c in campos if c.get("reservado")]
    assert reservados == ["extra_id", "extra_valor"]


def test_requisitos_acordados(campos):
    requisitos = {c["nombre"]: c["requisito"] for c in campos}
    assert requisitos["modo"] == ""
    assert requisitos["humedad"] == ""
    assert requisitos["tension_3v3"] == requisitos["corriente_3v3"] == ""
    assert requisitos["potencia_tx"] == ""
    assert requisitos["estado_descenso2"] == requisitos["servo"] == "C4"
    assert requisitos["tension_panel"] == requisitos["corriente_panel"] == "X6"
    assert requisitos["eco_id"] == requisitos["eco_codigo"] == "G15"
    assert requisitos["resultado_comando"] == "G15"
    assert requisitos["extra_id"] == requisitos["extra_valor"] == "F4"


def test_version_del_formato_es_2(formato):
    assert type(formato["version"]) is int
    assert formato["version"] == 2


def test_ya_no_es_provisorio(formato):
    assert "provisorio" not in formato
    assert "paquete" not in formato  # la sección del formato ASCII viejo


def test_enlace(formato):
    assert formato["enlace"] == {
        "codificacion": "binario",
        "crc": "CRC-16/CCITT-FALSE",
        "linea_puente": "<hex>,<rssi>,<snr>\n",
    }


def test_apid_106_en_11_bits(formato):
    apid = formato["cabecera"]["apid"]
    assert apid == 106
    assert 0 <= apid < 0x7FF  # 0x7FF es el APID de relleno (idle) de CCSDS


# "Sin dato": el mínimo del tipo si es con signo, el máximo si es sin signo.
# Escrito a mano; el decodificador tiene que dar lo mismo.
CENTINELA = {
    "uint8": 255,
    "int16": -32_768,
    "uint16": 65_535,
    "int32": -2_147_483_648,
    "uint32": 4_294_967_295,
}


def test_cada_tipo_tiene_centinela(campos):
    assert CENTINELA.keys() == TAMANIO.keys()
    for c in campos:
        assert c["tipo"] in CENTINELA, c["nombre"]


def test_el_centinela_es_el_extremo_del_tipo():
    for tipo, centinela in CENTINELA.items():
        bits = 8 * TAMANIO[tipo]
        if tipo.startswith("u"):
            assert centinela == 2**bits - 1, tipo
        else:
            assert centinela == -(2 ** (bits - 1)), tipo
