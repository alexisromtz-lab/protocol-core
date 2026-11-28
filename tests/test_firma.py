"""test_firma.py — el anillo 8: quien emitio el recibo, y lo que la firma no dice.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

QUE MIDE. Que un recibo `recibo-de-composicion/2` se pueda firmar y que un
tercero lo coteje **sin ejecutar el firmador**: la firma vive en
`protocol.firma`, el cotejo se reescribe dentro de
`examples/verificar_recibo_externo.py`, y P-110a ata las dos copias a los cinco
vectores oficiales de RFC 8032 §7.1. Dos implementaciones que no se cotejan
divergen solas; el vector es lo unico que las obliga a decir lo mismo.

LA FIRMA CUBRE LO QUE NADIE MAS MIRA. Las comprobaciones del verificador
recorren los campos que conoce; el canon firmado recorre el documento entero,
incluidas las llaves que no conoce. P-110d lo mide en la direccion incomoda: un
recibo con un campo anadido cierra con RC 0 **sin** firma —ningun verificador
tiene regla para ese campo— y no cierra con ella. Esa es la capacidad nueva, y
sin ese par de casos la firma seria decoracion.

POR QUE SE FIRMA AL LADO Y NO DENTRO. Una firma incluida en el JSON que firma no
puede cubrirse a si misma, y excluirla exige una segunda regla —«todo menos esta
llave»— con su propio agujero. Separada, los bytes firmados son el recibo entero
y no hay regla de exclusion que equivocar.

LO QUE NO CIERRA (lista cerrada). Que el emisor dijera la verdad y que el nodo
intermedio aplicara la regla que declaro: la firma autentica bytes, no trabajo.
Y la custodia de la semilla: quien la tenga firma como el emisor, y eso ningun
algoritmo lo arregla.
"""

from __future__ import annotations

import hashlib as _hashlib
import importlib.util as _importlib_util
import json as _json
import os as _os
import shutil as _shutil
import subprocess as _subprocess
import sys as _sys
import tempfile as _tempfile
import unicodedata as _unicodedata
import unittest as _unittest
from typing import Dict, List, Optional, Sequence, Tuple

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_SRC = _os.path.join(_RAIZ, "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.ausencia import pagina_desde_manifiesto  # noqa: E402
from protocol.composicion import (  # noqa: E402
    Recibo,
    Tramo,
    VeredictoDeComposicion,
    a_dict,
    componer,
)
from protocol.firma import (  # noqa: E402
    DOMINIO,
    FORMATO_FIRMABLE,
    bytes_firmados,
    clave_publica,
    firmar,
    firmar_recibo,
    verificar,
    verificar_recibo,
)
from protocol.types import ContratoViolado  # noqa: E402
from protocol.ubicacion import leer_manifiesto  # noqa: E402

_V = VeredictoDeComposicion
_EXTERNO = _os.path.join(_RAIZ, "examples", "verificar_recibo_externo.py")
_FIRMADOR = _os.path.join(_RAIZ, "examples", "firmar_recibo.py")
_VECTORES = _os.path.join(_RAIZ, "tests", "fixtures", "rfc8032.json")

_SEMILLA = bytes.fromhex(
    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
)
_REGLA_AB = "regla A->B: copia la pagina sin tocar un byte\n"
_REGLA_BC = "regla B->C: reordena y anade la columna de motivo\n"


def _externo():
    """El verificador, cargado como modulo: su copia de Ed25519 y su canon."""

    especificacion = _importlib_util.spec_from_file_location("_externo_firma", _EXTERNO)
    modulo = _importlib_util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)  # type: ignore[union-attr]
    return modulo


def _pagina(prefijo: str, filas: int = 3):
    texto = "".join(
        "%s  %s\n" % (("%x" % (indice + 1)) * 64, "%s-%02d.tsv" % (prefijo, indice))
        for indice in range(filas)
    )
    return pagina_desde_manifiesto(leer_manifiesto(texto))


