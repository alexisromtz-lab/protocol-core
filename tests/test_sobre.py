"""test_sobre.py — el anillo 6: el sobre, que envuelve al portador.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

QUE MIDE. Que el mismo autor publicando **los mismos bytes** de tres formas se lea
igual de las tres. Medido el 2026-11-25 sobre Debian 12: `Release` (149 266 B, sin
sobre) se leia; `InRelease` (151 075 B, firmado en claro) **se rechazaba** —con un
mensaje que ademas culpaba a la carga (`linea 4: 'Origin: Debian'`)— y `Release.gpg`
(1 760 B, firma pegada) no tiene filas porque atestigua a otro archivo.

LA DIANA ES DEL TERCERO. No hay ningun numero que este archivo invente: la carga
de `InRelease` tiene que dar, quitado el sobre, el `sha256` del `Release` entero.
Ese digest lo publica Debian; el lector solo puede acertarlo o fallarlo (P-93).

LA LEY DEL ANILLO. El sobre no cambia el objeto, cambia el archivo: dos digests,
`sobre` (el archivo) y `carga` (el objeto), y cuando no hay sobre son el mismo
(P-97). Corolario medido: las dos topologias que Debian publica del mismo contenido
llevan **dos firmas distintas** —1 452 de 1 732 bytes difieren—, porque la pegada
firma el archivo crudo y la de en-claro firma el texto canonizado. Decir «la misma
firma» seria falso; se publica como resultado negativo.

LA SEGUNDA LEY, que corrige a este mismo repositorio. `FUENTES.txt` declaraba sobre
el `Release` «la firma PGP final no se verifica», y ese archivo no tiene ni un byte
de PGP. Un punto ciego inventado es tan grave como un verde falso: el auditor no
puede distinguir «no pude verificarlo» de «no habia nada que verificar». Por eso
P-95 exige la **doble implicacion** sobre los diez artefactos vendorizados: se
nombra `firma no verificada` **si y solo si** hay bytes de firma.

NO CUBIERTO (lista cerrada): que la firma sea autentica —no hay verificacion de
clave publica en este anillo, y `firma no verificada` viaja con su numero de
bytes—; y la **frecuencia** del escape `- `, que ningun artefacto real ejercita
(medido: 0 lineas en los diez), de modo que el escape se mide por testigo
sintetico y su frecuencia se declara `no_medida` (P-96).
"""

from __future__ import annotations

