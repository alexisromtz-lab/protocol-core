"""test_portador.py — el anillo 5: el portador, que es lo unico que trae el cliente.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

QUE MIDE. Que el archivo que un tercero publica se lea **tal como lo escribio**.
Hasta el anillo 4 el protocolo sabia leer un manifiesto canonico (`hash` + dos
espacios + ruta) y llamaba «sin dos columnas» a todo lo demas. Medido el
2026-11-25 sobre cinco portadores reales: uno se leia, tres se rechazaban y uno
—una seccion `deb822` del `Release` de Debian— se leia **mal**, acusando de
alterado un archivo intacto. Un instrumento que confunde su propio dialecto con
la mentira del sujeto no mide: opina.

LAS CUATRO GRAMATICAS SON DISJUNTAS POR CONSTRUCCION. No hay una lista de
prioridades: hay cuatro patrones que no pueden encajar a la vez, porque
`coreutils` exige el separador en la columna 65 sin espacio delante, `deb822`
exige el espacio delante, `bsd` exige parentesis y `suelto` exige que la linea
entera sea el digest. Por eso `detectar` es una funcion y no una eleccion
(P-86): un archivo con dos lecturas posibles no se lee, se publica (P-87).

LOS BYTES SON LOS DEL TERCERO. `examples/portadores/` guarda los artefactos
reales con su `FUENTES.txt` —url, instante de descarga, bytes y sha256 del
artefacto completo—, de modo que la tabla de P-85 se pueda volver a medir sin
red. El `Release` de Debian entra completo (149 266 B) porque su ambiguedad y la
de un extracto suyo son **opuestas**, y esa oposicion es el hallazgo.

LO QUE ESTE ARCHIVO ANADE A LA TESIS. Cuando el portador ya es canonico el
digest del lector coincide con el `sha256` del archivo (P-85b): el lector no
anade nada suyo, y cuando anade algo lo publica. Un archivo que se lee distinto
segun quien lo lea no es un sujeto, es un acuerdo.

P-85 .. P-90 y P-92 son de este modulo. P-91 es del verificador externo:
`examples/verificar_recibo_externo.py` reimplementa las cuatro gramaticas sin
importar `protocol` y tiene que coincidir con este archivo sobre los mismos
artefactos.

NO CUBIERTO (lista cerrada): que la firma PGP del `CHECKSUM` de Fedora sea
autentica —se salta la envoltura y se publica `firma no verificada`, porque lo
que se atestigua es la linea, no el autor—; la convencion de escape de
`coreutils` (`\\ruta`), que este lector no admite y por tanto rechaza; y el SRI
en base64, que `ubicacion._dialecto` ya nombra y tambien rechaza.
"""

from __future__ import annotations

import os as _os
import re as _re
import sys as _sys
import unittest as _unittest
from typing import Dict, Tuple

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_SRC = _os.path.join(_RAIZ, "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.portador import (  # noqa: E402
    FORMATO_CANONICO,
    GRAMATICAS,
    Lectura,
    PortadorDesconocido,
    PortadorIncompleto,
    RecorteAmbiguo,
    detectar,
    dialecto_ajeno,
    facultades,
    leer,
    leer_sin_declarar,
    recortes,
)

_PORTADORES = _os.path.join(_RAIZ, "examples", "portadores")

#: Lo medido el 2026-11-25 recorriendo los artefactos completos. Cada fila es
#: (archivo, nombre del portador suelto, gramatica, filas, digest canonico d12).
_MEDIDO: Tuple[Tuple[str, str, str, int, str], ...] = (
    ("jq-1.7.1-sha256sum.txt", "", "coreutils", 26, "f1f692fe9f92"),
    ("node-v22.11.0-SHASUMS256.txt", "", "coreutils", 41, "23aaeb143953"),
    ("gh-2.62.0-checksums.txt", "", "coreutils", 20, "89dc6f5225aa"),
    ("fedora-41-CHECKSUM", "", "bsd", 1, "9bc34ed33916"),
    ("debian-12.15-Release", "", "deb822", 772, "c0dc59762595"),
    ("go-1.23.3.sha256", "go1.23.3.darwin-arm64.tar.gz", "suelto", 1, "750c7c9f7606"),
)