def _reglas() -> Tuple[str, str]:
    return _REGLA_AB, _REGLA_BC


def _recibo(con_regla: bool = True) -> Dict[str, object]:
    """Un `A -> B -> C` real: dos tramos, dos reglas declaradas fuera."""

    a, b, c = _pagina("acta"), _pagina("beta"), _pagina("gamma")
    regla_ab, regla_bc = _reglas()
    ab = Recibo(
        tramos=(
            Tramo(
                origen="A",
                destino="B",
                veredicto=_V.INTACTA,
                pagina_origen=a.filas,
                pagina_destino=b.filas,
                sha256_regla=_hashlib.sha256(regla_ab.encode()).hexdigest() if con_regla else "",
            ),
        )
    )
    bc = Recibo(
        tramos=(
            Tramo(
                origen="B",
                destino="C",
                veredicto=_V.REUBICADA,
                pagina_origen=b.filas,
                pagina_destino=c.filas,
                sha256_regla=_hashlib.sha256(regla_bc.encode()).hexdigest() if con_regla else "",
            ),
        )
    )
    return a_dict(componer(ab, bc))


def _acto(script: str, argumentos: Sequence[str], cwd: str, aislado: bool = False) -> Tuple[int, str]:
    corrida = _subprocess.run(
        [_sys.executable, "-B", script, *argumentos],
        cwd=cwd,
        env={} if aislado else None,
        stdout=_subprocess.PIPE,
        stderr=_subprocess.STDOUT,
        text=True,
    )
    return corrida.returncode, corrida.stdout


class _Base(_unittest.TestCase):
    def firmar(self, datos: Dict[str, object]) -> Tuple[str, str]:
        return firmar_recibo(datos, _SEMILLA), clave_publica(_SEMILLA).hex()

    def en_disco(
        self,
        directorio: str,
        datos: Dict[str, object],
        firmado_de: "Optional[Dict[str, object]]" = None,
    ) -> Tuple[str, str, str]:
        """Recibo, clave publica y firma escritos en `directorio`.

        `firmado_de` permite firmar **otro** recibo que el que queda en disco:
        es la unica forma de presentar una firma valida junto a un documento que
        no es el firmado, que es lo que P-110e necesita medir.
        """

        ruta = _os.path.join(directorio, "recibo.json")
        with open(ruta, "w", encoding="utf-8") as flujo:
            _json.dump(datos, flujo)
        firma, publica = self.firmar(datos if firmado_de is None else firmado_de)
        with open(_os.path.join(directorio, "R.firma"), "w", encoding="utf-8") as flujo:
            flujo.write(firma + "\n")
        with open(_os.path.join(directorio, "R.pub"), "w", encoding="utf-8") as flujo:
            flujo.write(publica + "\n")
        for indice, texto in enumerate(_reglas()):
            with open(
                _os.path.join(directorio, "regla-%d.txt" % indice), "w", encoding="utf-8"
            ) as flujo:
                flujo.write(texto)
        return ruta, publica, firma

    def aislado(self, directorio: str, *extra: str) -> Tuple[int, str]:
        """El verificador copiado fuera del arbol, bajo `env -i`."""

        copia = _os.path.join(directorio, "verificador.py")
        _shutil.copyfile(_EXTERNO, copia)
        return _acto(
            copia,
            [
                "--recibo",
                "recibo.json",
                "--regla",
                "regla-0.txt",
                "--regla",
                "regla-1.txt",
                *extra,
            ],
            directorio,
            aislado=True,
        )


