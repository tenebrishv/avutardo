"""El formato de los telecomandos está bien formado y es el acordado en la #11.

Es la única fuente del formato de subida: la estación terrena arma los
telecomandos con él y la FSW los valida con él. Los estados y los modos que
nombra tienen que existir en `telemetria.toml`, porque la Pico los compara con
lo que ella misma transmite.
"""

import re
import tomllib
from pathlib import Path

import pytest

PROTOCOLO = Path(__file__).resolve().parents[2] / "protocolo"
TOML = PROTOCOLO / "telecomandos.toml"
TELEMETRIA = PROTOCOLO / "telemetria.toml"

# Partes del telecomando (big-endian), acordadas en la #11.
CABECERA_CCSDS = 6
VERSION_FORMATO = 1
CODIGO = 1
PARAMETRO = 4  # int32
CRC = 2
LARGO_TELECOMANDO = 14

CENTINELA_UINT8 = 255  # "sin dato" de eco_codigo y de extra_id
INT32 = (-(2**31), 2**31 - 1)

UNIDADES = {"", "s", "Pa", "dBm", "V"}
GRUPOS = {"comunicaciones", "hora", "calibracion", "simulacion", "descenso", "camaras",
          "consultas", "mision"}  # fmt: skip
OBLIGATORIAS = {"nombre", "grupo", "requisito", "descripcion"}
OPCIONALES = {"valores", "unidad", "minimo", "maximo", "confirmar", "solo_en_estado",
              "solo_en_modo", "respuesta"}  # fmt: skip
REQUISITO = re.compile(r"([A-Z]+[0-9]+( [A-Z]+[0-9]+)*)?")
NOMBRE = re.compile(r"[A-Z][A-Z0-9]*(_[A-Z0-9]+)*")


@pytest.fixture(scope="module")
def formato() -> dict:
    with TOML.open("rb") as f:
        return tomllib.load(f)


@pytest.fixture(scope="module")
def telemetria() -> dict:
    with TELEMETRIA.open("rb") as f:
        return tomllib.load(f)


@pytest.fixture(scope="module")
def comandos(formato: dict) -> list[dict]:
    return formato["comando"]


def valores_de(telemetria: dict, campo: str) -> list[str]:
    return next(c["valores"] for c in telemetria["campo"] if c["nombre"] == campo)


# --- El paquete ---------------------------------------------------------------


def test_version_del_formato_es_1(formato):
    assert type(formato["version"]) is int
    assert formato["version"] == 1


def test_el_telecomando_mide_14_bytes(formato):
    assert CABECERA_CCSDS + VERSION_FORMATO + CODIGO + PARAMETRO + CRC == LARGO_TELECOMANDO
    assert formato["enlace"] == {
        "codificacion": "binario",
        "crc": "CRC-16/CCITT-FALSE",
        "largo": LARGO_TELECOMANDO,
    }


def test_el_apid_vive_solo_en_telemetria(formato, telemetria):
    # Uno solo para los dos sentidos: está en telemetria.toml y no se repite acá.
    assert "cabecera" not in formato
    assert telemetria["cabecera"]["apid"] == 106


# --- Los comandos -------------------------------------------------------------

# La tabla acordada en la #11, copiada a mano. El código es la posición, desde
# 0: cambiar el orden cambia los códigos y obliga a subir la versión.
COMANDOS_V1 = [
    "CX",
    "TX_POWER",
    "TIME_SET",
    "TIME_SYNC",
    "CAL_ALT",
    "CAL_IMU",
    "SIM",
    "SIMP",
    "SERVO",
    "DESCENT2",
    "CAM1",
    "CAM2",
    "CAM_STATUS",
    "GET_SENSORS",
    "TIME_STATUS",
    "GET_P0",
    "GET_RESETS",
    "GET_BAT",
    "RESET_MISSION",
]


def test_comandos_en_el_orden_acordado(comandos):
    assert [c["nombre"] for c in comandos] == COMANDOS_V1


