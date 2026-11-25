"""test_predicado.py — el Anillo 0, medido por sus falsadores.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

Lecturas declaradas. Ninguna se hace pasar por el texto de SPEC.md:

  1. El contrato del predicado vive en `PREDICADO.md` (§`#predicado-v1`), no en
     `SPEC.md`: el SPEC está sellado con fecha cierta y una sección nueva lo
     invalidaría. Los casos P-18, P-19 y P-20 son los **lectores** de ese
     contrato —P-18 del ancla, P-19 de las cinco decisiones que un tercero podía
     tomar al revés, y P-20 de que la implementación las obedece—, porque una
     convención sin lector se pudre sin que nadie lo note.
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
    desde_cuerpo,
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
#: real** (`examples/emitir_predicado.py`, que es el que emite el recibo).
#: Se mide el acto, no una fixture: una cota sobre una fixture es una cota
#: sobre la fixture. La holgura admite una referencia más y nada más.
#:
#: Re-declarada el mismo día al crecer el acto de 4 a 5 entradas y de 6 a 7
#: referencias de código: 69 líneas y 2 158 bytes. La subida **nombra sus
#: artefactos** (`src/protocol/ubicacion.py` y `tests/test_ubicacion.py`,
#: ambos dentro del acto porque la suite los ejecuta); una subida que no
#: pueda nombrar el artefacto que la causa no se hace, se parte el acto. El
#: formato cuesta 4 líneas por artefacto: un campo nuevo en cada entrada
#: rompe esta cota, y eso es lo que la cota vigila.
#:
#: Subida del 2026-11-25 a 77 líneas y 2 431 bytes, y los artefactos que la
#: causan se nombran: `tests/test_ausencia.py` entra en la página porque la
#: suite lo ejecuta, y `src/protocol/ausencia.py` porque la suite lo importa.
#: Dos artefactos, ocho líneas: el formato cuesta 4 por artefacto, no 3 — la
#: subida anterior había declarado 3 y por eso la cota quedó corta. El orden del
#: anillo 3 no se pagó con un campo nuevo, se pagó con las filas que le tocan.
#:
#: Lección del 2026-11-25 (§A2.2 aplicado al instrumento): la cota medía
#: `_predicado_real()`, una **reconstrucción** de la página, y la reconstrucción
#: se había separado del acto (otra `afirmacion`, otro `no_medido`): 76 líneas
#: allí, 77 aquí. La cota pasaba midiendo una página que el acto no emite. Por
#: eso ahora se mide el artefacto emitido y la reconstrucción sólo tiene que
#: **coincidir en forma** con él. Una cota sobre una copia no vigila el objeto.
#: Subida del 2026-11-25 a 81 líneas y 2 567 bytes: un tercer artefacto,
#: `tests/test_guiones.py`, entra por la misma puerta que las otras dos — la
#: suite lo ejecuta. Cuatro líneas más, y la cuenta cierra: tres artefactos por
#: cuatro líneas sobre las 69 de HEAD.
#: Subida del 2026-11-25 a 85 líneas y 2 702 bytes: un cuarto artefacto,
#: `tests/test_negocio.py`, paga la misma regla —cuatro líneas, no tres—. Se
#: sube midiendo el emitido, no contando a mano.
COPTA_LINEAS = 85
COPTA_BYTES = 2702
#: Cota del acto de censo. Es más ancha que la de la suite porque lleva 12
#: referencias vivas en vez de 10; se declara aparte para que una cota no mida
#: el acto que la escribió (§medición con unidad: cada acto, su número).
COPTA_CENSO_LINEAS = 80
COPTA_CENSO_BYTES = 2600

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
        # La cota se mide sobre el artefacto que el acto emitió, no sobre la
        # reconstrucción: la reconstrucción puede separarse del acto y entonces
        # la cota vigila una página que nadie publica.
        ruta_pagina = _os.path.join(_RAIZ, "examples", "predicado-suite.json")
        with open(ruta_pagina, "r", encoding="utf-8") as flujo:
            texto = flujo.read()
        lineas = len(texto.splitlines())
        bytes_ = len(texto.encode("utf-8"))
        _medicion("P-08 página emitida", (lineas, bytes_))
        self.assertLessEqual(lineas, COPTA_LINEAS)
        self.assertLessEqual(bytes_, COPTA_BYTES)

        predicado = self._predicado_real()
        pagina = predicado.pagina()
        _medicion("P-08 referencias", (len(predicado.entradas), len(predicado.codigo)))
        _medicion("P-08 digest de la página", predicado.digest().digest[:16])
        self.assertEqual(_json.loads(pagina), predicado.cuerpo())

        # La reconstrucción describe el mismo acto: si su forma diverge del
        # artefacto, o sobra una entrada en la página o falta en la prueba.
        cuerpo = _json.loads(texto)
        self.assertEqual(len(predicado.entradas), len(cuerpo["entradas"]))
        self.assertEqual(len(predicado.codigo), len(cuerpo["codigo"]))
        self.assertEqual(
            [e.ruta.texto for e in predicado.entradas],
            [e["ruta"] for e in cuerpo["entradas"]],
        )
        self.assertEqual(
            [c.ruta.texto for c in predicado.codigo], [c["ruta"] for c in cuerpo["codigo"]]
        )

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

    def test_p19_la_especificacion_cierra_las_cuatro_ambiguedades(self) -> None:
        """Lector de las decisiones que un tercero podía tomar al revés (§2).

        Medido el 2026-11-24 con un verificador escrito leyendo SÓLO
        `PREDICADO.md`: reprodujo el digest al bit y, aun así, encontró cuatro
        puntos donde otra decisión razonable daba otro digest **sin violar la
        especificación** —salto final, orden de listas, orden de claves
        anidadas y `h_prev` ausente frente a nulo—, más uno de alcance: la
        regla de `..` enunciada sobre «ningún campo» en vez de sobre las rutas.
        Los cinco se escribieron en §2. Esta prueba es su lector: si alguien los
        borra, la ambigüedad vuelve y no se sabe hasta que un cliente diverge.
        """

        with open(_os.path.join(_RAIZ, "PREDICADO.md"), "r", encoding="utf-8") as flujo:
            texto = " ".join(flujo.read().split())

        decisiones = (
            "en toda profundidad",      # claves anidadas (§2.2)
            "termina en `}`",           # sin salto final (§2.8)
            "conservan su orden",       # listas: el orden entra al digest (§2.7)
            "está siempre presente",    # `h_prev` nulable, no omitible (§2.6)
            "la regla es de las rutas", # `..`/absoluta/NUL sólo en rutas (§2 cierre)
        )
        faltan = [fragmento for fragmento in decisiones if fragmento not in texto]
        _medicion("P-19 decisiones declaradas", (len(decisiones) - len(faltan), len(decisiones)))
        self.assertEqual(faltan, [], "la especificación perdió decisiones que cambian el digest")

    def test_p20_la_implementacion_obedece_esas_decisiones(self) -> None:
        """Las cinco decisiones de P-19, medidas sobre el objeto, no sobre el texto."""

        canon = canonizar({"b": {"z": 1, "a": 2}})
        _medicion("P-20 canon anidado", canon)
        self.assertEqual(canon, b'{"b":{"a":2,"z":1}}')  # §2.2, recursivo
        self.assertFalse(canon.endswith(b"\n"))  # §2.8, sin salto final
        self.assertNotEqual(  # §2.7, el orden de la lista entra al digest
            canonizar({"l": [1, 2]}), canonizar({"l": [2, 1]})
        )

        cuerpo = self._predicado_real().cuerpo()
        self.assertIn("h_prev", cuerpo)  # §2.6, la clave está aunque sea nula
        self.assertIsNone(cuerpo["h_prev"])

        with self.assertRaises(ContratoViolado):  # §3, hex en minúscula
            Hash(ALGORITMO, "A" * 64)

        with self.assertRaises(ContratoViolado):  # §2.7, desordenada se rechaza
            Predicado(
                afirmacion="una lista desordenada no se canoniza",
                entradas=(_entrada("b/dos.txt", H_A), _entrada("a/uno.txt", H_B)),
                codigo=(),
                entorno=Entorno("darwin", "CPython 3.9.6", ()),
                salida=_entrada("a/salida.txt", H_C),
                veredicto=VeredictoReclamado.CONFORME,
            )

    def test_p21_la_pagina_del_censo_cabe_y_su_veredicto_es_su_propia_resta(
        self,
    ) -> None:
        # El acto de censo (`examples/emitir_censo.py`) emite una SEGUNDA página
        # con la misma forma: `declarado · observado · discrepancia`. Su cota es
        # otra porque tiene más referencias vivas (12 frente a 10); heredarla del
        # acto de la suite mediría el acto que escribió la primera cota, no éste.
        ruta_pagina = _os.path.join(_RAIZ, "examples", "predicado-censo.json")
        ruta_salida = _os.path.join(_RAIZ, "examples", "censo-vigente.txt")
        with open(ruta_pagina, "r", encoding="utf-8") as flujo:
            texto = flujo.read()
        cuerpo = _json.loads(texto)
        lineas = len(texto.splitlines())
        bytes_ = len(texto.encode("utf-8"))
        _medicion("P-21 página del censo", (lineas, bytes_))
        _medicion(
            "P-21 referencias del censo", (len(cuerpo["entradas"]), len(cuerpo["codigo"]))
        )
        self.assertLessEqual(lineas, COPTA_CENSO_LINEAS)
        self.assertLessEqual(bytes_, COPTA_CENSO_BYTES)

        with open(ruta_salida, "rb") as flujo:
            salida = flujo.read()
        campos = dict(
            linea.split("=", 1) for linea in salida.decode("utf-8").splitlines() if "=" in linea
        )

        # 1. La salida que la página declara es la que está en disco. Si no, la
        #    página describe un archivo que ya no existe.
        self.assertEqual(cuerpo["salida"]["sha256"], _hashlib.sha256(salida).hexdigest())

        # 2. El veredicto de la página ES la resta que su salida publica, hecha
        #    aquí por otro camino. Una página rancia con veredicto fresco muere
        #    en esta línea; y `NO_MEDIDO` no se lee como cero.
        if campos["declarado"] == "NO_MEDIDO":
            esperado = VeredictoReclamado.NO_MEDIDO.value
        else:
            diferencia = int(campos["observado"]) - int(campos["declarado"])
            self.assertEqual(diferencia, int(campos["discrepancia"]))
            esperado = (
                VeredictoReclamado.CONFORME.value
                if diferencia == 0
                else VeredictoReclamado.NO_CONFORME.value
            )
        self.assertEqual(cuerpo["veredicto"], esperado)
        _medicion("P-21 veredicto y su resta", (cuerpo["veredicto"], esperado))


class TestVerificacionDesdeLaPagina(_unittest.TestCase):
    """P-22 · P-23 · P-24 — quien verifica tiene un archivo, no un emisor.

    La `Contrafirma` sólo es el objeto vendible si un tercero puede levantar el
    predicado desde la página publicada y recalcular su nombre. Sin la inversa,
    la contrafirma cubre un digest que sólo su autor sabe reproducir, y eso es
    una promesa con formato, no una prueba.
    """

    PAGINAS = (
        "examples/predicado-suite.json",
        "examples/predicado-censo.json",
        "examples/predicado-sello.json",
    )

    def _texto(self, relativa: str) -> str:
        with open(_os.path.join(_RAIZ, relativa), "r", encoding="utf-8") as flujo:
            return flujo.read()

    def test_p22_la_inversa_reproduce_la_pagina_publicada(self) -> None:
        for relativa in self.PAGINAS:
            texto = self._texto(relativa)
            predicado = desde_cuerpo(texto)
            _medicion("P-22 digest desde el archivo", (relativa, predicado.digest().digest[:16]))
            # 1. La página en disco se recompone byte a byte desde el objeto.
            self.assertEqual(predicado.pagina(), texto.rstrip("\n"))
            # 2. Y el texto JSON produce el mismo objeto que el diccionario: la
            #    ruta de lectura no cambia el acto.
            self.assertEqual(desde_cuerpo(_json.loads(texto)).digest(), predicado.digest())

    def test_p23_la_pagina_no_admite_ni_una_llave_menos_ni_una_de_mas(self) -> None:
        texto = self._texto("examples/predicado-censo.json")
        cuerpo = _json.loads(texto)
        sin_h_prev = {clave: valor for clave, valor in cuerpo.items() if clave != "h_prev"}
        with self.assertRaises(ContratoViolado):
            desde_cuerpo(sin_h_prev)
        con_extra = dict(cuerpo, nota="campo que el formato viejo ignoraria")
        with self.assertRaises(ContratoViolado):
            desde_cuerpo(con_extra)
        sin_entorno_lagunas = _json.loads(texto)
        sin_entorno_lagunas["entorno"] = {
            "plataforma": sin_entorno_lagunas["entorno"]["plataforma"],
            "runtime": sin_entorno_lagunas["entorno"]["runtime"],
        }
        with self.assertRaises(ContratoViolado):
            desde_cuerpo(sin_entorno_lagunas)
        _medicion("P-23 rechazos de la inversa", ("h_prev ausente", "llave de mas", "no_medido ausente"))

    def test_p24_la_contrafirma_cubre_el_acto_y_refuta_el_manipulado(self) -> None:
        texto = self._texto("examples/predicado-censo.json")
        predicado = desde_cuerpo(texto)
        contrafirma = contrafirmar(
            predicado, "test_p24", VeredictoAdjudicado.CONFIRMA, "ancla-de-prueba"
        )
        self.assertTrue(verificar_contrafirma(predicado, contrafirma))

        cuerpo = _json.loads(texto)
        otro = "no_conforme" if cuerpo["veredicto"] == "conforme" else "conforme"
        manipulado = desde_cuerpo(dict(cuerpo, veredicto=otro))
        resultado = verificar_contrafirma(manipulado, contrafirma)
        self.assertIsInstance(resultado, Divergencia)
        self.assertEqual(resultado.campo, "digest_del_predicado")
        _medicion(
            "P-24 una letra mueve el nombre del acto",
            (cuerpo["veredicto"], otro, resultado.medido[:16]),
        )


if __name__ == "__main__":
    _unittest.main()