#: El `sha256` del archivo `jq-1.7.1-sha256sum.txt`, que ya viene canonico.
_SHA256_DE_JQ = "f1f692fe9f923a4f5c6741729fb5931212ebccfff976225feb7a2ccec8635da4"

_H = "a" * 64
_G = "b" * 64


def _texto(archivo: str) -> str:
    with open(_os.path.join(_PORTADORES, archivo), "rb") as mango:
        return mango.read().decode("utf-8")


def _par(ruta: str, digest: str) -> str:
    return "%s  %s\n" % (digest, ruta)


class TestLosArtefactosReales(_unittest.TestCase):
    def test_p85a_cada_artefacto_real_se_lee_con_su_unica_gramatica(self) -> None:
        """Una tabla medida, no una opinion: cuatro gramaticas, seis archivos, cero rechazos."""

        for archivo, nombre, portador, filas, digest in _MEDIDO:
            with self.subTest(archivo=archivo):
                lectura = leer_sin_declarar(_texto(archivo), nombre or None)
                self.assertEqual(lectura.portador, portador)
                self.assertEqual(len(lectura.pares), filas)
                self.assertEqual(lectura.digest()[:12], digest)

    def test_p85b_cuando_el_portador_ya_es_canonico_el_lector_no_anade_nada(self) -> None:
        """El control contra el que se mide todo lo demas: digest canonico == sha256 del archivo.

        `sha256sum.txt` de jq 1.7.1 ya viene ordenado y con dos espacios. Si el
        lector devolviera otra cosa sobre el portador canonico, el anadido seria
        suyo, y entonces el digest no certificaria el archivo sino al lector.
        """

        lectura = leer_sin_declarar(_texto("jq-1.7.1-sha256sum.txt"))
        self.assertEqual(lectura.digest(), _SHA256_DE_JQ)
        self.assertEqual((lectura.prefijadas, lectura.crlf), (0, 0))

    def test_p85c_un_portador_desordenado_publica_que_reordeno(self) -> None:
        """Node no publica su `SHASUMS256.txt` ordenado: el recibo lo dice y cambia el digest."""

        lectura = leer_sin_declarar(_texto("node-v22.11.0-SHASUMS256.txt"))
        self.assertNotEqual(
            lectura.digest(),
            "dddf2b497e71a131348716f78662c9fd51b9a30f808d5c5b81e7f3c7824a83fb",
        )
        self.assertTrue(any("reordenado" in linea for linea in lectura.lineas()))

    def test_p85d_el_archivo_sin_salto_final_se_lee(self) -> None:
        """64 caracteres y ni un `\\n`: el portador suelto no termina en salto por definicion."""

        self.assertFalse(_texto("go-1.23.3.sha256").endswith("\n"))
        self.assertEqual(detectar(_H, "x.sha256"), "suelto")