def test_los_que_salieron_no_estan(comandos):
    nombres = {c["nombre"] for c in comandos}
    assert not nombres & {"PING", "GET_STATUS", "GET_GPS", "CAL_ALL"}


def test_ningun_codigo_pisa_el_centinela(comandos):
    assert len(comandos) < CENTINELA_UINT8


def test_nombres_en_mayusculas(comandos):
    for c in comandos:
        assert NOMBRE.fullmatch(c["nombre"]), c["nombre"]


def test_cada_comando_tiene_lo_obligatorio_y_nada_mas(comandos):
    for c in comandos:
        assert not OBLIGATORIAS - c.keys(), f"{c['nombre']}: faltan {OBLIGATORIAS - c.keys()}"
        sobran = c.keys() - OBLIGATORIAS - OPCIONALES
        assert not sobran, f"{c['nombre']}: claves desconocidas {sobran}"


def test_grupos_conocidos(comandos):
    for c in comandos:
        assert c["grupo"] in GRUPOS, f"{c['nombre']}: {c['grupo']!r}"


def test_requisito_es_un_codigo_del_anexo(comandos):
    for c in comandos:
        assert REQUISITO.fullmatch(c["requisito"]), f"{c['nombre']}: {c['requisito']!r}"


def test_requisitos_acordados(comandos):
    requisitos = {c["nombre"]: c["requisito"] for c in comandos if c["requisito"]}
    assert requisitos == {
        "TIME_SET": "F3",
        "CAL_ALT": "G1",
        "DESCENT2": "C4",
        "CAM_STATUS": "F4",
        "GET_SENSORS": "F4",
        "TIME_STATUS": "F4",
        "GET_P0": "F4",
        "GET_RESETS": "F4",
        "GET_BAT": "X6 F4",
    }


# --- El parámetro -------------------------------------------------------------


def test_parametro_con_nombre_o_numero_nunca_los_dos(comandos):
    for c in comandos:
        if "valores" in c:
            assert not c.keys() & {"unidad", "minimo", "maximo"}, c["nombre"]


def test_parametros_con_nombre_acordados(comandos):
    # Se codifican en este orden, desde 0.
    con_valores = {c["nombre"]: c["valores"] for c in comandos if "valores" in c}
    assert con_valores == {
        "CX": ["ON", "OFF"],
        "SIM": ["OFF", "PRESSURE", "FULL"],
        "SERVO": ["MIN", "CENTER", "MAX"],
        "DESCENT2": ["ARM", "DISARM"],
        "CAM1": ["START", "STOP", "RESTART"],
        "CAM2": ["START", "STOP", "RESTART"],
    }


def test_sim_coincide_con_el_modo(comandos, telemetria):
    # SIM OFF = FLIGHT, PRESSURE = SIM_PRESSURE, FULL = SIM_FULL: el mismo código.
    sim = next(c for c in comandos if c["nombre"] == "SIM")
    modos = valores_de(telemetria, "modo")
    assert modos[: len(sim["valores"])] == ["FLIGHT", "SIM_PRESSURE", "SIM_FULL"]


def test_parametros_numericos_acordados(comandos):
    numericos = {
        c["nombre"]: (c["unidad"], c.get("minimo"), c.get("maximo"))
        for c in comandos
        if "unidad" in c
    }
    assert numericos == {
        "TX_POWER": ("dBm", 2, 28),
        "TIME_SET": ("s", None, None),
        "SIMP": ("Pa", None, None),
    }


def test_rango_entero_dentro_de_int32(comandos):
    for c in comandos:
        minimo, maximo = c.get("minimo", INT32[0]), c.get("maximo", INT32[1])
        assert type(minimo) is int and type(maximo) is int, c["nombre"]
        assert INT32[0] <= minimo <= maximo <= INT32[1], c["nombre"]
        assert c.get("unidad", "") in UNIDADES, c["nombre"]


# --- Confirmación y rechazos --------------------------------------------------