import hashlib as _hashlib
import os as _os
import sys as _sys
import unittest as _unittest

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_SRC = _os.path.join(_RAIZ, "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.portador import facultades, leer_sin_declarar  # noqa: E402
from protocol.sobre import (  # noqa: E402
    TOPOLOGIAS,
    SobreSinCarga,
    desenvolver,
    leer_sobre,
)

_PORTADORES = _os.path.join(_RAIZ, "examples", "portadores")

#: Los diez artefactos vendorizados. `FUENTES.txt` no es uno de ellos: es el censo.
_ARTEFACTOS = tuple(
    sorted(n for n in _os.listdir(_PORTADORES) if n != "FUENTES.txt")
)

#: El `sha256` de `debian-12.15-Release` completo, publicado por Debian y medido
#: en `FUENTES.txt`. Es la diana: el lector no la calcula, la tiene que acertar.
_SHA256_DEL_RELEASE = "abcf5882746e0f68171f41adbb4ac01b74b49d62d203379befb9265804311a4f"

#: El digest canonico de la pagina que ambos archivos publican (`c0dc59762595`).
_DIGEST_DE_LA_PAGINA = "c0dc59762595"


def _texto(archivo: str) -> str:
    with open(_os.path.join(_PORTADORES, archivo), "rb") as mango:
        return mango.read().decode("utf-8")


def _sha256(archivo: str) -> str:
    with open(_os.path.join(_PORTADORES, archivo), "rb") as mango:
        return _hashlib.sha256(mango.read()).hexdigest()


def _bloque_de_firma(texto: str) -> str:
    lineas = texto.split("\n")
    inicio = next(i for i, l in enumerate(lineas) if l.rstrip() == "-----BEGIN PGP SIGNATURE-----")
    fin = next(i for i, l in enumerate(lineas) if l.rstrip() == "-----END PGP SIGNATURE-----")
    return "\n".join(lineas[inicio : fin + 1])


class TestLaDianaEsDelTercero(_unittest.TestCase):
    def test_p93_el_sobre_se_quita_y_la_carga_es_el_archivo_sin_firmar(self) -> None:
        """Quitado el sobre, `InRelease` **es** `Release`: 149 266 B y su sha256.

        El valor esperado lo publica Debian en `FUENTES.txt`; si el lector se
        equivoca en un byte, lo falla. No hay margen para que dos errores se
        compensen: el digest es de 256 bits.
        """

        sobre = leer_sobre(_texto("debian-12.15-InRelease"))
        self.assertEqual(sobre.topologia, "firmado_en_claro")
        self.assertEqual(sobre.carga_digest, _SHA256_DEL_RELEASE)
        self.assertEqual(sobre.carga_digest, _sha256("debian-12.15-Release"))
        self.assertEqual(
            _hashlib.sha256(sobre.carga.encode("utf-8", "surrogateescape")).hexdigest(),
            _SHA256_DEL_RELEASE,
        )
        self.assertEqual(len(sobre.carga.encode("utf-8", "surrogateescape")), 149266)

    def test_p93b_la_pagina_del_firmado_y_la_del_sin_firmar_son_la_misma(self) -> None:
        """Antes del anillo 6 este archivo se **rechazaba**. Ahora publica la misma pagina."""

        firmado = leer_sin_declarar(_texto("debian-12.15-InRelease"))
        sin_firmar = leer_sin_declarar(_texto("debian-12.15-Release"))
        self.assertEqual(firmado.portador, "deb822")
        self.assertEqual(len(firmado.pares), 772)
        self.assertEqual(firmado.digest(), sin_firmar.digest())
        self.assertTrue(firmado.digest().startswith(_DIGEST_DE_LA_PAGINA))
        self.assertEqual(facultades(_texto("debian-12.15-InRelease")), ("deb822",))


class TestLasTresTopologias(_unittest.TestCase):
    def test_p94_el_mismo_autor_publica_el_mismo_contenido_de_tres_formas(self) -> None:
        """`sin_sobre`, `firmado_en_claro` y `firma_pegada` son hechos de Debian 12."""

        self.assertEqual(
            tuple(leer_sobre(_texto(n)).topologia for n in (
                "debian-12.15-Release",
                "debian-12.15-InRelease",
                "debian-12.15-Release.gpg",
            )),
            ("sin_sobre", "firmado_en_claro", "firma_pegada"),
        )
        self.assertEqual(TOPOLOGIAS, ("sin_sobre", "firmado_en_claro", "firma_pegada"))

    def test_p94b_una_firma_pegada_no_trae_filas_y_lo_nombra(self) -> None:
        """`Release.gpg` atestigua a otro archivo y no lo nombra: el vinculo es el nombre.

        Devolver cero filas seria publicar un manifiesto vacio, que es distinto de
        publicar «esto no es un manifiesto». El tipo `SobreSinCarga` es el veredicto.
        """

        texto = _texto("debian-12.15-Release.gpg")
        sobre = leer_sobre(texto)
        self.assertEqual(sobre.carga, "")
        self.assertEqual(sobre.carga_digest, "")
        self.assertGreater(sobre.bytes_firma, 0)
        with self.assertRaises(SobreSinCarga) as caja:
            desenvolver(texto)
        self.assertGreater(caja.exception.bytes_firma, 0)


class TestElPuntoCiegoSeDeclaraConTestigo(_unittest.TestCase):
    def test_p95_ningun_artefacto_sin_firma_declara_una_firma_que_no_verificar(self) -> None:
        """Doble implicacion sobre los diez artefactos: `firma no verificada` ⇔ hay firma.

        Este es el falsador del defecto medido en `FUENTES.txt`, que afirmaba no
        verificar la firma de un archivo con cero bytes de PGP. Una sola direccion
        no basta: sin firma no se declara el punto ciego, y con firma no se calla.
        """

        medido = {}
        for nombre in _ARTEFACTOS:
            sobre = leer_sobre(_texto(nombre))
            dicho = any("firma no verificada" in linea for linea in sobre.lineas())
            medido[nombre] = (sobre.bytes_firma > 0, dicho)
        con_firma = [n for n, (firma, _) in medido.items() if firma]
        self.assertEqual(
            sorted(con_firma), ["debian-12.15-InRelease", "debian-12.15-Release.gpg", "fedora-41-CHECKSUM"]
        )
        for nombre, (firma, dicho) in medido.items():
            self.assertEqual(firma, dicho, "%s declara firma=%s pero dice=%s" % (nombre, firma, dicho))

    def test_p95b_sin_sobre_se_publica_un_hecho_y_no_una_disculpa(self) -> None:
        """`0 bytes de firma | no habia nada que verificar` es el estado honesto."""

        lineas = leer_sobre(_texto("debian-12.15-Release")).lineas()
        self.assertEqual(len(lineas), 1)
        self.assertIn("0 bytes de firma", lineas[0])
        self.assertIn("no habia nada que verificar", lineas[0])
        self.assertNotIn("firma no verificada", lineas[0])


class TestElEscapeDelSobre(_unittest.TestCase):
    @staticmethod
    def _envolver(carga: str) -> str:
        escapada = "\n".join(
            ("- " + linea if linea.startswith("-") else linea) for linea in carga.split("\n")
        )
        return (
            "-----BEGIN PGP SIGNED MESSAGE-----\nHash: SHA256\n\n%s"
            "-----BEGIN PGP SIGNATURE-----\n\niQIzBAEBCAAdFiEE\n=abcd\n"
            "-----END PGP SIGNATURE-----\n" % (escapada,)
        )

    def test_p96_el_escape_de_rfc_4880_se_deshace_y_se_cuenta(self) -> None:
        """`- ruta` firmado es `ruta` leido. La carga vuelve byte a byte a su origen."""

        carga = (
            "%s  a.md\n"
            "-%s  ruta-que-empieza-por-guion.md\n"
            "-texto-libre-que-tambien-empieza-por-guion\n" % ("a" * 64, "b" * 64)
        )
        sobre = leer_sobre(self._envolver(carga))
        self.assertEqual(sobre.topologia, "firmado_en_claro")
        self.assertEqual(sobre.escapadas, 2)
        self.assertEqual(sobre.carga, carga)
        self.assertEqual(
            sobre.carga_digest,
            _hashlib.sha256(carga.encode("utf-8", "surrogateescape")).hexdigest(),
        )

    def test_p96b_la_frecuencia_del_escape_en_lo_real_se_declara_no_medida(self) -> None:
        """Ningun artefacto real del censo trae una linea escapada: 0 de 10.

        El eje se mide por testigo sintetico (P-96); su frecuencia en lo publicado
        es `no_medida`, y se publica como tal en vez de suponerla cero.
        """

        total = sum(leer_sobre(_texto(n)).escapadas for n in _ARTEFACTOS)
        self.assertEqual(total, 0)
        self.assertEqual(len(_ARTEFACTOS), 10)


class TestDosArchivosUnObjeto(_unittest.TestCase):
    def test_p97_el_sobre_cambia_el_archivo_y_no_el_objeto(self) -> None:
        """`sobre` ≠ `carga` en el firmado, y `carga` del firmado = `sobre` del sin firmar."""

        firmado = leer_sobre(_texto("debian-12.15-InRelease"))
        sin_firmar = leer_sobre(_texto("debian-12.15-Release"))
        self.assertNotEqual(firmado.sobre_digest, firmado.carga_digest)
        self.assertEqual(firmado.carga_digest, sin_firmar.sobre_digest)
        self.assertEqual(sin_firmar.sobre_digest, sin_firmar.carga_digest)
        self.assertEqual(firmado.sobre_digest, _sha256("debian-12.15-InRelease"))
        self.assertEqual(firmado.bytes_firma, 1759)
        self.assertGreater(
            len(_texto("debian-12.15-InRelease").encode("utf-8")),
            len(_texto("debian-12.15-Release").encode("utf-8")),
        )

    def test_p97b_las_dos_formas_llevan_dos_firmas_distintas(self) -> None:
        """Resultado negativo medido: misma longitud, 1 452 de 1 732 bytes distintos.

        La pegada firma el archivo crudo; la de en-claro, el texto canonizado por
        RFC 4880. Publicar «la misma firma» seria un falso verde sobre el autor.
        """

        pegada = _bloque_de_firma(_texto("debian-12.15-Release.gpg"))
        en_claro = _bloque_de_firma(_texto("debian-12.15-InRelease"))
        self.assertNotEqual(pegada, en_claro)
        self.assertEqual(len(pegada), len(en_claro))
        distintos = sum(1 for a, b in zip(pegada, en_claro) if a != b)
        self.assertEqual(distintos, 1452)


class TestElTerceroDesenvuelveSinLlamarAlGenerador(_unittest.TestCase):
    """P-98: el verificador externo quita el sobre por su cuenta y coincide.

    Antes del anillo 6 el tercero leia el `InRelease` **por casualidad**: la
    cabecera del sobre caia en el mismo cubo que los comentarios y el digest
    salia bien sin que el verificador pudiera decir que parte habia medido. Un
    digest acertado por casualidad no es una facultad; es un verde que no se
    sostiene cuando el artefacto cambia de forma.
    """

    def _externo(self):
        import importlib

        ejemplos = _os.path.join(_RAIZ, "examples")
        if ejemplos not in _sys.path:
            _sys.path.insert(0, ejemplos)
        return importlib.import_module("verificar_recibo_externo")

    def test_p98a_los_dos_desenvolvedores_coinciden_en_el_censo_entero(self) -> None:
        externo = self._externo()
        self.assertNotIn("protocol", externo.__dict__)
        for nombre in _ARTEFACTOS:
            with self.subTest(archivo=nombre):
                texto = _texto(nombre)
                topologia, carga, bytes_firma, escapadas = externo._desenvolver(texto)
                propio = leer_sobre(texto)
                self.assertEqual(
                    (topologia, carga, bytes_firma, escapadas),
                    (propio.topologia, propio.carga, propio.bytes_firma, propio.escapadas),
                )

    def test_p98b_el_tercero_da_el_mismo_digest_de_carga_que_el_generador(self) -> None:
        """La diana de P-93, ahora por la otra implementacion, que no importa nada."""

        externo = self._externo()
        carga = externo._desenvolver(_texto("debian-12.15-InRelease"))[1]
        self.assertEqual(
            _hashlib.sha256(carga.encode("utf-8", "surrogateescape")).hexdigest(),
            _SHA256_DEL_RELEASE,
        )
        leidas, leido_por, _ = externo._leer_manifiesto(carga, "auto", None)
        self.assertEqual(leido_por, "deb822")
        canonica = sorted(leidas, key=lambda fila: fila[0].encode("utf-8"))
        self.assertEqual(
            externo._digest_de_pagina(canonica, "m"),
            leer_sin_declarar(_texto("debian-12.15-Release")).digest(),
        )

    def test_p98c_una_firma_pegada_es_entrada_invalida_y_no_un_manifiesto_vacio(self) -> None:
        externo = self._externo()
        with self.assertRaises(externo.EntradaInvalida) as caja:
            externo.verificar(
                externo._demo(), _texto("debian-12.15-Release.gpg"), None
            )
        self.assertIn("cero carga", str(caja.exception))