class TestUnaGramaticaNoSeElige(_unittest.TestCase):
    def test_p86a_ningun_artefacto_real_tiene_dos_lecturas(self) -> None:
        """La disyuncion es del diseno, no de una lista de prioridades que alguien reordena."""

        for archivo, nombre, portador, _, _ in _MEDIDO:
            with self.subTest(archivo=archivo):
                self.assertEqual(facultades(_texto(archivo), nombre or None), (portador,))

    def test_p86b_el_marcador_binario_de_coreutils_es_una_columna_valida(self) -> None:
        """`sha256sum -b` escribe un asterisco donde `-t` escribe un espacio. Son la misma familia."""

        binario = _H + " *gh_2.62.0_linux_386.deb\n"
        self.assertEqual(facultades(binario), ("coreutils",))
        self.assertEqual(leer(binario, "coreutils").pares, (("gh_2.62.0_linux_386.deb", _H),))

    def test_p86c_el_rechazo_nombra_la_linea_y_el_dialecto_ajeno(self) -> None:
        """Un rechazo sin linea no se puede arreglar; uno que nombra el dialecto se puede declarar."""

        ajenos = {
            "sha256-47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=": "SRI base64",
            "SHA256 (ruta) = aabb": "BSD",
            _H + " una-sola-separacion.txt": "un solo espacio",
            "SHA512:": "seccion de otro algoritmo",
            "d41d8cd98f00b204e9800998ecf8427e  md5.txt": "md5sum",
        }
        for linea, esperado in ajenos.items():
            with self.subTest(linea=linea[:24]):
                self.assertIn(esperado, dialecto_ajeno(linea))
                with self.assertRaises(PortadorDesconocido) as atrapado:
                    detectar(linea + "\n")
                self.assertEqual(atrapado.exception.linea, 1)
                self.assertIn(esperado, atrapado.exception.dialecto)

    def test_p86d_declarar_un_portador_que_no_encaja_se_rechaza_en_la_primera_linea(self) -> None:
        """Declarar no adivina: si el archivo no es de esa gramatica, se dice donde deja de serlo.

        En el `Release` completo la primera linea ya no es `coreutils` (`Origin: Debian`,
        linea 1), y el rechazo nombra el portador que si lo explica — sin adoptarlo.
        """

        with self.assertRaises(PortadorDesconocido) as atrapado:
            leer(_texto("debian-12.15-Release"), "coreutils")
        self.assertEqual(atrapado.exception.linea, 1)
        self.assertIn("deb822", atrapado.exception.dialecto)


class TestElRecorteEsElTestigo(_unittest.TestCase):
    def test_p87a_el_extracto_alineado_abre_una_segunda_lectura(self) -> None:
        """Mismo archivo, dos digests: el extracto no es «el mismo» archivo, y se ve.

        Sobre estas 12 filas todos los tamanos traen relleno, asi que quitar el
        espacio inicial las convierte en columnas validas de `coreutils` cuyas
        rutas empiezan por el tamano.
        """

        extracto = _texto("debian-12.15-Release-seccion-sha256.txt")
        self.assertEqual(facultades(extracto), ("deb822",))
        propia = leer(extracto, "deb822")
        alternativas = recortes(extracto)
        self.assertEqual(len(alternativas), 1)
        self.assertEqual(alternativas[0].portador, "coreutils")
        self.assertTrue(alternativas[0].recorte)
        self.assertNotEqual(propia.digest(), alternativas[0].digest())
        self.assertTrue(alternativas[0].pares[0][0].strip()[0].isdigit())
        self.assertEqual(propia.pares[0][0], "contrib/Contents-all")

    def test_p87b_el_archivo_completo_no_es_ambiguo(self) -> None:
        """El contraste que hace del recorte un testigo: el completo, con 772 filas, no se recorta.

        58 de sus 772 filas escriben un tamano de 8 digitos y dejan una sola
        separacion: el archivo se sostiene por el 7,5 % de sus filas.
        """

        completo = _texto("debian-12.15-Release")
        self.assertEqual(facultades(completo), ("deb822",))
        self.assertEqual(recortes(completo), ())
        una_sola = [
            linea for linea in completo.split("\n") if _re.match(r"^ [0-9a-f]{64} [0-9]", linea)
        ]
        self.assertEqual(len(una_sola), 58)

    def test_p87c_sin_declarar_no_se_elige_entre_dos_lecturas(self) -> None:
        """Elegir en silencio es publicar una lectura como si fuera el archivo."""

        with self.assertRaises(RecorteAmbiguo) as atrapado:
            leer_sin_declarar(_texto("debian-12.15-Release-seccion-sha256.txt"))
        lecturas = atrapado.exception.lecturas
        self.assertEqual(len(lecturas), 2)
        self.assertEqual({una.portador for una in lecturas}, {"deb822", "coreutils"})
        self.assertEqual(len({una.digest() for una in lecturas}), 2)