class TestLaFirmaReproduceRfc8032(_Base):
    def test_p110a_las_dos_implementaciones_cotejan_los_cinco_vectores(self) -> None:
        """Si el firmador y el verificador no cotejan el mismo vector, uno miente."""

        with open(_VECTORES, encoding="utf-8") as flujo:
            vectores = _json.load(flujo)["vectores"]
        self.assertEqual(sorted(vectores), ["1", "1024", "2", "3", "SHA(abc)"])
        externo = _externo()
        for nombre, vector in sorted(vectores.items()):
            semilla = bytes.fromhex(vector["secreto"])
            publica = bytes.fromhex(vector["publica"])
            mensaje = bytes.fromhex(vector["mensaje"])
            firma = bytes.fromhex(vector["firma"])
            self.assertEqual(clave_publica(semilla), publica, nombre)
            self.assertEqual(firmar(mensaje, semilla), firma, nombre)
            self.assertTrue(verificar(mensaje, firma, publica), nombre)
            self.assertTrue(externo.verificar_firma(mensaje, firma, publica), nombre)
            if mensaje:
                mutado = mensaje[:-1] + bytes((mensaje[-1] ^ 1,))
                self.assertFalse(verificar(mutado, firma, publica), nombre)
                self.assertFalse(externo.verificar_firma(mutado, firma, publica), nombre)


class TestElCanonFirmadoEsElDelTercero(_Base):
    def test_p110b_el_dominio_y_el_canon_coinciden_con_el_verificador(self) -> None:
        """Un canon distinto por una coma invalida toda firma; se coteja, no se supone."""

        externo = _externo()
        datos = _recibo()
        self.assertEqual(datos["formato"], FORMATO_FIRMABLE)
        self.assertEqual(DOMINIO, b"recibo-de-composicion/2\n")
        self.assertEqual(externo.DOMINIO_FIRMA, DOMINIO)
        self.assertEqual(externo.FORMATO_FIRMABLE, FORMATO_FIRMABLE)
        self.assertEqual(bytes_firmados(datos), DOMINIO + externo._canonizar(datos))

        # La NFC no es cosmetica: el mismo texto en dos formas Unicode es el
        # mismo objeto para el generador y tiene que ser los mismos bytes aqui.
        compuesto = dict(datos)
        compuesto["nota"] = "cafe\u0301"
        normalizado = dict(datos)
        normalizado["nota"] = _unicodedata.normalize("NFC", "cafe\u0301")
        self.assertNotEqual(
            _json.dumps(compuesto, sort_keys=True), _json.dumps(normalizado, sort_keys=True)
        )
        self.assertEqual(bytes_firmados(compuesto), bytes_firmados(normalizado))
        for invalido in ({"x": 1.5}, {"x": [1.5]}, {"x": object()}):
            with self.assertRaises(ValueError):
                externo._canonizar(invalido)


class TestElTerceroCotejaFueraDelArbol(_Base):
    def test_p110c_un_recibo_firmado_cierra_bajo_env_i(self) -> None:
        with _tempfile.TemporaryDirectory() as directorio:
            self.en_disco(directorio, _recibo())
            codigo, salida = self.aislado(directorio, "--clave", "R.pub", "--firma", "R.firma")
        self.assertEqual(codigo, 0, salida)
        self.assertIn("firma | valida | clave", salida)
        self.assertIn("limite | la firma dice quien emitio estos bytes", salida)

    def test_p110c_sin_las_dos_banderas_no_se_coteja_nada(self) -> None:
        with _tempfile.TemporaryDirectory() as directorio:
            self.en_disco(directorio, _recibo())
            codigo, salida = self.aislado(directorio, "--clave", "R.pub")
            self.assertEqual(codigo, 2, salida)
            self.assertIn("--clave y --firma se dan juntas", salida)


