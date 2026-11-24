"""test_predicado.py — el Anillo 0, medido por sus falsadores.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

Lecturas declaradas. Ninguna se hace pasar por el texto de SPEC.md:

  1. El contrato del predicado vive en `PREDICADO.md` (§`#v1`), no en `SPEC.md`:
     el SPEC está sellado con fecha cierta y una sección nueva lo invalidaría.
     El caso P-18 es el **lector** de ese puntero —comprueba que el ancla exista
     y que el tipo declarado resuelva a este repositorio—, porque una convención
     sin lector se pudre sin que nadie lo note.
  2. Las rutas de la referencia heredan el alfabeto ASCII de §2.1 vía
     `RutaRelativa`; por eso NFC/NFD **no** las toca y el caso de normalización
     se mide sobre texto libre (`afirmacion`, `entorno`). Medirlo sobre rutas
     habría sido una prueba que no puede diferir.
  3. El caso de la cadena reescrita afirma un **resultado negativo**: una cadena
     de digests sin ancla cuadra aunque un atacante la reescriba de punta a
     punta. Se escribe como aserción y no como comentario porque es el límite
     que la `Contrafirma` existe para cubrir; esconderlo sería vender una
     garantía que el formato no da.
  4. El caso de compacidad mide el predicado REAL sobre los archivos de este
     repositorio, no sobre fixtures: una página que sólo cabe con datos de
     juguete no es una página.
  5. Este archivo imprime lo medido con el prefijo `MEDICION |`.

NO CUBIERTO por este archivo (lista cerrada): la firma criptográfica y el ancla
pública (la `Contrafirma` es un enunciado, no una firma) · la medición del
sistema de archivos (`metrics`) · el tiempo de verificación, que se publica como
medición informativa y no como aserción, porque un umbral de reloj de pared en
un test es una prueba que falla sin que nada se haya roto.
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import os as _os
import sys as _sys
import unicodedata as _unicodedata
import unittest as _unittest

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_SRC = _os.path.join(_RAIZ, "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.predicado import (  # noqa: E402
    TIPO_DE_ESTATUTO,
    TIPO_DE_PREDICADO,
    Contrafirma,
    Entorno,
    Eslabon,
    Predicado,
    VeredictoAdjudicado,
    VeredictoReclamado,
    canonizar,
    contrafirmar,
    desde_in_toto,
    verificar_cadena,
    verificar_contrafirma,
)
from protocol.types import (  # noqa: E402
    ALGORITMO,
    ContratoViolado,
    Divergencia,
    EntradaManifiesto,
    Hash,
    RutaRelativa,
)

#: Cotas de la página, fijadas sobre la medición del 2026-11-24 del **acto
#: real** (`examples/emitir_predicado.py`, que es el que emite el recibo):
#: 61 líneas y 1 881 bytes con 4 entradas y 6 referencias de código.
#: Se mide el acto, no una fixture: una cota sobre una fixture es una cota
#: sobre la fixture. La holgura admite una referencia más y nada más.
COPTA_LINEAS = 65
COPTA_BYTES = 2000

H_A = Hash(ALGORITMO, "a" * 64)
H_B = Hash(ALGORITMO, "b" * 64)
H_C = Hash(ALGORITMO, "c" * 64)
H_D = Hash(ALGORITMO, "d" * 64)


def _medicion(etiqueta: str, valor: object) -> None:
    print("MEDICION | %s | %s" % (etiqueta, valor))


def _entrada(ruta: str, h: Hash) -> EntradaManifiesto:
    return EntradaManifiesto(RutaRelativa(ruta), h)


def _slug(titulo: str) -> str:
    """Slug de ancla al estilo GitHub: minúsculas, espacios a `-`, resto fuera."""

    bajo = titulo.lower().replace(" ", "-")
    return "".join(c for c in bajo if c.isalnum() or c in "-_")


def _entorno() -> Entorno:
    version = "CPython %d.%d.%d" % _sys.version_info[:3]
    return Entorno(_sys.platform, version, ("corrida en CI linux",))


def _predicado(
    afirmacion: str = "el archivo medido se produce con el código declarado",
    entradas: tuple = (),
    codigo: tuple = (),
    salida_h: Hash = H_C,
    veredicto: VeredictoReclamado = VeredictoReclamado.CONFORME,
    h_prev: object = None,
) -> Predicado:
    return Predicado(
        afirmacion=afirmacion,
        entradas=entradas if entradas else (_entrada("datos/tabla.csv", H_A),),
        codigo=codigo if codigo else (_entrada("src/medir.py", H_B),),
        entorno=_entorno(),
        salida=_entrada("salida/reporte.json", salida_h),
        veredicto=veredicto,
        h_prev=h_prev,
    )


def _cadena() -> tuple:
    p0 = _predicado(afirmacion="primer acto")
    p1 = _predicado(afirmacion="segundo acto", h_prev=p0.digest())
    p2 = _predicado(afirmacion="tercer acto", h_prev=p1.digest())
    return (p0, p1, p2)


class TestFormaCanonica(_unittest.TestCase):
    """El canon es la única función que un tercero debe reimplementar."""

    def test_p01_el_canon_no_depende_del_orden_de_las_llaves(self) -> None:
        uno = {"b": 1, "a": {"d": [1, 2], "c": "x"}}
        otro = {"a": {"c": "x", "d": [1, 2]}, "b": 1}
        self.assertEqual(canonizar(uno), canonizar(otro))
        _medicion("P-01 canon de dos órdenes", canonizar(uno) == canonizar(otro))

    def test_p02_nfd_y_nfc_dan_el_mismo_digest(self) -> None:
        compuesto = _unicodedata.normalize("NFC", "medición de la señal")
        descompuesto = _unicodedata.normalize("NFD", compuesto)
        self.assertNotEqual(compuesto, descompuesto, "la fixture no difiere: la prueba no puede diferir")
        p_nfc = _predicado(afirmacion=compuesto)
        p_nfd = _predicado(afirmacion=descompuesto)
        self.assertEqual(p_nfc.digest(), p_nfd.digest())
        self.assertEqual(
            _unicodedata.is_normalized("NFC", p_nfd.afirmacion),
            True,
            "el predicado guarda el texto en NFC, no la forma con la que llegó",
        )
        _medicion("P-02 NFD/NFC digest", p_nfd.digest().digest[:16])
        _medicion("P-02 NFD guardado como NFC", _unicodedata.is_normalized("NFC", p_nfd.afirmacion))

    def test_p03_el_canon_rechaza_flotantes(self) -> None:
        with self.assertRaises(ContratoViolado):
            canonizar({"r0": 1.2316})
        with self.assertRaises(ContratoViolado):
            canonizar({"anidado": [{"x": 0.5}]})
        self.assertEqual(canonizar({"r0": "1.2316"}), b'{"r0":"1.2316"}')
        _medicion("P-03 flotante rechazado", "ContratoViolado")


class TestEntornoDeclarado(_unittest.TestCase):
    """Un entorno sin lagunas declaradas es una afirmación fuerte, no un vacío."""

    def test_p04_el_entorno_vacio_no_construye(self) -> None:
        with self.assertRaises(ContratoViolado):
            Entorno("", "CPython 3.12.13")
        with self.assertRaises(ContratoViolado):
            Entorno("darwin", "   ")
        _medicion("P-04 entorno vacío", "ContratoViolado")

    def test_p05_la_laguna_se_declara_y_no_se_omite(self) -> None:
        with self.assertRaises(ContratoViolado):
            Entorno("darwin", "CPython 3.12.13", None)  # type: ignore[arg-type]
        with self.assertRaises(ContratoViolado):
            Entorno("darwin", "CPython 3.12.13", ("",))
        sin_lagunas = Entorno("darwin", "CPython 3.12.13", ())
        self.assertEqual(sin_lagunas.no_medido, ())
        _medicion("P-05 `() ` explícito", "construye")


class TestPredicado(_unittest.TestCase):
    """Las siete fronteras del objeto."""

    def test_p06_los_siete_campos_estan_y_el_veredicto_es_reclamado(self) -> None:
        cuerpo = _predicado().cuerpo()
        self.assertEqual(
            tuple(sorted(cuerpo)),
            ("afirmacion", "codigo", "entorno", "entradas", "h_prev", "salida", "veredicto"),
        )
        with self.assertRaises(ContratoViolado):
            _predicado(veredicto=VeredictoAdjudicado.CONFIRMA)  # type: ignore[arg-type]
        with self.assertRaises(ContratoViolado):
            _predicado(afirmacion="")
        _medicion("P-06 campos", len(cuerpo))

    def test_p07_una_identidad_truncada_no_es_identidad(self) -> None:
        truncado = Hash(ALGORITMO, "a" * 12, anchura=12)
        with self.assertRaises(ContratoViolado):
            _predicado(entradas=(_entrada("datos/tabla.csv", truncado),))
        with self.assertRaises(ContratoViolado):
            _predicado(salida_h=truncado)
        _medicion("P-07 hash truncado", "ContratoViolado")

    def test_p08_las_rutas_van_en_orden_byte_a_byte_y_sin_repetir(self) -> None:
        with self.assertRaises(ContratoViolado):
            _predicado(
                entradas=(_entrada("datos/z.csv", H_A), _entrada("datos/a.csv", H_B)),
            )
        with self.assertRaises(ContratoViolado):
            _predicado(
                entradas=(_entrada("datos/a.csv", H_A), _entrada("datos/a.csv", H_B)),
            )
        _medicion("P-08 desorden y repetición", "ContratoViolado")


class TestCadena(_unittest.TestCase):
    """Coherencia interna, y el límite que se declara en voz alta."""

    def test_p09_una_cadena_de_tres_cuadra(self) -> None:
        cadena = _cadena()
        self.assertIs(verificar_cadena(cadena), True)
        self.assertEqual([p.h_prev for p in cadena[1:]], [p.digest() for p in cadena[:-1]])
        _medicion("P-09 cadena de tres", [p.digest().digest[:8] for p in cadena])

    def test_p10_mutar_cualquiera_de_los_siete_campos_rompe_la_cadena(self) -> None:
        p0, p1, p2 = _cadena()
        mutaciones = {
            "afirmacion": _predicado(afirmacion="otro acto", h_prev=p0.digest()),
            "entradas": _predicado(entradas=(_entrada("datos/tabla.csv", H_D),), h_prev=p0.digest()),
            "codigo": _predicado(codigo=(_entrada("src/medir.py", H_D),), h_prev=p0.digest()),
            "entorno": _predicado(h_prev=p0.digest()),
            "salida": _predicado(salida_h=H_D, h_prev=p0.digest()),
            "veredicto": _predicado(veredicto=VeredictoReclamado.NO_CONFORME, h_prev=p0.digest()),
            "h_prev": _predicado(h_prev=None),
        }
        medido = []
        for campo, mutado in mutaciones.items():
            if campo == "entorno":
                mutado = Predicado(
                    afirmacion="el archivo medido se produce con el código declarado",
                    entradas=(_entrada("datos/tabla.csv", H_A),),
                    codigo=(_entrada("src/medir.py", H_B),),
                    entorno=Entorno(_sys.platform, "CPython 0.0.0", ("corrida en CI linux",)),
                    salida=_entrada("salida/reporte.json", H_C),
                    veredicto=VeredictoReclamado.CONFORME,
                    h_prev=p0.digest(),
                )
            self.assertNotEqual(mutado.digest(), p1.digest(), "la mutación de %s no cambió el digest" % campo)
            resultado = verificar_cadena((p0, mutado, p2))
            self.assertIsInstance(resultado, Eslabon, "la mutación de %s no fue detectada" % campo)
            medido.append((campo, resultado.indice))
        _medicion("P-10 mutaciones detectadas", medido)
        self.assertEqual(len(medido), 7)

    def test_p11_una_cadena_reescrita_cuadra_sin_ancla(self) -> None:
        """El resultado negativo: sin ancla, el formato no distingue reescritura.

        Un atacante que reescribe los tres eslabones y recalcula cada `h_prev`
        produce una cadena que este verificador aprueba. Sólo la `Contrafirma`
        anclada —commit, DOI, log de transparencia— lo detecta. Se mide para que
        nadie venda lo contrario.
        """

        reescrita = []
        previo = None
        for acto in ("acto falsificado uno", "acto falsificado dos", "acto falsificado tres"):
            eslabon = _predicado(afirmacion=acto, h_prev=previo)
            reescrita.append(eslabon)
            previo = eslabon.digest()
        self.assertIs(verificar_cadena(tuple(reescrita)), True)
        original = _cadena()
        self.assertNotEqual(reescrita[0].digest(), original[0].digest())
        _medicion("P-11 cadena reescrita", "cuadra sin ancla (límite declarado)")

    def test_p12_un_fragmento_no_es_una_cadena_rota(self) -> None:
        cadena = _cadena()
        fragmento = cadena[1:]
        self.assertIsInstance(verificar_cadena(fragmento), Eslabon)
        self.assertIs(verificar_cadena(fragmento, exigir_origen=False), True)
        with self.assertRaises(ContratoViolado):
            verificar_cadena(())
        _medicion("P-12 fragmento", "universo distinto, no cadena rota")


class TestContrafirma(_unittest.TestCase):
    """El objeto vendible: la respuesta de un tercero sobre un acto."""

    def test_p13_la_contrafirma_cubre_el_digest_y_no_otro(self) -> None:
        p = _predicado()
        firma = contrafirmar(p, "auditoría externa", VeredictoAdjudicado.CONFIRMA, "doi:10.5281/zenodo.X")
        self.assertIs(verificar_contrafirma(p, firma), True)
        otro = _predicado(afirmacion="otro acto")
        divergencia = verificar_contrafirma(otro, firma)
        self.assertIsInstance(divergencia, Divergencia)
        assert isinstance(divergencia, Divergencia)
        self.assertEqual(divergencia.campo, "digest_del_predicado")
        _medicion("P-13 contrafirma sobre otro acto", divergencia.campo)

    def test_p14_la_contrafirma_adjudica_no_reclama(self) -> None:
        with self.assertRaises(ContratoViolado):
            Contrafirma("x", H_A, VeredictoReclamado.CONFORME)  # type: ignore[arg-type]
        with self.assertRaises(ContratoViolado):
            Contrafirma("", H_A, VeredictoAdjudicado.CONFIRMA)
        try:
            firma = Contrafirma("x", H_A, VeredictoAdjudicado.CONFIRMA, "")
        except ContratoViolado:
            pass
        else:  # pragma: no cover - sólo si el contrato se afloja
            self.fail("un ancla vacía no es ⊥: es un ancla no declarada")
        self.assertIsNone(Contrafirma("x", H_A, VeredictoAdjudicado.NO_MEDIDO).ancla)
        _medicion("P-14 veredicto ajeno rechazado", "ContratoViolado")


class TestProyeccionInToto(_unittest.TestCase):
    """La proyección es una vista; la ida y vuelta prueba que no pierde nada."""

    def test_p15_ida_y_vuelta_conserva_los_siete_campos(self) -> None:
        p = _predicado(h_prev=H_D)
        estatuto = p.a_in_toto()
        self.assertEqual(estatuto["_type"], TIPO_DE_ESTATUTO)
        self.assertEqual(estatuto["predicateType"], TIPO_DE_PREDICADO)
        self.assertEqual(estatuto["subject"][0]["digest"][ALGORITMO], H_C.digest)
        self.assertEqual(len(estatuto["subject"]), 1)
        self.assertNotIn("salida", estatuto["predicate"])
        self.assertEqual(desde_in_toto(estatuto), p)
        self.assertEqual(desde_in_toto(estatuto).digest(), p.digest())
        _medicion("P-15 in-toto ida y vuelta", "iguales")

    def test_p16_un_estatuto_de_otro_tipo_no_se_traduce(self) -> None:
        estatuto = _predicado().a_in_toto()
        with self.assertRaises(ContratoViolado):
            desde_in_toto(dict(estatuto, predicateType="https://slsa.dev/provenance/v1"))
        with self.assertRaises(ContratoViolado):
            desde_in_toto(dict(estatuto, _type="https://example.test/Otro/v1"))
        with self.assertRaises(ContratoViolado):
            desde_in_toto(dict(estatuto, subject=[]))
        _medicion("P-16 tipo ajeno", "ContratoViolado")


class TestPagina(_unittest.TestCase):
    """Una página medida sobre los archivos reales, no sobre fixtures."""

    def _predicado_real(self) -> Predicado:
        def referencias(subdir: str) -> tuple:
            base = _os.path.join(_RAIZ, subdir)
            entradas = []
            for nombre in sorted(_os.listdir(base)):
                if not nombre.endswith(".py") or nombre == "__init__.py":
                    continue
                with open(_os.path.join(base, nombre), "rb") as flujo:
                    digest = _hashlib.sha256(flujo.read()).hexdigest()
                entradas.append(_entrada("%s/%s" % (subdir, nombre), Hash(ALGORITMO, digest)))
            return tuple(entradas)

        codigo = list(referencias("src/protocol"))
        ruta_emisor = _os.path.join(_RAIZ, "examples", "emitir_predicado.py")
        with open(ruta_emisor, "rb") as flujo:
            emisor = _hashlib.sha256(flujo.read()).hexdigest()
        codigo.append(_entrada("examples/emitir_predicado.py", Hash(ALGORITMO, emisor)))

        return Predicado(
            afirmacion="la suite declara verde sobre el código medido, en el entorno declarado",
            entradas=referencias("tests"),
            codigo=tuple(sorted(codigo, key=lambda e: e.ruta.clave_bytes)),
            entorno=_entorno(),
            salida=_entrada("examples/veredicto-suite.txt", H_C),
            veredicto=VeredictoReclamado.CONFORME,
        )

    def test_p17_la_pagina_cabe_y_se_mide(self) -> None:
        predicado = self._predicado_real()
        pagina = predicado.pagina()
        lineas = len(pagina.splitlines())
        bytes_ = len(pagina.encode("utf-8"))
        _medicion("P-08 página", (lineas, bytes_))
        _medicion("P-08 referencias", (len(predicado.entradas), len(predicado.codigo)))
        _medicion("P-08 digest de la página", predicado.digest().digest[:16])
        self.assertLessEqual(lineas, COPTA_LINEAS)
        self.assertLessEqual(bytes_, COPTA_BYTES)
        self.assertEqual(_json.loads(pagina), predicado.cuerpo())

    def test_p18_el_tipo_de_predicado_tiene_documento_y_ancla(self) -> None:
        prefijo = "https://github.com/alexisromtz-lab/protocol-core/blob/main/"
        self.assertTrue(TIPO_DE_PREDICADO.startswith(prefijo), TIPO_DE_PREDICADO)
        resto = TIPO_DE_PREDICADO[len(prefijo) :]
        archivo, _, ancla = resto.partition("#")
        self.assertTrue(ancla, "el tipo debe nombrar un ancla, no sólo el archivo")

        ruta = _os.path.join(_RAIZ, archivo)
        self.assertTrue(_os.path.exists(ruta), "el documento del predicado no existe: %s" % archivo)
        with open(ruta, "r", encoding="utf-8") as flujo:
            texto = flujo.read()

        # Ancla al estilo GitHub: se pliega el título a slug (minúsculas,
        # espacios a guion, se cae la puntuación) y se exige que el declarado
        # sea uno de los slugs del documento. Comparar contra el título crudo
        # mediría el archivo; esto mide el enlace que un tercero va a pulsar.
        titulos = [linea for linea in texto.splitlines() if linea.startswith("#")]
        slugs = [_slug(linea.lstrip("#").strip()) for linea in titulos]
        _medicion("P-18 ancla", (archivo, ancla, len(slugs), ancla in slugs))
        self.assertIn(ancla, slugs, "ningún título de %s produce el ancla %r" % (archivo, ancla))
        # El documento tiene que declarar el límite que el producto vende como
        # límite, no como garantía: si desaparece del documento, desaparece del
        # contrato y el verificador de un tercero no lo sabría.
        self.assertIn("sin ancla", texto)


if __name__ == "__main__":
    _unittest.main()