class TestInvarianciaDelPortador(_unittest.TestCase):
    def test_p88_los_mismos_pares_en_cuatro_portadores_dan_el_mismo_digest(self) -> None:
        """El veredicto no puede depender de como el tercero escribio su archivo."""

        pares: Dict[str, str] = {"ruta/a.tsv": "1" * 64, "ruta/b.tsv": "2" * 64}
        textos = {
            "coreutils": "".join(_par(ruta, dig) for ruta, dig in pares.items()),
            "bsd": "".join("SHA256 (%s) = %s\n" % (ruta, dig) for ruta, dig in pares.items()),
            "deb822": "SHA256:\n"
            + "".join(" %s  %7d %s\n" % (dig, 1, ruta) for ruta, dig in pares.items()),
        }
        digests = {uno: leer(texto, uno).digest() for uno, texto in textos.items()}
        self.assertEqual(set(digests.values()), {digests["coreutils"]})
        # `suelto` no escribe el nombre: con una sola fila el par es el mismo y el digest tambien.
        suelto = leer("1" * 64 + "\n", "suelto", "ruta/a.tsv").digest()
        self.assertEqual(suelto, leer(_par("ruta/a.tsv", "1" * 64), "coreutils").digest())
        self.assertEqual(
            textos["coreutils"],
            "".join(FORMATO_CANONICO % (dig, ruta) for ruta, dig in pares.items()),
        )

    def test_p88b_el_orden_del_portador_no_es_el_orden_del_digest(self) -> None:
        """Dos archivos con las mismas filas en distinto orden: un digest, y se declara cual."""

        uno = _par("a.tsv", _H) + _par("b.tsv", _G)
        otro = _par("b.tsv", _G) + _par("a.tsv", _H)
        primera, segunda = leer_sin_declarar(uno), leer_sin_declarar(otro)
        self.assertEqual(primera.digest(), segunda.digest())
        self.assertEqual(primera.canonicos(), segunda.canonicos())
        self.assertNotEqual(primera.pares, segunda.pares)
        self.assertTrue(any("canonico" in linea for linea in primera.lineas()))
        self.assertTrue(any("reordenado" in linea for linea in segunda.lineas()))


class TestLoQueElPortadorNoEscribe(_unittest.TestCase):
    def test_p89_el_portador_suelto_sin_nombre_esta_incompleto_y_no_adivina(self) -> None:
        """`go.dev` publica 64 caracteres y ni una ruta: el nombre lo pone quien descarga."""

        texto = _texto("go-1.23.3.sha256")
        with self.assertRaises(PortadorIncompleto) as atrapado:
            detectar(texto)
        self.assertIn("nombre", str(atrapado.exception))
        lectura = leer(texto, "suelto", "go1.23.3.darwin-arm64.tar.gz")
        self.assertEqual(lectura.pares, (("go1.23.3.darwin-arm64.tar.gz", texto.strip()),))

    def test_p89b_dos_digests_en_un_portador_suelto_se_rechazan(self) -> None:
        """Un archivo suelto con dos hashes no tiene dos rutas: no es un manifiesto."""

        with self.assertRaises(PortadorDesconocido):
            leer(_H + "\n" + _G + "\n", "suelto", "x")


class TestLaEnvolturaNoEsElContenido(_unittest.TestCase):
    def test_p90a_la_firma_pgp_se_salta_y_se_declara_no_verificada(self) -> None:
        """Se atestigua la linea, no el autor: decir lo contrario seria otro veredicto."""

        lectura = leer_sin_declarar(_texto("fedora-41-CHECKSUM"))
        self.assertEqual(lectura.portador, "bsd")
        self.assertEqual(lectura.envoltura, "pgp")
        self.assertEqual(len(lectura.pares), 1)
        self.assertTrue(any("firma no verificada" in linea for linea in lectura.lineas()))

    def test_p90b_el_release_encadena_secciones_y_la_cabecera_se_encuentra(self) -> None:
        """`MD5Sum:`, `SHA1:` y `SHA256:` van sin linea en blanco entre ellos.

        Si la cabecera solo se buscara fuera de una seccion, el `SHA256:` de la
        linea 786 quedaria dentro del cuerpo de `MD5Sum:` y el archivo saldria
        con cero filas: un archivo entero leido como vacio.
        """

        completo = _texto("debian-12.15-Release")
        self.assertIn("\nSHA256:\n", completo)
        self.assertEqual(completo.count("\nMD5Sum:\n"), 1)
        lectura = leer_sin_declarar(completo)
        self.assertEqual(lectura.envoltura, "seccion SHA256")
        self.assertEqual(len(lectura.pares), 772)
        self.assertGreaterEqual(lectura.ignoradas, 13)
        self.assertEqual(lectura.pares[0][0], "contrib/Contents-all")