class TestUnaMutacionNoCierra(_Base):
    def test_p110d_lo_que_ningun_otro_chequeo_mira_lo_mira_la_firma(self) -> None:
        """El par de casos: el campo anadido es invisible sin firma y visible con ella."""

        with _tempfile.TemporaryDirectory() as directorio:
            ruta, _, _ = self.en_disco(directorio, _recibo())
            sin_firma, salida_sin = self.aislado(directorio)
            with open(ruta, encoding="utf-8") as flujo:
                datos = _json.load(flujo)
            datos["nota_del_emisor"] = "campo que el verificador no conoce"
            with open(ruta, "w", encoding="utf-8") as flujo:
                _json.dump(datos, flujo)
            alterado, salida_alterado = self.aislado(directorio)
            con_firma, salida_con = self.aislado(
                directorio, "--clave", "R.pub", "--firma", "R.firma"
            )
        self.assertEqual(sin_firma, 0, salida_sin)
        self.assertEqual(alterado, 0, salida_alterado)
        self.assertEqual(con_firma, 1, salida_con)
        self.assertIn("firma | REFUTA", salida_con)

    def test_p110d_un_byte_en_la_firma_o_en_la_regla_no_cierra(self) -> None:
        with _tempfile.TemporaryDirectory() as directorio:
            self.en_disco(directorio, _recibo())
            firma = _os.path.join(directorio, "R.firma")
            with open(firma, encoding="utf-8") as flujo:
                crudo = flujo.read().strip()
            mutada = ("0" if crudo[0] != "0" else "1") + crudo[1:]
            with open(firma, "w", encoding="utf-8") as flujo:
                flujo.write(mutada + "\n")
            codigo_firma, salida_firma = self.aislado(
                directorio, "--clave", "R.pub", "--firma", "R.firma"
            )
            with open(firma, "w", encoding="utf-8") as flujo:
                flujo.write(crudo + "\n")
            regla = _os.path.join(directorio, "regla-1.txt")
            with open(regla, "a", encoding="utf-8") as flujo:
                flujo.write("# un byte de mas en el artefacto\n")
            codigo_regla, salida_regla = self.aislado(
                directorio, "--clave", "R.pub", "--firma", "R.firma"
            )
        self.assertEqual(codigo_firma, 1, salida_firma)
        self.assertIn("firma | REFUTA", salida_firma)
        self.assertEqual(codigo_regla, 1, salida_regla)
        self.assertIn("REGLA_NO_COINCIDE", salida_regla)


class TestSoloSeFirmaLoFirmable(_Base):
    def test_p110e_un_1_no_se_firma_ni_se_coteja_como_firmado(self) -> None:
        """Firmar un `/1` autenticaria al falsificador; se acusa en vez de firmar."""

        sin_regla = _recibo(con_regla=False)
        self.assertEqual(sin_regla["formato"], "recibo-de-composicion/1")
        with self.assertRaises(ContratoViolado):
            firmar_recibo(sin_regla, _SEMILLA)
        firma = firmar_recibo(_recibo(), _SEMILLA)
        with self.assertRaises(ContratoViolado):
            verificar_recibo(sin_regla, firma, clave_publica(_SEMILLA).hex())

        with _tempfile.TemporaryDirectory() as directorio:
            # La firma es de un `/2` valido y el documento en disco es el `/1`:
            # el par exacto que un falsificador presentaria.
            self.en_disco(directorio, sin_regla, firmado_de=_recibo())
            with open(_os.path.join(directorio, "semilla.hex"), "w", encoding="utf-8") as flujo:
                flujo.write(_SEMILLA.hex() + "\n")
            ruta = _os.path.join(directorio, "recibo.json")
            codigo_acto, salida_acto = _acto(
                _FIRMADOR,
                [
                    "--recibo",
                    ruta,
                    "--semilla",
                    "semilla.hex",
                    "--firma-salida",
                    "x.firma",
                    "--clave-salida",
                    "x.pub",
                ],
                directorio,
            )
            codigo, salida = _acto(
                _EXTERNO,
                ["--recibo", ruta, "--clave", "R.pub", "--firma", "R.firma"],
                directorio,
            )
        self.assertEqual(codigo_acto, 2, salida_acto)
        self.assertIn("solo se firma un recibo", salida_acto)
        self.assertEqual(codigo, 1, salida)
        self.assertIn("FIRMA_NO_FIRMABLE", salida)


if __name__ == "__main__":
    _unittest.main()