def test_confirmar_es_true_o_una_lista_de_valores(comandos):
    for c in comandos:
        if "confirmar" not in c:
            continue
        if "valores" in c:
            assert isinstance(c["confirmar"], list), c["nombre"]
            assert set(c["confirmar"]) <= set(c["valores"]), c["nombre"]
        else:
            assert c["confirmar"] is True, c["nombre"]


def test_comandos_con_confirmacion_acordados(comandos):
    confirmar = {c["nombre"]: c["confirmar"] for c in comandos if "confirmar" in c}
    assert confirmar == {
        "CX": ["OFF"],
        "CAL_ALT": True,
        "SIM": ["OFF", "PRESSURE", "FULL"],
        "DESCENT2": ["DISARM"],
        "RESET_MISSION": True,
    }


def test_estados_y_modos_existen_en_la_telemetria(comandos, telemetria):
    estados = set(valores_de(telemetria, "estado_fsw"))
    modos = set(valores_de(telemetria, "modo"))
    for c in comandos:
        assert set(c.get("solo_en_estado", [])) <= estados, c["nombre"]
        assert set(c.get("solo_en_modo", [])) <= modos, c["nombre"]


def test_rechazos_por_estado_y_modo_acordados(comandos):
    por_estado = {c["nombre"]: c["solo_en_estado"] for c in comandos if "solo_en_estado" in c}
    por_modo = {c["nombre"]: c["solo_en_modo"] for c in comandos if "solo_en_modo" in c}
    standby = ["STANDBY"]
    assert por_estado == {
        "CAL_ALT": standby,
        "CAL_IMU": standby,
        "SIM": standby,
        "SERVO": standby,
        "RESET_MISSION": standby,
    }
    assert por_modo == {"SIMP": ["SIM_PRESSURE"]}


# --- Las consultas ------------------------------------------------------------

CONSULTAS = ["CAM_STATUS", "GET_SENSORS", "TIME_STATUS", "GET_P0", "GET_RESETS", "GET_BAT"]


def test_las_consultas_no_llevan_parametro(comandos):
    for c in comandos:
        if "respuesta" in c:
            assert c["grupo"] == "consultas", c["nombre"]
            assert not c.keys() & {"valores", "unidad"}, c["nombre"]


def test_consultas_acordadas(comandos):
    assert [c["nombre"] for c in comandos if "respuesta" in c] == CONSULTAS


def test_respuestas_acordadas(comandos):
    respuestas = {c["nombre"]: c["respuesta"] for c in comandos if "respuesta" in c}
    assert respuestas == {
        "CAM_STATUS": {
            "forma": "bits",
            "bits": ["cam1_grabando", "cam1_sd_con_lugar", "cam2_grabando", "cam2_sd_con_lugar"],
        },
        "GET_SENSORS": {
            "forma": "bits",
            "bits": ["ds3231", "bme280", "ina3221", "gps_l76k", "lsm6dso32"],
        },
        "TIME_STATUS": {"forma": "valores", "valores": ["SIN_HORA", "TIME_SET", "TIME_SYNC"]},
        "GET_P0": {"forma": "entero", "unidad": "Pa"},
        "GET_RESETS": {"forma": "entero", "unidad": ""},
        "GET_BAT": {
            "forma": "mitades",
            "alto": {"nombre": "tension_bateria", "unidad": "V", "divisor": 1000},
            "bajo": {"nombre": "tension_panel", "unidad": "V", "divisor": 1000},
        },
    }


def test_los_bits_entran_en_int32(comandos):
    for c in comandos:
        if c.get("respuesta", {}).get("forma") == "bits":
            assert len(c["respuesta"]["bits"]) <= 31, c["nombre"]


# --- El par extra de la telemetría --------------------------------------------


def test_el_par_extra_ya_no_es_reservado(telemetria):
    campos = {c["nombre"]: c for c in telemetria["campo"]}
    for nombre in ("extra_id", "extra_valor"):
        assert "reservado" not in campos[nombre], nombre
        assert "#11" not in campos[nombre]["descripcion"], nombre
    assert "#11" not in campos["eco_codigo"]["descripcion"]