class TestNormalizacionesContadas(_unittest.TestCase):
    def test_p92_el_prefijo_y_el_fin_de_linea_se_cuentan_y_no_cambian_el_digest(self) -> None:
        """Un archivo con CRLF y `./` es el mismo archivo: se publica la normalizacion."""

        limpio = _par("ruta/a.tsv", _H) + _par("ruta/b.tsv", _G)
        crudo = _par("./ruta/a.tsv", _H).replace("\n", "\r\n") + _par(
            "./ruta/b.tsv", _G
        ).replace("\n", "\r\n")
        uno, otro = leer_sin_declarar(limpio), leer_sin_declarar(crudo)
        self.assertEqual(uno.digest(), otro.digest())
        self.assertEqual((otro.prefijadas, otro.crlf), (2, 2))
        self.assertTrue(any("2 prefijos ./" in linea for linea in otro.lineas()))
        self.assertTrue(any("2 fines de linea CR" in linea for linea in otro.lineas()))

    def test_p92b_una_lectura_sin_filas_no_es_una_lectura(self) -> None:
        """Cero filas no es un archivo de cero rutas: es un rechazo, y el tipo lo prohibe."""

        with self.assertRaises(ValueError):
            Lectura(portador="coreutils", pares=(), envoltura="", comentarios=0, ignoradas=0)
        self.assertEqual(GRAMATICAS, ("coreutils", "bsd", "deb822", "suelto"))


class TestElTerceroNoImportaElModulo(_unittest.TestCase):
    """P-91: el verificador externo reescribe las gramaticas y tiene que coincidir.

    Dos modulos que importan el mismo patron coinciden por construccion; la
    coincidencia solo mide si cada uno llego al mismo digest **por su cuenta**.
    """

    def _externo(self):
        import importlib

        ejemplos = _os.path.join(_RAIZ, "examples")
        if ejemplos not in _sys.path:
            _sys.path.insert(0, ejemplos)
        return importlib.import_module("verificar_recibo_externo")

    def test_p91a_los_artefactos_dan_el_mismo_digest_en_los_dos_lectores(self) -> None:
        externo = self._externo()
        self.assertNotIn("protocol", externo.__dict__)
        for archivo, nombre, gramatica, filas, digest in _MEDIDO:
            with self.subTest(archivo=archivo):
                texto = _texto(archivo)
                leidas, leido_por, _ = externo._leer_manifiesto(
                    texto, "auto", nombre or None
                )
                propia = leer(texto, gramatica, nombre or None)
                self.assertEqual(leido_por, gramatica)
                self.assertEqual(len(leidas), filas)
                canonica = sorted(leidas, key=lambda fila: fila[0].encode("utf-8"))
                self.assertEqual(externo._digest_de_pagina(canonica, "m"), propia.digest())
                self.assertEqual(propia.digest()[:12], digest)

    def test_p91b_declarar_un_portador_que_no_encaja_es_entrada_invalida(self) -> None:
        """El verificador del tercero no adivina: declara, y si no encaja sale con 2."""

        externo = self._externo()
        casos = (
            ("debian-12.15-Release", "coreutils", None),
            ("go-1.23.3.sha256", "suelto", None),
            ("jq-1.7.1-sha256sum.txt", "inventado", None),
        )
        for archivo, portador, nombre in casos:
            with self.subTest(archivo=archivo, portador=portador):
                with self.assertRaises(externo.EntradaInvalida):
                    externo._leer_manifiesto(_texto(archivo), portador, nombre)
        codigo, lineas = externo.verificar(
            externo._demo(), None, "cita-09:30-sillon1"
        )
        self.assertEqual(codigo, 0)
        self.assertTrue(any(linea.startswith("intervalo |") for linea in lineas))


if __name__ == "__main__":
    _unittest.main()
