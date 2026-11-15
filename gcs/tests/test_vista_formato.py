"""La vista "sin codificar" del formato (#16) sale de los `.toml` y no los contradice.

El script vive en `protocolo/` y genera lo que muestra la PDR: las tablas de
campos y el mismo paquete en ASCII y en binario. Los largos y los tiempos en el
aire de acá están escritos a mano, desde lo acordado en la #10 y la #11.
"""

import importlib.util
from pathlib import Path

import pytest

PROTOCOLO = Path(__file__).resolve().parents[2] / "protocolo"


@pytest.fixture(scope="module")
def vista():
    spec = importlib.util.spec_from_file_location("vista_formato", PROTOCOLO / "vista_formato.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_crc16_ccitt_false_da_el_valor_de_control(vista):
    # Valor de control publicado del CRC-16/CCITT-FALSE para "123456789".
    assert vista.crc16(b"123456789") == 0x29B1


@pytest.fixture(scope="module")
def formatos(vista):
    return vista.leer_formatos()


def test_el_paquete_de_telemetria_mide_75_bytes(vista, formatos):
    telemetria, _ = formatos
    paquete = vista.codificar_telemetria(telemetria, 156, vista.EJEMPLO_TELEMETRIA)
    assert len(paquete) == 75  # versión 2, acordada en la #10


def test_la_telemetria_lleva_cabecera_ccsds_tm_version_y_crc(vista, formatos):
    telemetria, _ = formatos
    paquete = vista.codificar_telemetria(telemetria, 156, vista.EJEMPLO_TELEMETRIA)
    # Versión 0, tipo TM, sin secundaria, APID 106 | flags 11, contador 156 |
    # largo del campo de datos menos 1: 75 − 6 − 1 = 68.
    assert paquete[:6] == bytes.fromhex("006A C09C 0044")
    assert paquete[6] == 2
    assert int.from_bytes(paquete[-2:]) == vista.crc16(paquete[:-2])


def test_el_telecomando_mide_14_bytes_como_dice_su_toml(vista, formatos):
    telemetria, telecomandos = formatos
    paquete = vista.codificar_telecomando(telemetria, telecomandos, 17, "GET_BAT", None)
    assert len(paquete) == 14  # versión 1, acordada en la #11
    assert len(paquete) == telecomandos["enlace"]["largo"]


def test_el_telecomando_lleva_cabecera_tc_codigo_parametro_y_crc(vista, formatos):
    telemetria, telecomandos = formatos
    paquete = vista.codificar_telecomando(telemetria, telecomandos, 8, "SIMP", 95000)
    # Tipo TC, APID 106 | flags 11, número 8 | 14 − 6 − 1 = 7.
    assert paquete[:6] == bytes.fromhex("106A C008 0007")
    assert paquete[6] == 1  # versión de los telecomandos
    assert paquete[7] == 7  # SIMP es el octavo comando del .toml
    assert paquete[8:12] == (95000).to_bytes(4, "big")
    assert int.from_bytes(paquete[-2:]) == vista.crc16(paquete[:-2])


def test_un_parametro_con_valores_viaja_como_su_codigo(vista, formatos):
    telemetria, telecomandos = formatos
    paquete = vista.codificar_telecomando(telemetria, telecomandos, 1, "CAM1", "RESTART")
    assert paquete[8:12] == (2).to_bytes(4, "big")


def test_tiempo_en_el_aire_a_sf9_coincide_con_lo_acordado(vista):
    # SF9, BW 125 kHz, CR 4/5, preámbulo 12: las cifras de los .toml.
    assert round(vista.tiempo_en_el_aire_ms(75)) == 447
    assert round(vista.tiempo_en_el_aire_ms(14)) == 181


def test_la_linea_ascii_lleva_lo_mismo_que_el_binario(vista, formatos):
    telemetria, _ = formatos
    linea = vista.linea_telemetria(telemetria, 156, vista.EJEMPLO_TELEMETRIA)
    # Al estilo de la planilla: APID en 4 cifras, contador y los 32 campos en el
    # orden del .toml, con los decimales que da cada divisor.
    assert linea == (
        "0106,156,DESCENT_1,FLIGHT,2026-11-12T13:14:03Z,155,94532,125.4,18.70,52,"
        "7.820,0.650,3.310,0.180,5.200,0.420,-54.8012000,-67.6921000,130.5,10,"
        "0.12,-0.08,9.72,1.2,-0.8,0.1,ARMED,90,22,17,17,ACCEPTED,17,512496720"
    )


def test_sin_dato_es_na_en_la_linea_y_centinela_en_el_binario(vista, formatos):
    telemetria, _ = formatos
    valores = vista.EJEMPLO_TELEMETRIA | {"extra_id": None, "extra_valor": None}
    linea = vista.linea_telemetria(telemetria, 156, valores)
    paquete = vista.codificar_telemetria(telemetria, 156, valores)
    assert linea.endswith(",NA,NA")
    assert paquete[68:73] == bytes.fromhex("FF 80000000")  # 255 y el mínimo del int32


def test_la_linea_del_telecomando_sigue_a_la_planilla(vista, formatos):
    telemetria, telecomandos = formatos
    assert (
        vista.linea_telecomando(telemetria, telecomandos, 17, "GET_BAT", None)
        == "CMD,0106,0017,GET_BAT,NA"
    )
    assert (
        vista.linea_telecomando(telemetria, telecomandos, 8, "SIMP", 95000)
        == "CMD,0106,0008,SIMP,95000"
    )


def test_la_tabla_de_telemetria_suma_75_bytes_de_punta_a_punta(vista, formatos):
    telemetria, _ = formatos
    filas = vista.filas_telemetria(telemetria)
    assert sum(f["largo"] for f in filas) == 75
    assert filas[0]["bytes"] == "0–5"
    assert filas[-1]["bytes"] == "73–74"
    etiquetas = [f["etiqueta"] for f in filas]
    assert etiquetas[2:-1] == [c["etiqueta"] for c in telemetria["campo"]]


def test_la_tabla_de_telecomandos_suma_14_bytes(vista, formatos):
    _, telecomandos = formatos
    filas = vista.filas_telecomando(telecomandos)
    assert sum(f["largo"] for f in filas) == 14
    assert [f["bytes"] for f in filas] == ["0–5", "6", "7", "8–11", "12–13"]


def test_los_codigos_son_la_posicion_en_el_toml(vista, formatos):
    _, telecomandos = formatos
    codigos = vista.filas_codigos(telecomandos)
    assert len(codigos) == 19
    assert (codigos[0]["codigo"], codigos[0]["nombre"]) == (0, "CX")
    assert (codigos[7]["codigo"], codigos[7]["nombre"]) == (7, "SIMP")


def test_los_archivos_de_la_vista_estan_al_dia_con_los_toml(vista):
    # La diapositiva no puede diferir del código: si cambia un .toml, hay que
    # volver a correr `uv run protocolo/vista_formato.py`.
    generados = vista.generar()
    assert set(generados) == {
        "formato.md",
        "telemetria-campos.csv",
        "telecomandos-campos.csv",
        "telecomandos-codigos.csv",
        "ejemplo.csv",
    }
    for nombre, contenido in generados.items():
        en_disco = (PROTOCOLO / "vista" / nombre).read_text(encoding="utf-8")
        assert en_disco == contenido, f"{nombre} está desactualizado"
